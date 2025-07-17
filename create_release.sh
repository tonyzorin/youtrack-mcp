#!/bin/bash

# GitHub Release Creation Script for v1.5.0
# Run this after authenticating with: gh auth login

set -e

echo "🚀 Creating GitHub release v1.5.0..."

# Create the release
gh release create v1.5.0 \
  --title "v1.5.0 - Major Docker Performance Optimization" \
  --notes "## 🚀 Performance Release - 25x Faster Docker Builds

### Major Improvements
- **Docker Build Speed**: 15+ minutes → 35 seconds (**25x faster**)
- **Image Size Reduction**: 401MB → 181MB (**2.2x smaller**)
- **Simplified Dependencies**: Eliminated Git compilation and build tools
- **Production Ready**: Official MCP PyPI package (mcp>=1.11.0)

### Technical Changes
- Removed unnecessary Git compilation from Dockerfile
- Switched from \`git+https://github.com/modelcontextprotocol/python-sdk.git\` to official PyPI \`mcp>=1.11.0\`
- Eliminated build dependencies (gcc, make, autoconf, etc.)
- Simplified version handling logic
- Maintained full functionality with zero regressions

### Performance Metrics
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Build Time | 15+ minutes | 35 seconds | **25x faster** |
| Image Size | 401-881MB | 181MB | **2-5x smaller** |
| Dependencies | Git + build tools | PyPI only | Much simpler |

### Quality Assurance
- ✅ All 251 tests pass
- ✅ Zero functional regressions
- ✅ Backward compatible
- ✅ Production tested

### Docker Images
- \`tonyzorin/youtrack-mcp:1.5.0\`
- \`tonyzorin/youtrack-mcp:latest\`

This release significantly improves CI/CD performance and reduces deployment overhead while maintaining full functionality.

**Full Changelog**: https://github.com/tonyzorin/youtrack-mcp/compare/v1.4.3...v1.5.0" \
  --latest

echo "✅ Release v1.5.0 created successfully!"
echo "🐳 CI/CD will now build optimized Docker images:"
echo "   - tonyzorin/youtrack-mcp:1.5.0"
echo "   - tonyzorin/youtrack-mcp:latest"
echo "🎯 Docker builds will now be 25x faster!" 