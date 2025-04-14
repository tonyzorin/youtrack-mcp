#!/bin/bash

# Build the Docker image
echo "Building YouTrack MCP server Docker image..."
docker build -t youtrack-mcp .

# Check if .env file exists
if [ -f .env ]; then
    echo "Using environment variables from .env file"
    docker run -i --rm --env-file .env youtrack-mcp
else
    # Prompt for YouTrack credentials
    read -p "Enter YouTrack URL: " YOUTRACK_URL
    read -sp "Enter YouTrack API token: " YOUTRACK_API_TOKEN
    echo ""
    
    echo "Starting YouTrack MCP server Docker container..."
    docker run -i --rm \
        -e YOUTRACK_URL="$YOUTRACK_URL" \
        -e YOUTRACK_API_TOKEN="$YOUTRACK_API_TOKEN" \
        youtrack-mcp
fi 