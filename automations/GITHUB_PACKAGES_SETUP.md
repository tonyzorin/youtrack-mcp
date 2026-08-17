# GitHub Packages Dual Publishing Setup

This document explains the enhanced CI/CD pipeline that publishes YouTrack MCP to multiple package registries for maximum accessibility.

## 🎯 Publishing Strategy Overview

Our enhanced workflow now publishes to **four registries** simultaneously:

### Docker Images
1. **Docker Hub** (Primary): `searchanise/youtrack-mcp`
2. **GitHub Container Registry** (New): `ghcr.io/searchanise/youtrack-mcp`

### npm Packages  
1. **npmjs.org** (Primary): `youtrack-mcp-searchanise`
2. **GitHub Packages** (New): `@searchanise/youtrack-mcp`

## 🔄 Automated Publishing Triggers

### Main Branch Push → WIP Docker Images
```bash
# Triggers on: git push origin main
# Publishes to:
searchanise/youtrack-mcp:1.11.1_wip
ghcr.io/searchanise/youtrack-mcp:1.11.1_wip
```

### GitHub Release → Production Release
```bash
# Triggers on: GitHub release creation
# Publishes Docker images:
searchanise/youtrack-mcp:latest
searchanise/youtrack-mcp:1.11.1
ghcr.io/searchanise/youtrack-mcp:latest
ghcr.io/searchanise/youtrack-mcp:1.11.1

# Publishes npm packages:
youtrack-mcp-searchanise@1.11.1         # npmjs.org
@searchanise/youtrack-mcp@1.11.1        # GitHub Packages
```

## 🔧 Required GitHub Secrets

The workflow requires **3 secrets** to be configured in your GitHub repository:

### 1. DOCKER_USERNAME
```
Name: DOCKER_USERNAME
Value: searchanise
Purpose: Docker Hub authentication
```

### 2. DOCKER_PASSWORD  
```
Name: DOCKER_PASSWORD
Value: [Docker Hub access token]
Create at: https://hub.docker.com/settings/security
Permissions: Read, Write, Delete
```

### 3. NPM_TOKEN
```
Name: NPM_TOKEN
Value: [npm access token] 
Create at: https://www.npmjs.com/settings/tokens
Type: Automation token (recommended)
Purpose: npmjs.org publishing
```

### 4. GITHUB_TOKEN (Automatic)
```
Name: GITHUB_TOKEN
Value: [Automatically provided by GitHub]
Purpose: GitHub Container Registry + GitHub Packages
Setup: No manual configuration required
```

## 📦 Installation Options for Users

After publishing, users can install from multiple sources:

### Docker Options
```bash
# Docker Hub (Primary)
docker pull searchanise/youtrack-mcp:latest

# GitHub Container Registry  
docker pull ghcr.io/searchanise/youtrack-mcp:latest
```

### npm Options
```bash
# npmjs.org (Primary)
npm install -g youtrack-mcp-searchanise

# GitHub Packages (requires registry config)
npm config set @searchanise:registry https://npm.pkg.github.com
npm install -g @searchanise/youtrack-mcp
```

## 🚀 Workflow Features

### Multi-Platform Docker Support
- **Architectures**: AMD64 + ARM64 (Apple Silicon support)
- **Registries**: Docker Hub + GitHub Container Registry
- **Identical content**: Both registries contain the same images

### Smart npm Publishing
- **Version Sync**: Automatically updates package.json version from Python version
- **Registry Switching**: Publishes to npmjs.org, then reconfigures for GitHub Packages
- **Release-Only**: npm packages only publish on releases, not main branch pushes

### Enhanced Security
- **GitHub Container Registry**: Uses GITHUB_TOKEN (no additional secrets)
- **Scoped Packages**: GitHub Packages uses `@searchanise/youtrack-mcp` scope
- **Token Isolation**: Each registry uses appropriate authentication method

## 📋 Claude Desktop Integration Examples

Users can choose their preferred registry in Claude Desktop configuration:

### Option 1: Docker Hub
```json
{
  "mcpServers": {
    "youtrack": {
      "command": "docker",
      "args": ["run", "--rm", "-e", "YOUTRACK_URL=...", "-e", "YOUTRACK_API_TOKEN=...", "searchanise/youtrack-mcp:latest"]
    }
  }
}
```

