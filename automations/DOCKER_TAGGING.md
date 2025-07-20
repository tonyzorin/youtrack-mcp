# 🏷️ **Improved Docker Tagging Strategy**

## **New Clear Tagging System**

Instead of confusing tags like `0.3.7_wip` and `pr-15`, we now use semantic, environment-based tags that are much easier to understand.

### **📊 Tag Comparison**

| Trigger | **OLD Tags** (confusing) | **NEW Tags** (clear) |
|---------|---------------------------|----------------------|
| **Push to main** | `tonyzorin/youtrack-mcp:0.3.7_wip`<br/>`tonyzorin/youtrack-mcp:a1b2c3d4` | `tonyzorin/youtrack-mcp:v0.3.7-dev`<br/>`tonyzorin/youtrack-mcp:v0.3.7-dev-a1b2c3d4`<br/>`tonyzorin/youtrack-mcp:latest-dev` |
| **Pull Request #15** | `tonyzorin/youtrack-mcp:pr-15`<br/>`tonyzorin/youtrack-mcp:a1b2c3d4` | `tonyzorin/youtrack-mcp:v0.3.7-pr15`<br/>`tonyzorin/youtrack-mcp:v0.3.7-pr15-a1b2c3d4` |
| **Release v1.0.0** | `tonyzorin/youtrack-mcp:1.0.0`<br/>`tonyzorin/youtrack-mcp:latest`<br/>`tonyzorin/youtrack-mcp:a1b2c3d4` | `tonyzorin/youtrack-mcp:v1.0.0`<br/>`tonyzorin/youtrack-mcp:v1.0.0-stable`<br/>`tonyzorin/youtrack-mcp:latest`<br/>`tonyzorin/youtrack-mcp:stable` |

## **🎯 Benefits of New System**

### **1. Environment Clarity**
- **`-dev`**: Clearly indicates development/testing builds
- **`-pr15`**: Obvious this is for Pull Request #15
- **`-stable`**: Explicitly marks production-ready releases

### **2. Version Semantics**
- **`v0.3.7-dev`**: Version 0.3.7 in development
- **`v1.0.0-stable`**: Version 1.0.0 production release
- **`latest-dev`**: Always the newest development build

### **3. Better Organization**
- Development teams can easily identify build types
- Clear separation between testing and production images
- Consistent naming across all environments

## **🔄 When Tags Are Created**

### **Development Workflow**
```bash
# You push changes to main branch
git push origin main

# GitHub Actions automatically creates:
# ✅ v0.3.7-dev              (main development image)
# ✅ v0.3.7-dev-a1b2c3d4     (with specific commit)
# ✅ latest-dev              (always latest development)
```

### **Pull Request Workflow**
```bash
# Someone creates PR #23
# GitHub Actions automatically creates:
# ✅ v0.3.7-pr23             (PR testing image)
# ✅ v0.3.7-pr23-a1b2c3d4    (with specific commit)
```

### **Release Workflow**
```bash
# You create Release v1.0.0
# GitHub Actions automatically creates:
# ✅ v1.0.0                  (version release)
# ✅ v1.0.0-stable           (explicit stability)
# ✅ latest                  (latest production)
# ✅ stable                  (latest stable)
```

## **📋 Usage Examples**

### **For Development**
```bash
# Use latest development build
docker pull tonyzorin/youtrack-mcp:latest-dev

# Use specific development version
docker pull tonyzorin/youtrack-mcp:v0.3.7-dev

# Use specific commit for debugging
docker pull tonyzorin/youtrack-mcp:v0.3.7-dev-a1b2c3d4
```

### **For Testing PRs**
```bash
# Test specific Pull Request
docker pull tonyzorin/youtrack-mcp:v0.3.7-pr23

# Test with specific commit
docker pull tonyzorin/youtrack-mcp:v0.3.7-pr23-a1b2c3d4
```

### **For Production**
```bash
# Use latest stable release
docker pull tonyzorin/youtrack-mcp:latest
# or
docker pull tonyzorin/youtrack-mcp:stable

# Use specific version
docker pull tonyzorin/youtrack-mcp:v1.0.0

# Use explicitly stable version
docker pull tonyzorin/youtrack-mcp:v1.0.0-stable
```

## **🛠️ Implementation**

The new tagging system is implemented in `.github/workflows/docker-build.yml` with logic that:

1. **Detects the trigger type** (push, PR, release)
2. **Extracts version** from `youtrack_mcp/version.py`
3. **Generates appropriate tags** based on environment
4. **Provides clear logging** about what's being built

## **💡 Migration Guide**

### **If you were using:**
- `tonyzorin/youtrack-mcp:0.3.7_wip` → Use `tonyzorin/youtrack-mcp:v0.3.7-dev`
- `tonyzorin/youtrack-mcp:pr-15` → Use `tonyzorin/youtrack-mcp:v0.3.7-pr15`
- `tonyzorin/youtrack-mcp:latest` → **No change** (still latest production)

### **New recommended usage:**
- **Development**: `tonyzorin/youtrack-mcp:latest-dev`
- **Production**: `tonyzorin/youtrack-mcp:stable`
- **Specific version**: `tonyzorin/youtrack-mcp:v1.0.0-stable`

This tagging strategy follows Docker and Kubernetes best practices, making it much easier for teams to understand what each image contains and when to use it! 🚀 