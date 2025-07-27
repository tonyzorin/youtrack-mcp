#!/bin/bash
# YouTrack MCP Docker Pull and Run Script
# This ensures we always have the latest image before running

IMAGE="tonyzorin/youtrack-mcp:1.16.2_wip"

echo "Pulling latest YouTrack MCP image..." >&2
docker pull "$IMAGE" >&2

echo "Starting YouTrack MCP server..." >&2
exec docker run -i --rm \
  -e "YOUTRACK_API_TOKEN=${YOUTRACK_API_TOKEN}" \
  -e "YOUTRACK_URL=${YOUTRACK_URL}" \
  -e "YOUTRACK_CLOUD=${YOUTRACK_CLOUD}" \
  "$IMAGE" 