### Option 2: GitHub Container Registry
```json
{
  "mcpServers": {
    "youtrack": {
      "command": "docker", 
      "args": ["run", "--rm", "-e", "YOUTRACK_URL=...", "-e", "YOUTRACK_API_TOKEN=...", "ghcr.io/searchanise/youtrack-mcp:latest"]
    }
  }
}
```

### Option 3: npmjs.org
```json
{
  "mcpServers": {
    "youtrack": {
      "command": "npx",
      "args": ["youtrack-mcp-searchanise"],
      "env": {"YOUTRACK_URL": "...", "YOUTRACK_API_TOKEN": "..."}
    }
  }
}
```

### Option 4: GitHub Packages npm
```json
{
  "mcpServers": {
    "youtrack": {
      "command": "npx", 
      "args": ["@searchanise/youtrack-mcp"],
      "env": {"YOUTRACK_URL": "...", "YOUTRACK_API_TOKEN": "..."}
    }
  }
}
```

## 🔍 Registry URLs & Package Pages

### Docker Registries
- **Docker Hub**: [hub.docker.com/r/searchanise/youtrack-mcp](https://hub.docker.com/r/searchanise/youtrack-mcp)
- **GitHub Container Registry**: [github.com/searchanise/youtrack-mcp/pkgs/container/youtrack-mcp](https://github.com/searchanise/youtrack-mcp/pkgs/container/youtrack-mcp)

### npm Registries  
- **npmjs.org**: [npmjs.com/package/youtrack-mcp-searchanise](https://www.npmjs.com/package/youtrack-mcp-searchanise)
- **GitHub Packages**: [github.com/searchanise/youtrack-mcp/pkgs/npm/@searchanise/youtrack-mcp](https://github.com/searchanise/youtrack-mcp/pkgs/npm/%40searchanise%2Fyoutrack-mcp)

## 💡 Benefits of Dual Publishing

### For Users
- **Choice**: Multiple installation methods and registries
- **Reliability**: Redundancy if one registry has issues
- **Integration**: GitHub Packages integrates with repository permissions
- **Performance**: Choose fastest registry for your location/network

### For Developers
- **Visibility**: Packages appear in GitHub repository
- **Security**: GitHub Packages inherit repository access controls
- **Automation**: Single workflow manages all publishing
- **Compatibility**: Maintains existing installation methods

## 🛠️ Development Workflow

### Testing Changes
1. **Push to main** → Get WIP Docker images for testing
2. **Verify functionality** → Test with latest WIP images
3. **Create release** → Publish production images + npm packages

### Version Management
```bash
# Bump version (updates youtrack_mcp/version.py)
python scripts/version_bump.py minor

# Push changes
git push origin main
git push origin --tags

# Create GitHub release
# → Triggers full publishing to all 4 registries
```

## 🔧 Troubleshooting

### GitHub Actions Failures
1. **Check secrets**: Ensure all 3 secrets are properly configured
2. **Verify tokens**: Make sure tokens have correct permissions
3. **Check logs**: Review GitHub Actions workflow logs for specific errors

### Registry Authentication Issues
```bash
# Docker Hub login test
docker login

# GitHub Container Registry login test  
docker login ghcr.io

# npm registry test
npm whoami

# GitHub Packages npm test
npm whoami --registry=https://npm.pkg.github.com
```

### Package Not Found Errors
- **Docker**: Images publish on main pushes and releases
- **npm**: Packages only publish on releases, not main pushes
- **GitHub Packages**: May require authentication for private registries

## 🎯 Migration Benefits

This setup provides:
- ✅ **Zero breaking changes** - All existing installation methods continue to work
- ✅ **Additional options** - Users can choose their preferred registry
- ✅ **Future-proofing** - GitHub integration for enterprise environments
- ✅ **Automated publishing** - No manual intervention required
- ✅ **Comprehensive coverage** - Docker + npm across multiple registries

The enhanced publishing pipeline ensures maximum compatibility and accessibility while maintaining the simplicity of the original workflow. 