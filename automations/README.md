# Automation Scripts

This directory contains local automation scripts for project management and development workflows.

## 🛠️ Available Scripts

### **Release Management**
- **`create_release.sh`** - Automate GitHub release creation with proper tagging
- **`build-local.sh`** - Build and test Docker images locally
- **`RELEASE_INSTRUCTIONS.md`** - Step-by-step guide for creating GitHub releases
- **`DOCKER_TAGGING.md`** - Docker tagging strategy and deployment documentation

### **GitHub Integration**
- **`test_github_access.sh`** - Test GitHub API connectivity and permissions
- **`close_pr.sh`** - Automatically close pull requests with comments
- **`comment_on_pr.sh`** - Add automated comments to pull requests

## 📋 Usage

All scripts should be run from the project root directory:

```bash
# Example: Create a new release
./automations/create_release.sh

# Example: Test GitHub access
./automations/test_github_access.sh

# Example: Build locally
./automations/build-local.sh
```

## 🔧 Prerequisites

Most scripts require:
- GitHub CLI (`gh`) installed and configured
- Docker installed (for build scripts)
- Proper environment variables set (see individual scripts)

## 📁 Related Directories

- **`scripts/`** - Development and CI/CD utility scripts
- **`.github/workflows/`** - GitHub Actions workflow definitions 