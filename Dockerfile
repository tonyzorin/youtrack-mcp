FROM python:3.13-alpine

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import mcp; print(dir(mcp))"

# Copy the rest of the application
COPY . .

# Default environment variables (will be overridden at runtime)
ENV MCP_SERVER_NAME="youtrack-mcp"
ENV MCP_SERVER_DESCRIPTION="YouTrack MCP Server"
ENV MCP_DEBUG="false"
ENV YOUTRACK_VERIFY_SSL="true"

# Run the MCP server in stdio mode for Claude integration by default
CMD ["python", "main.py", "--transport", "stdio"]