# YouTrack MCP Server

[![npm version](https://badge.fury.io/js/youtrack-mcp-tonyzorin.svg)](https://www.npmjs.com/package/youtrack-mcp-tonyzorin)
[![npm downloads](https://img.shields.io/npm/dm/youtrack-mcp-tonyzorin.svg)](https://www.npmjs.com/package/youtrack-mcp-tonyzorin)

A Model Context Protocol (MCP) server for JetBrains YouTrack, enabling seamless integration with Claude Desktop and other MCP clients.

## Quick Start

Choose your preferred installation method:

### Option 1: npm/Node.js (Recommended)

**Installation:**
```bash
# Install globally
npm install -g youtrack-mcp-tonyzorin

# Or use with npx (no installation required)
npx youtrack-mcp-tonyzorin
```

**Usage:**
```bash
# Run with stdio transport (for Claude Desktop)
npx youtrack-mcp-tonyzorin

# Run with HTTP transport
npx youtrack-mcp-tonyzorin --http --port 8000

# Show help
npx youtrack-mcp-tonyzorin --help
```

### Option 2: Docker

**Using Docker Hub:**
```bash
# Use the latest stable release
docker run --rm \
  -e YOUTRACK_URL="https://your.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  tonyzorin/youtrack-mcp:latest

# Or use the latest development build
docker run --rm \
  -e YOUTRACK_URL="https://your.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  tonyzorin/youtrack-mcp:1.11.1_wip
```

**Available Docker Tags:**
- `latest` - Latest stable release
- `1.11.1` - Specific version tags  
- `1.11.1_wip` - Work-in-progress builds from main branch
- `pr-<number>` - Pull request builds for testing

## Configuration

### Environment Variables

Set these environment variables for both npm and Docker options:

```bash
export YOUTRACK_URL="https://your.youtrack.cloud"
export YOUTRACK_API_TOKEN="your-token"
export YOUTRACK_VERIFY_SSL="true"  # Optional, default: true
```

### Claude Desktop Integration

Choose your preferred method:

#### Using npm/Node.js:
```json
{
  "mcpServers": {
    "youtrack": {
      "command": "npx",
      "args": ["youtrack-mcp-tonyzorin"],
      "env": {
        "YOUTRACK_URL": "https://your.youtrack.cloud",
        "YOUTRACK_API_TOKEN": "your-token"
      }
    }
  }
}
```

#### Using Docker Hub:
```json
{
  "mcpServers": {
    "youtrack": {
      "command": "docker",
      "args": [
        "run", "--rm",
        "-e", "YOUTRACK_URL=https://your.youtrack.cloud",
        "-e", "YOUTRACK_API_TOKEN=your-token",
        "tonyzorin/youtrack-mcp:latest"
      ]
    }
  }
}
```

#### Using GitHub Container Registry:
```json
{
  "mcpServers": {
    "youtrack": {
      "command": "docker",
      "args": [
        "run", "--rm",
        "-e", "YOUTRACK_URL=https://your.youtrack.cloud",
        "-e", "YOUTRACK_API_TOKEN=your-token",
        "ghcr.io/tonyzorin/youtrack-mcp:latest"
      ]
    }
  }
}
```

#### Using GitHub Packages npm:
```json
{
  "mcpServers": {
    "youtrack": {
      "command": "npx",
      "args": ["@tonyzorin/youtrack-mcp"],
      "env": {
        "YOUTRACK_URL": "https://your.youtrack.cloud",
        "YOUTRACK_API_TOKEN": "your-token"
      }
    }
  }
}
```

## Features

- **Issue Management**: Create, read, update, and delete YouTrack issues
- **Project Management**: Access project information and custom fields
- **Search Capabilities**: Advanced search with filters and custom fields
- **User Management**: Retrieve user information and permissions
- **Attachment Support**: Download and process issue attachments (up to 10MB)
- **Multi-Platform Support**: ARM64/Apple Silicon and AMD64 architecture support

## Requirements

### For npm/Node.js option:
- **Node.js**: 18.0.0 or higher
- **Python**: 3.8 or higher (automatically detected)
- **YouTrack**: Cloud or Server instance with API access

### For Docker option:
- **Docker**: Latest version
- **YouTrack**: Cloud or Server instance with API access

*Note: Docker option includes all dependencies pre-installed*

## API Commands

Once configured, you can use these commands in Claude:

- Create, update, and manage YouTrack issues
- Search issues with advanced filters
- Access project information and custom fields
- Download and analyze issue attachments
- Manage user permissions and assignments

## CLI Options

```
Usage:
  npx youtrack-mcp-tonyzorin [options] [-- server-args]

Options:
  --help, -h           Show help message
  --version, -v        Show version information
  --info               Show server information
  --stdio              Use stdio transport (default)
  --http               Use HTTP transport
  --host <host>        Host to bind HTTP server (default: 0.0.0.0)
  --port <port>        Port for HTTP server (default: 8000)

Environment Variables:
  YOUTRACK_URL          Your YouTrack instance URL (required)
  YOUTRACK_API_TOKEN    Your YouTrack API token (required)
  YOUTRACK_VERIFY_SSL   Verify SSL certificates (default: true)
```

## Examples

### Basic Usage

#### npm/Node.js:
```bash
# Set environment variables
export YOUTRACK_URL="https://prodcamp.youtrack.cloud"
export YOUTRACK_API_TOKEN="your-token"

# Run the server
npx youtrack-mcp-tonyzorin
```

#### Docker Hub:
```bash
# Run with environment variables
docker run --rm \
  -e YOUTRACK_URL="https://prodcamp.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  tonyzorin/youtrack-mcp:latest
```

#### GitHub Container Registry:
```bash
# Run with environment variables
docker run --rm \
  -e YOUTRACK_URL="https://prodcamp.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  ghcr.io/tonyzorin/youtrack-mcp:latest
```

#### GitHub Packages npm:
```bash
# Set up GitHub registry (one-time setup)
npm config set @tonyzorin:registry https://npm.pkg.github.com

# Run with npx
npx @tonyzorin/youtrack-mcp
```

### HTTP Mode

#### npm/Node.js:
```bash
# Start HTTP server on port 8000
npx youtrack-mcp-tonyzorin --http --port 8000

# Test the server
curl http://localhost:8000/api/tools
```

#### Docker Hub:
```bash
# Start HTTP server with port mapping
docker run --rm -p 8000:8000 \
  -e YOUTRACK_URL="https://prodcamp.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  tonyzorin/youtrack-mcp:latest --transport http --host 0.0.0.0

# Test the server
curl http://localhost:8000/api/tools
```

#### GitHub Container Registry:
```bash
# Start HTTP server with port mapping
docker run --rm -p 8000:8000 \
  -e YOUTRACK_URL="https://prodcamp.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  ghcr.io/tonyzorin/youtrack-mcp:latest --transport http --host 0.0.0.0

# Test the server
curl http://localhost:8000/api/tools
```

#### GitHub Packages npm:
```bash
# Start HTTP server
npx @tonyzorin/youtrack-mcp --http --port 8000

# Test the server
curl http://localhost:8000/api/tools
```

### Development Mode

#### npm/Node.js:
```bash
# Run with debug logging
npx youtrack-mcp-tonyzorin -- --log-level DEBUG
```

#### Docker Hub:
```bash
# Run with debug logging
docker run --rm \
  -e YOUTRACK_URL="https://prodcamp.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  tonyzorin/youtrack-mcp:latest --log-level DEBUG
```

#### GitHub Container Registry:
```bash
# Run with debug logging
docker run --rm \
  -e YOUTRACK_URL="https://prodcamp.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  ghcr.io/tonyzorin/youtrack-mcp:latest --log-level DEBUG
```

#### GitHub Packages npm:
```bash
# Run with debug logging
npx @tonyzorin/youtrack-mcp -- --log-level DEBUG
```

## Troubleshooting

### npm/Node.js Issues

#### Python Not Found
If you get a "Python not found" error:

```bash
# Install Python 3.8+
# macOS with Homebrew:
brew install python

# Ubuntu/Debian:
sudo apt-get install python3

# Windows: Download from python.org
```

#### Permission Errors
```bash
# Check your YouTrack API token
npx youtrack-mcp-tonyzorin --info

# Verify your environment variables
echo $YOUTRACK_URL
echo $YOUTRACK_API_TOKEN
```

### Docker Issues

#### Container Won't Start
```bash
# Check Docker is running
docker --version

# Check container logs
docker run --rm \
  -e YOUTRACK_URL="https://your.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  tonyzorin/youtrack-mcp:latest --version
```

#### Port Already in Use
```bash
# Use a different port
docker run --rm -p 8001:8000 \
  -e YOUTRACK_URL="https://your.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  tonyzorin/youtrack-mcp:latest --transport http
```

#### GitHub Container Registry Authentication
```bash
# If you get pull errors from ghcr.io, you might need to authenticate
docker login ghcr.io

# Then try pulling again
docker pull ghcr.io/tonyzorin/youtrack-mcp:latest
```

### GitHub Packages Issues

#### npm Registry Configuration
```bash
# If @tonyzorin/youtrack-mcp is not found, configure the registry
npm config set @tonyzorin:registry https://npm.pkg.github.com

# You might need authentication for GitHub Packages npm
npm login --registry=https://npm.pkg.github.com
```

#### Package Not Found
If GitHub Packages npm shows "package not found":
- The package is published only on releases
- Check if a release has been created
- Fallback to npmjs.org version: `npm install -g youtrack-mcp-tonyzorin`

### Common Issues (Both Options)

#### Connection Issues
If you can't connect to YouTrack:

- Verify your YouTrack URL is correct
- Check that your API token has proper permissions
- Ensure your network allows connections to YouTrack
- Try testing the API token manually:
  ```bash
  curl -H "Authorization: Bearer your-token" \
       "https://your.youtrack.cloud/api/admin/projects"
  ```

## Which Option Should I Choose?

### Choose **npm/Node.js** if you:
- ✅ Already have Node.js installed
- ✅ Want faster startup times
- ✅ Prefer lighter resource usage
- ✅ Need to modify or debug the server

**Registry Options:**
- **npmjs.org** (recommended): `youtrack-mcp-tonyzorin` - Better discovery, wider usage
- **GitHub Packages**: `@tonyzorin/youtrack-mcp` - Integrated with GitHub, requires registry config

### Choose **Docker** if you:
- ✅ Want isolated, consistent environments
- ✅ Don't want to install Node.js/Python
- ✅ Are running in containerized infrastructure
- ✅ Want guaranteed dependency compatibility

**Registry Options:**
- **Docker Hub** (recommended): `tonyzorin/youtrack-mcp` - Faster, no auth required
- **GitHub Container Registry**: `ghcr.io/tonyzorin/youtrack-mcp` - Integrated with GitHub, may require auth

## Support

- **GitHub**: [Issues and bug reports](https://github.com/tonyzorin/youtrack-mcp/issues)
- **Documentation**: [Full documentation](https://github.com/tonyzorin/youtrack-mcp)

### Package Registries
- **Docker Hub**: [tonyzorin/youtrack-mcp](https://hub.docker.com/r/tonyzorin/youtrack-mcp)
- **GitHub Container Registry**: [ghcr.io/tonyzorin/youtrack-mcp](https://github.com/tonyzorin/youtrack-mcp/pkgs/container/youtrack-mcp)
- **npmjs.org**: [youtrack-mcp-tonyzorin](https://www.npmjs.com/package/youtrack-mcp-tonyzorin)
- **GitHub Packages npm**: [@tonyzorin/youtrack-mcp](https://github.com/tonyzorin/youtrack-mcp/pkgs/npm/%40tonyzorin%2Fyoutrack-mcp)

### Contact
- **Telegram**: [t.me/tonyzorin](https://t.me/tonyzorin)

## License

MIT © Tony Zorin 