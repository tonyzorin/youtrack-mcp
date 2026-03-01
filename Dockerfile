FROM python:3.14-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default environment variables (override at runtime)
ENV MCP_SERVER_NAME="youtrack-mcp"
ENV MCP_SERVER_DESCRIPTION="YouTrack MCP Server"
ENV MCP_DEBUG="false"
ENV YOUTRACK_VERIFY_SSL="true"
ENV YOUTRACK_URL=""
ENV YOUTRACK_API_TOKEN=""

# Transport mode: stdio (default, for Claude/Cursor) or sse (for SSE server)
ENV TRANSPORT="stdio"
# Port for SSE transport mode
ENV PORT="8000"

ENTRYPOINT ["python", "main.py"]
