# AWS RDS MySQL MCP Integration

A Model Context Protocol (MCP) implementation for MySQL database operations with dual server configurations - one integrated with AWS Bedrock and Streamlit UI as MCP client, and another standalone server for general MCP clients like Claude Desktop.

## Features

- **Dual MCP Server Implementation**
  - Integrated Streamlit UI app with AWS Bedrock agent which also act as MCP Client
  - Standalone FastMCP server (fastmcp_server.py) for Claude Desktop and other MCP clients
- **Secure MySQL Operations** with built-in safety checks
- **Natural Language SQL** via AWS Bedrock integration
- **Real-time Database Interaction** through web interface

## Project Structure

```
MCP/
├── app.py                 # Streamlit frontend with Bedrock integration
├── mcp_server.py         # MCP server for Bedrock integration
├── fastmcp_server.py     # Standalone MCP server
├── config.py             # Configuration loader
├── .env.example          # Environment variables template
├── .env                  # Your environment variables (create from .env.example)
└── README.md             # This file
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv-mcp

# Activate virtual environment
# Windows:
venv-mcp\Scripts\activate
# macOS/Linux:
source venv-mcp/bin/activate
```

### 2. Install Dependencies

```bash
pip install fastmcp pymysql streamlit boto3 python-dotenv
```

### 3. Environment Configuration

#### Note: Make sure you have AWS IAM credential profile configured on the machine from where you running app and/or MCP server.

Copy the example environment file and configure your settings:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual values
```

.env will have below config. Update it with the actual values:

```bash
# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# MySQL Database Configuration
RDS_HOST=your-mysql-host.amazonaws.com
RDS_PORT=3306
RDS_USER=your-username
RDS_PASS=your-password
RDS_DB=your-database-name
```

**Security Note**: 
- Never commit `.env` files to version control
- Add `.env` to your `.gitignore` file
- Use AWS IAM roles in production environments

## Usage

### Option 1: Streamlit App with Bedrock Integration

Run the integrated Streamlit application:

```bash
streamlit run app.py
```

- Access the web interface at `http://localhost:8501`
- Enter natural language commands (e.g., "Create a users table with id and name columns")
- The app uses AWS Bedrock to interpret commands and execute SQL

### Option 2: Standalone MCP Server

For use with Claude Desktop or other MCP clients:

```bash
python fastmcp_server.py
```

#### Claude Desktop Configuration

Add to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "mysql-server": {
      "command": "python",
      "args": ["path/to/your/fastmcp_server.py"],
      "cwd": "path/to/your/MCP/directory"
    }
  }
}
```

## Configuration Details

### Database Settings

Configure your MySQL connection in the `.env` file:

- **RDS_HOST**: Your MySQL server hostname
- **RDS_PORT**: MySQL port (default: 3306)
- **RDS_USER**: Database username
- **RDS_PASS**: Database password
- **RDS_DB**: Database name

### AWS Bedrock Settings

- **AWS_REGION**: AWS region for Bedrock service
- **MODEL_ID**: Bedrock model identifier

## Security Features

- **SQL Injection Protection**: Input validation and parameterized queries
- **Dangerous Operation Blocking**: Prevents DROP DATABASE, TRUNCATE operations
- **Connection Timeout**: 10-second connection timeout
- **Transaction Rollback**: Automatic rollback on errors

## Supported SQL Operations

- `SELECT` - Query data
- `INSERT` - Add new records
- `UPDATE` - Modify existing records
- `DELETE` - Remove records
- `CREATE` - Create tables/indexes
- `DROP` - Drop tables (with restrictions)
- `SHOW` - Display database information
- `DESCRIBE` - Show table structure

## Example Commands

### Natural Language (Streamlit App & Claude Desktop)
- "Show all tables in the database"
- "Create a user table with id, name, and email"
- "Insert a new user with name John and email john@example.com"
- "Find all users whose name starts with J"

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Verify MySQL server is running
   - Check firewall settings
   - Confirm connection credentials

2. **AWS Bedrock Errors**
   - Ensure AWS credentials are configured
   - Verify Bedrock model access permissions
   - Check AWS region settings

3. **MCP Client Connection**
   - Confirm server is running on stdio
   - Verify client configuration paths
   - Check Python environment activation

### Debug Mode

Enable debug logging by setting:
```bash
export PYTHONPATH=.
python -v fastmcp_server.py
```

## License

This project is provided as-is for educational and development purposes without any liability to author.

---

**Note**: This implementation requires proper AWS credentials and MySQL database access. Ensure all security best practices are followed & tested in non-production environments.
