# app.py

import os
import streamlit as st
import subprocess
import threading
import json
import uuid
import boto3
from config import AWS_REGION, MODEL_ID, TOOL_DEFS

env = os.environ.copy()
env["PYTHONPATH"] = os.getcwd()

# ========== MCP CLIENT SETUP ==========

# Start the FastMCP server subprocess (over stdio)
mcp_proc = subprocess.Popen(
    ["python", "mcp_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    env=env
)

# Stream MCP responses in the background (optional logging)
def log_stderr():
    for line in mcp_proc.stderr:
        print("[MCP stderr]", line.strip())

threading.Thread(target=log_stderr, daemon=True).start()

# Initialize MCP connection
mcp_initialized = False

def initialize_mcp():
    global mcp_initialized
    if mcp_initialized:
        return
    
    import time
    time.sleep(0.5)  # Give server time to start
    
    # Initialize MCP protocol
    req_id = str(uuid.uuid4())
    init_request = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "streamlit-client",
                "version": "1.0.0"
            }
        }
    }
    
    mcp_proc.stdin.write(json.dumps(init_request) + "\n")
    mcp_proc.stdin.flush()
    
    # Wait for initialization response
    timeout = 0
    while timeout < 100:
        timeout += 1
        line = mcp_proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        try:
            response = json.loads(line)
            if response.get("id") == req_id and "result" in response:
                # Send initialized notification
                notify_request = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                mcp_proc.stdin.write(json.dumps(notify_request) + "\n")
                mcp_proc.stdin.flush()
                mcp_initialized = True
                break
        except json.JSONDecodeError:
            continue

# MCP call function (JSON-RPC 2.0 over stdio)
def mcp_call(method, params):
    initialize_mcp()
    
    req_id = str(uuid.uuid4())
    request = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "tools/call",
        "params": {
            "name": method,
            "arguments": params
        }
    }
    mcp_proc.stdin.write(json.dumps(request) + "\n")
    mcp_proc.stdin.flush()

    timeout = 0
    while timeout < 100:
        timeout += 1
        line = mcp_proc.stdout.readline()
        if not line:
            raise RuntimeError("MCP server closed unexpectedly.")
        try:
            response = json.loads(line)
        except json.JSONDecodeError:
            continue
        if response.get("id") == req_id:
            if "error" in response:
                return {"error": response["error"]}
            result = response.get("result", {})
            
            # Handle different response formats
            if "content" in result:
                content = result["content"]
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict) and "text" in first_content:
                        return first_content["text"]
                    else:
                        return str(first_content)
                return str(content)
            else:
                return result
    
    raise RuntimeError("MCP timeout - no response received")

# ========== BEDROCK CLIENT SETUP ==========

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)

def converse_with_tools(user_prompt: str):
    import time
    import random
    from botocore.exceptions import ClientError
    
    messages = [{
        "role": "user",
        "content": [{"text": user_prompt}]
    }]

    tool_config = {"tools": TOOL_DEFS}
    max_iterations = 3  # Allow complete responses
    iteration = 0
    base_delay = 3

    def make_bedrock_call_with_retry(messages, max_retries=3):
        for attempt in range(max_retries):
            try:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                if attempt > 0:
                    time.sleep(delay)
                
                return bedrock.converse(
                    modelId=MODEL_ID,
                    messages=messages,
                    toolConfig=tool_config
                )
            except ClientError as e:
                if e.response['Error']['Code'] == 'ThrottlingException':
                    if attempt == max_retries - 1:
                        raise
                    continue
                else:
                    raise
        return None

    try:
        response = make_bedrock_call_with_retry(messages)
    except Exception as e:
        return f"Initial call failed: {str(e)}"

    while iteration < max_iterations:
        iteration += 1
        
        output = response.get('output', {})
        message = output.get('message', {})
        content = message.get('content', [])
        
        tool_use_block = None
        for block in content:
            if block.get('toolUse'):
                tool_use_block = block['toolUse']
                break
        
        if not tool_use_block:
            break
            
        tool_name = tool_use_block.get('name')
        tool_input = tool_use_block.get('input', {})
        tool_use_id = tool_use_block.get('toolUseId')
        
        try:
            tool_result = mcp_call(tool_name, tool_input)
            print(f"[DEBUG] Tool result: {tool_result}")  # Debug output
            
            # Format structured data for better readability
            if isinstance(tool_result, dict) and "rows" in tool_result and "columns" in tool_result:
                formatted_result = f"Query executed successfully.\n\nColumns: {tool_result['columns']}\n\nResults:\n"
                for row in tool_result['rows']:
                    formatted_result += f"- {', '.join(map(str, row))}\n"
                tool_result_text = formatted_result
            else:
                tool_result_text = str(tool_result)
                
        except Exception as e:
            tool_result_text = f"Tool failed: {str(e)}"
        
        messages.append({"role": "assistant", "content": content})
        messages.append({
            "role": "user",
            "content": [{
                "toolResult": {
                    "toolUseId": tool_use_id,
                    "content": [{"text": tool_result_text}]
                }
            }]
        })
        
        try:
            response = make_bedrock_call_with_retry(messages)
        except Exception as e:
            return f"Call {iteration} failed: {str(e)}"

    output = response.get('output', {})
    message = output.get('message', {})
    content = message.get('content', [])
    
    text_content = []
    for block in content:
        if block.get('text'):
            text_content.append(block['text'])
    
    return '\n'.join(text_content) if text_content else "No response"

# ========== STREAMLIT UI ==========

st.set_page_config(page_title="Bedrock + FastMCP RDS App", page_icon="🧠")
st.title("💬 Bedrock + FastMCP for RDS MySQL")
st.markdown("Enter SQL-related commands in natural language (e.g. 'Create a table users...').")

user_input = st.text_area("Your instruction:", height=200)

if st.button("Run"):
    if not user_input.strip():
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Thinking..."):
            try:
                result = converse_with_tools(user_input)
                st.success("Done!")
                st.code(result)
            except Exception as e:
                st.error(f"Error: {str(e)}")
