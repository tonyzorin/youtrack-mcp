# GitHub Release Instructions for v1.0.0

## To complete the v1.0.0 release and get the 'latest' Docker tag:

### 1. Navigate to GitHub Releases
Go to: https://github.com/tonyzorin/youtrack-mcp/releases

### 2. Create New Release
- Click **"Create a new release"**
- Choose existing tag: **v1.0.0**
- Release title: **"YouTrack MCP v1.0.0 - Production Ready"**

### 3. Release Description
Copy and paste this content:

```markdown
# YouTrack MCP Server v1.0.0 🎉

Major milestone release with comprehensive attachment support and enhanced code quality.

## ✨ What's New in v1.0.0

### 📎 Attachment Support
- **Full attachment support** for YouTrack issues  
- Download and process attachments up to 750KB (1MB base64)
- Base64 encoding for Claude Desktop compatibility
- Comprehensive file size validation and error handling

### 🧪 Enhanced Testing & Quality  
- **Test coverage: 41%** (208/208 tests passing)
- **Zero linting issues** - flake8, black, mypy, isort all pass
- Professional code quality standards
- Comprehensive unit tests for all core functionality

### 🐳 Docker Improvements
- **Stable Docker images** with proper tagging strategy
- Available on Docker Hub: `tonyzorin/youtrack-mcp:1.0.0`
- Automated CI/CD pipeline with GitHub Actions
- Multi-architecture support

### 🛠️ Developer Experience
- Enhanced error handling and logging
- Improved API client with better connection management
- Comprehensive tool definitions for Claude integration
- Better parameter validation and normalization

### 🚀 Production Ready
- **Major version milestone** - stable API
- Comprehensive attachment processing
- Professional code quality
- Full CI/CD automation
- Docker Hub integration

## 📦 Installation

### Docker (Recommended)
```bash
docker run --rm \
  -e YOUTRACK_URL="https://your-instance.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  tonyzorin/youtrack-mcp:latest
```

### Claude Desktop Configuration
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "youtrack": {
      "command": "docker",
      "args": ["run", "--rm", "-i", 
               "-e", "YOUTRACK_URL=https://your-instance.youtrack.cloud",
               "-e", "YOUTRACK_API_TOKEN=your-token",
               "tonyzorin/youtrack-mcp:latest"],
      "env": {}
    }
  }
}
```

## 🔧 Available Tools

- **Issue Management**: Create, read, update issues with full metadata
- **Attachment Support**: Download and process attachments (NEW!)
- **Project Management**: List projects, custom fields, workflows
- **Advanced Search**: Flexible issue search with filters
- **User Management**: Get user information and permissions
- **Resource Discovery**: Find available resources and configurations

## 🏗️ For Developers

- **API Coverage**: Complete YouTrack REST API integration
- **Type Safety**: Full TypeScript-style type hints
- **Testing**: 41% coverage with comprehensive unit tests
- **Code Quality**: Zero linting issues, professional standards
- **Documentation**: Comprehensive tool definitions and examples

This release represents a major milestone in YouTrack MCP development!
```

### 4. Publish Release
- Ensure "Set as the latest release" is checked
- Click **"Publish release"**

### 5. Expected Results
After publishing, GitHub Actions will automatically:
- Build Docker image: `tonyzorin/youtrack-mcp:1.0.0`
- Build Docker image: `tonyzorin/youtrack-mcp:latest` 
- Build Docker image: `tonyzorin/youtrack-mcp:<commit-sha>`

### 6. Verify Docker Images
Check Docker Hub: https://hub.docker.com/r/tonyzorin/youtrack-mcp/tags
You should see the new tags appear within 5-10 minutes. 