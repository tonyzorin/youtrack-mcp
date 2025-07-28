# Commit & Deployment Workflow

## 🚨 Safety First: New Workflow Structure

The CI/CD pipeline now has built-in safety measures to prevent accidental production deployments.

### Workflow Options

| Build Type | Purpose | Auto-Deploy | Confirmation Required |
|------------|---------|-------------|----------------------|
| `test_only` | **DEFAULT** - Run tests only | ❌ None | ❌ No |
| `dev_build` | Build WIP images for testing | ✅ WIP tags | ❌ No |
| `production_release` | Build production images | ✅ Production tags | ⚠️ **YES** |

## Development Workflow

### 1. Local Development & Testing
```bash
# Make changes to code
git add .
git commit -m "Your changes"

# Test locally first
python -m pytest tests/unit/ -x
docker build -t youtrack-mcp-local .

# Push changes
git push origin main
```
**Result**: Automatic WIP build triggered → `tonyzorin/youtrack-mcp:X.X.X-wip`

### 2. Development Testing
```bash
# Test only (safe, no deployments)
gh workflow run ci.yml
# OR explicitly:
gh workflow run ci.yml --field build_type=test_only
```
**Result**: Tests run, no Docker images built

### 3. WIP/Development Builds
```bash
# Build WIP images for testing
gh workflow run ci.yml --field build_type=dev_build
```
**Result**: 
- `tonyzorin/youtrack-mcp:X.X.X-wip`
- `tonyzorin/youtrack-mcp:<commit-sha>`

## Production Deployment (Protected)

### 4. Production Release (Requires Confirmation)

⚠️ **IMPORTANT**: Production deployments require **explicit double confirmation**

#### Option A: Use Current Version
```bash
gh workflow run ci.yml \
  --field build_type=production_release \
  --field confirm_production=true \
  --field release_type=current
```

#### Option B: Bump Version + Release
```bash
gh workflow run ci.yml \
  --field build_type=production_release \
  --field confirm_production=true \
  --field release_type=minor \
  --field create_github_release=true
```

**Result**: 
- `tonyzorin/youtrack-mcp:X.X.X` (production)
- `tonyzorin/youtrack-mcp:latest` (production)
- NPM package published
- GitHub release created (if requested)

## Version Management

### Current Version
```bash
python3 -c "exec(open('youtrack_mcp/version.py').read()); print(__version__)"
```

### Version Bumping
```bash
# Patch version (X.X.1 → X.X.2)
python scripts/version_bump.py patch

# Minor version (X.1.X → X.2.0) 
python scripts/version_bump.py minor

# Major version (1.X.X → 2.0.0)
python scripts/version_bump.py major

# Custom version
python scripts/version_bump.py 1.2.3
```

## Docker Tagging Strategy

### Automatic Tags (Push to main)
| Trigger | Tags Created | Purpose |
|---------|--------------|---------|
| Push to `main` | `X.X.X-wip`, `<commit-sha>` | Development testing |

### Manual Tags (Workflow Dispatch)
| Build Type | Tags Created | Purpose |
|------------|--------------|---------|
| `test_only` | None | Testing only |
| `dev_build` | `X.X.X-wip`, `<commit-sha>` | Development builds |
| `production_release` | `X.X.X`, `latest`, `<commit-sha>` | Production release |

## Safety Checklist

### Before Production Release
- [ ] All tests passing locally
- [ ] Docker build successful locally  
- [ ] WIP version tested and working
- [ ] Version number appropriate
- [ ] Release notes prepared (if creating GitHub release)
- [ ] **Confirm you want to deploy to production**

### Production Release Command
```bash
# ALWAYS use these exact parameters for production:
gh workflow run ci.yml \
  --field build_type=production_release \
  --field confirm_production=true \
  --field release_type=current
```

## Emergency Procedures

### If Accidental Production Deploy
1. Check what was deployed:
   ```bash
   curl -s "https://registry.hub.docker.com/v2/repositories/tonyzorin/youtrack-mcp/tags" | jq -r '.results[0:5][] | "\(.name) - \(.last_updated)"'
   ```

2. If needed, revert by deploying previous version:
   ```bash
   gh workflow run ci.yml \
     --field build_type=production_release \
     --field confirm_production=true \
     --field release_type=custom \
     --field custom_version=PREVIOUS_VERSION
   ```

### Rollback Strategy
- Production images are immutable
- Use version bumping to deploy fixes
- Emergency: Deploy previous known-good version

## File Structure

```
youtrack-mcp/
├── youtrack_mcp/version.py     # Version source of truth
├── package.json                # NPM version (auto-synced)
├── scripts/version_bump.py     # Version management
├── .github/workflows/ci.yml    # CI/CD pipeline
└── Dockerfile                  # Container definition
```

## Troubleshooting

### Common Issues
- **"No confirmation"**: Add `--field confirm_production=true`
- **"Wrong build type"**: Use `build_type=production_release`
- **"Version conflicts"**: Check current version first
- **"Docker auth"**: Verify Docker Hub credentials in GitHub secrets

### Required GitHub Secrets
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub access token  
- `NPM_TOKEN`: NPM publish token

## Best Practices

1. **Always test locally first** before any CI/CD trigger
2. **Use WIP builds** for testing before production
3. **Explicit confirmation** required for production
4. **Version bumps** should be meaningful (follow semver)
5. **Monitor deployments** and verify functionality
6. **Document changes** in commit messages and release notes

---

**Remember**: The default workflow behavior is now **safe** - it won't deploy to production without explicit confirmation! 🛡️ 