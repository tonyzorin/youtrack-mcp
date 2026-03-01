FROM python:3.13-alpine

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt && \
    python -c "import mcp; print(dir(mcp))"

# Copy the rest of the application
COPY . .

# Default environment variables (will be overridden at runtime)
ENV MCP_SERVER_NAME="youtrack-mcp"
ENV MCP_SERVER_DESCRIPTION="YouTrack MCP Server"
ENV MCP_DEBUG="false"
ENV YOUTRACK_VERIFY_SSL="true"

# Transport mode: stdio (default, for Claude/Cursor integration), sse (for SSE server), http (for REST API)
ENV TRANSPORT="stdio"
# Port for SSE and HTTP transport modes
ENV PORT="8000"

# Run the MCP server with configurable transport
CMD ["sh", "-c", "python main.py --transport  --port "]