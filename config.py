# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Amazon Bedrock
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")

# RDS MySQL config
RDS_HOST = os.getenv("RDS_HOST")
RDS_PORT = int(os.getenv("RDS_PORT", "3306"))
RDS_USER = os.getenv("RDS_USER")
RDS_PASS = os.getenv("RDS_PASS")
RDS_DB = os.getenv("RDS_DB")

# Validate required environment variables
required_vars = ["RDS_HOST", "RDS_USER", "RDS_PASS", "RDS_DB"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Bedrock tool definitions
TOOL_DEFS = [
    {
        "toolSpec": {
            "name": "execute_sql",
            "description": "Execute SQL on RDS MySQL (CREATE, SELECT, etc.)",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL query to execute"
                        }
                    },
                    "required": ["sql"]
                }
            }
        }
    }
]
