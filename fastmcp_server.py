#!/usr/bin/env python3

from fastmcp import FastMCP
import pymysql
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database configuration
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

# Create the MCP server
mcp = FastMCP("RDS MySQL Server")

@mcp.tool()
def execute_sql(sql: str) -> str:
    """Execute SQL queries on RDS MySQL database"""
    if not sql or not sql.strip():
        return "Error: Empty SQL query"
    
    sql = sql.strip()
    dangerous_keywords = ['DROP DATABASE', 'DROP SCHEMA', 'TRUNCATE']
    if any(keyword in sql.upper() for keyword in dangerous_keywords):
        return "Error: Dangerous SQL operation not allowed"
    
    conn = None
    try:
        conn = pymysql.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            user=RDS_USER,
            password=RDS_PASS,
            database=RDS_DB,
            connect_timeout=10
        )
        with conn.cursor() as cur:
            cur.execute(sql)
            if sql.upper().startswith("SELECT"):
                rows = cur.fetchall()
                if cur.description:
                    cols = [d[0] for d in cur.description]
                    result = f"Columns: {cols}\nRows: {list(rows)}"
                    return result
                else:
                    return "No results"
            else:
                conn.commit()
                return f"Query executed successfully. Affected rows: {cur.rowcount}"
    except Exception as e:
        return f"Database error: {str(e)}"
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    mcp.run()