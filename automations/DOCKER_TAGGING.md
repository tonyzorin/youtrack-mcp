# 🏷️ **Docker Tagging Strategy**

## **Current Tagging System**

Our Docker images use a simple, clear tagging strategy based on the trigger event.

### **📊 Tag Reference**

| Trigger | Tags Created | Purpose | Example |
|---------|--------------|---------|---------|
| **Push to `main`** | `<version>_wip`, `<commit-sha>` | Work-in-progress builds for testing | `1.11.1_wip`, `a1b2c3d4` |
| **GitHub Release** | `<version>`, `latest`, `<commit-sha>` | Production releases | `1.11.1`, `latest`, `a1b2c3d4` |
| **Pull Request** | Tests only, no build | PR validation only | No images created |

### **🎯 Usage Examples**


**For Testing (WIP builds):**
```bash
# Use latest development build
docker pull tonyzorin/youtrack-mcp:1.11.1_wip

# Use specific commit 
docker pull tonyzorin/youtrack-mcp:a1b2c3d4
```

**For Production (Releases):**
```bash
# Use latest stable release
docker pull tonyzorin/youtrack-mcp:latest

# Use specific version
docker pull tonyzorin/youtrack-mcp:1.11.1
```

## **🔄 Automated Process**

### **Main Branch Push (Development)**
When code is pushed to `main`:
1. ✅ Tests run automatically  
2. 🔨 Docker builds for multiple platforms (AMD64 + ARM64)
3. 🏷️ Tagged as `<version>_wip` and `<commit-sha>`
4. 📦 Pushed to Docker Hub
5. 💬 Available for testing immediately

### **GitHub Release (Production)**
When a GitHub release is created:
1. ✅ Tests run automatically
2. 🔨 Docker builds for multiple platforms (AMD64 + ARM64)  
3. 🏷️ Tagged as `<version>`, `latest`, and `<commit-sha>`
4. 📦 Pushed to Docker Hub
5. 🚀 Production-ready release available

### **Pull Request (Validation)**
When a PR is opened:
1. ✅ Tests run automatically
2. ❌ No Docker build (testing only)
3. 📝 Results visible in PR checks

## **🏗️ Multi-Platform Support**

All images are built for both:
- **AMD64** (Intel/standard servers)
- **ARM64** (Apple Silicon/M1/M2 Macs, ARM servers)

## **📋 Best Practices**

### **For Development & Testing:**
- Use `_wip` tags for latest development features
- Test with WIP builds before release
- Reference specific commit hashes for reproducible builds

### **For Production:**
- Use `latest` for newest stable release
- Use specific version tags for pinned deployments
- Always test WIP builds before promoting to release

### **Version Bumping:**
```bash
# Bump version using helper script
python scripts/version_bump.py minor  # 1.11.1 → 1.12.0
python scripts/version_bump.py patch  # 1.11.1 → 1.11.2
python scripts/version_bump.py major  # 1.11.1 → 2.0.0
```

## **🔍 Verification**

Check available tags on Docker Hub:
- 🐳 [DockerHub Repository](https://hub.docker.com/r/tonyzorin/youtrack-mcp/tags)
- 📦 [GitHub Packages](https://github.com/tonyzorin/youtrack-mcp/pkgs/container/youtrack-mcp) 