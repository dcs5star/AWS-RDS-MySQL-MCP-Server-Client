# mcp_server.py

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


app = FastMCP(name="rds_mcp_server", version="1.0.0")

@app.tool()
def execute_sql(sql: str) -> dict:
    """
    Execute SQL on RDS MySQL.
    Supports CREATE, DROP, INSERT, UPDATE, DELETE, SELECT.
    Returns affected rows or result set.
    """
    if not sql or not sql.strip():
        return {"error": "Empty SQL query"}
    
    # Basic SQL validation
    sql = sql.strip()
    dangerous_keywords = ['DROP DATABASE', 'DROP SCHEMA', 'TRUNCATE', 'DELETE FROM mysql']
    if any(keyword in sql.upper() for keyword in dangerous_keywords):
        return {"error": "Dangerous SQL operation not allowed"}
    
    conn = None
    try:
        conn = pymysql.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            user=RDS_USER,
            password=RDS_PASS,
            database=RDS_DB,
            connect_timeout=10,
            autocommit=False
        )
        with conn.cursor() as cur:
            cur.execute(sql)
            if sql.upper().startswith(("SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN")):
                rows = cur.fetchall()
                if cur.description:
                    cols = [d[0] for d in cur.description]
                    return {"columns": cols, "rows": list(rows)}
                else:
                    return {"columns": [], "rows": []}
            else:
                conn.commit()
                return {"status": "OK", "affected": cur.rowcount}
    except pymysql.Error as e:
        if conn:
            conn.rollback()
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": f"Execution error: {str(e)}"}
    finally:
        if conn:
            conn.close()



if __name__ == "__main__":
    app.run()  # Starts MCP via stdio
