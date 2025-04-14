FROM python:3.10-slim

WORKDIR /app

# Install git for pip dependencies from GitHub
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import mcp; print(dir(mcp))"

# Copy the rest of the application
COPY . .

# Environment variables
ENV YOUTRACK_URL="https://prodcamp.youtrack.cloud"
ENV YOUTRACK_API_TOKEN="perm-YWRtaW4=.NDMtMQ==.Gf98SD8i4WI1B0LKxWp1xXn1So3RSL"
ENV MCP_SERVER_NAME="youtrack-mcp"
ENV MCP_SERVER_DESCRIPTION="YouTrack MCP Server"
ENV MCP_DEBUG="false"

# Run the MCP server
CMD ["python", "main.py"]