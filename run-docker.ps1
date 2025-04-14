# Build the Docker image
Write-Host "Building YouTrack MCP server Docker image..." -ForegroundColor Green
docker build -t youtrack-mcp .

# Check if .env file exists
if (Test-Path .env) {
    Write-Host "Using environment variables from .env file" -ForegroundColor Green
    docker run -i --rm --env-file .env youtrack-mcp
}
else {
    # Prompt for YouTrack credentials
    $YOUTRACK_URL = Read-Host "Enter YouTrack URL"
    $YOUTRACK_API_TOKEN = Read-Host "Enter YouTrack API token" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($YOUTRACK_API_TOKEN)
    $TOKEN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    
    Write-Host "Starting YouTrack MCP server Docker container..." -ForegroundColor Green
    docker run -i --rm `
        -e YOUTRACK_URL="$YOUTRACK_URL" `
        -e YOUTRACK_API_TOKEN="$TOKEN" `
        youtrack-mcp
} 