# YouTrack MCP

A Model Context Protocol (MCP) server that provides access to YouTrack functionality.

## 🚀 Quick Reference - Common Operations

### **🎯 State Transitions (Most Common)**
```python
# ✅ PROVEN WORKING FORMAT - Use simple strings
update_issue_state("DEMO-123", "In Progress")
update_issue_state("PROJECT-456", "Fixed")
update_issue_state("TASK-789", "Closed")

# ❌ DON'T USE - Complex objects fail
# update_custom_fields(issue_id, {"State": {"name": "In Progress"}})  # FAILS
# update_custom_fields(issue_id, {"State": {"id": "154-2"}})         # FAILS
```

### **🚨 Priority Updates (Very Common)**
```python
# ✅ PROVEN WORKING FORMAT - Use simple strings
update_issue_priority("DEMO-123", "Critical")
update_issue_priority("PROJECT-456", "Major") 
update_issue_priority("TASK-789", "Normal")

# ❌ DON'T USE - Complex objects fail
# update_custom_fields(issue_id, {"Priority": {"name": "Critical"}})  # FAILS
# update_custom_fields(issue_id, {"Priority": {"id": "152-1"}})       # FAILS
```

### **👤 Assignment Updates (Common)**
```python
# ✅ PROVEN WORKING FORMAT - Use login names
update_issue_assignee("DEMO-123", "admin")
update_issue_assignee("PROJECT-456", "john.doe")
update_issue_assignee("TASK-789", "jane.smith")

# ❌ DON'T USE - Complex objects fail
# update_custom_fields(issue_id, {"Assignee": {"login": "admin"}})    # FAILS
```

### **🏷️ Type Updates (Common)**
```python
# ✅ PROVEN WORKING FORMAT - Use simple strings
update_issue_type("DEMO-123", "Bug")
update_issue_type("PROJECT-456", "Feature")
update_issue_type("TASK-789", "Task")

# ❌ DON'T USE - Complex objects fail
# update_custom_fields(issue_id, {"Type": {"name": "Bug"}})          # FAILS
```

### **⏱️ Time Estimation (Common)**
```python
# ✅ PROVEN WORKING FORMAT - Use simple time strings
update_issue_estimation("DEMO-123", "4h")     # 4 hours
update_issue_estimation("PROJECT-456", "2d")  # 2 days
update_issue_estimation("TASK-789", "30m")    # 30 minutes
update_issue_estimation("TASK-790", "1w")     # 1 week
update_issue_estimation("TASK-791", "3d 5h")  # 3 days 5 hours

# ❌ DON'T USE - ISO duration or complex formats fail
# update_custom_fields(issue_id, {"Estimation": "PT4H"})             # FAILS
```

### **⚡ Complete Issue Workflows**
```python
# 🎯 Complete Triage Workflow
update_issue_type("DEMO-123", "Bug")           # Classify as bug
update_issue_priority("DEMO-123", "Critical")  # Set priority  
update_issue_assignee("DEMO-123", "admin")     # Assign to admin
update_issue_estimation("DEMO-123", "4h")      # Estimate 4 hours
update_issue_state("DEMO-123", "In Progress")  # Start work
add_comment("DEMO-123", "Critical bug triaged and assigned")

# 🚀 Feature Development Workflow  
update_issue_type("PROJ-456", "Feature")       # Classify as feature
update_issue_priority("PROJ-456", "Normal")    # Standard priority
update_issue_assignee("PROJ-456", "jane.doe")  # Assign to developer
update_issue_estimation("PROJ-456", "2d")      # Estimate 2 days
add_comment("PROJ-456", "Feature ready for development")

# ✅ Task Completion Workflow
update_issue_state("TASK-789", "Fixed")        # Mark as fixed
add_comment("TASK-789", "Implementation completed and tested")

# 📊 Quick Updates (Most Common)
update_issue_state("DEMO-123", "In Progress")       # Start work
update_issue_priority("DEMO-123", "Critical")       # Escalate
update_issue_assignee("DEMO-123", "admin")          # Reassign
update_issue_type("DEMO-123", "Bug")                # Reclassify
update_issue_estimation("DEMO-123", "6h")           # Re-estimate
```

### **📝 Other Custom Fields**
```python
# ✅ Working formats for different field types:

# Priority (enum field)
update_custom_fields("DEMO-123", {"Priority": "Critical"})

# Assignee (user field) 
update_custom_fields("DEMO-123", {"Assignee": "admin"})

# Estimation (period field)
update_custom_fields("DEMO-123", {"Estimation": "4h"})

# Type (enum field)
update_custom_fields("DEMO-123", {"Type": "Bug"})

# Multiple fields at once
update_custom_fields("DEMO-123", {
    "Priority": "Critical",
    "Assignee": "admin", 
    "Type": "Bug"
})
```

### **🔍 Finding Issues**
```python
# Search by text
search_issues("bug in login")

# Search by project
get_project_issues("DEMO")

# Get specific issue
get_issue("DEMO-123")
```

### **📋 Creating Issues**
```python
create_issue(
    project_id="DEMO",
    summary="Bug in login system",
    description="Users cannot log in with special characters"
)
```

### **🔗 Linking Issues**
```python
# Create dependency
add_dependency("DEMO-123", "DEMO-124")

# Create relates link
add_relates_link("DEMO-123", "DEMO-125")
```

### **💬 Comments**
```python
add_comment("DEMO-123", "Fixed the login bug")
get_issue_comments("DEMO-123")
```

---

## Installation

[![Docker Build and Push](https://github.com/tonyzorin/youtrack-mcp/actions/workflows/docker-build.yml/badge.svg)](https://github.com/tonyzorin/youtrack-mcp/actions/workflows/docker-build.yml)

This project provides a Model Context Protocol (MCP) server for YouTrack, enabling seamless integration with Claude Desktop and other MCP clients.

## Quick Start

### Using Docker (Recommended)

Choose from multiple registries:

#### Docker Hub (Primary)
```bash
# Use the latest stable release
docker run --rm \
  -e YOUTRACK_URL="https://your-instance.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  tonyzorin/youtrack-mcp:latest

# Or use the latest development build
docker run --rm \
  -e YOUTRACK_URL="https://your-instance.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  tonyzorin/youtrack-mcp:1.1.2_wip
```

#### GitHub Container Registry (New)
```bash
# Use the latest stable release
docker run --rm \
  -e YOUTRACK_URL="https://your-instance.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  ghcr.io/tonyzorin/youtrack-mcp:latest

# Or use the latest development build
docker run --rm \
  -e YOUTRACK_URL="https://your-instance.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="your-token" \
  ghcr.io/tonyzorin/youtrack-mcp:1.1.2_wip
```

### Available Docker Tags

Both registries provide identical tags:

- `latest` - Latest stable release (currently 1.1.2)
- `1.1.2` - Specific version tags  
- `1.1.2_wip` - Work-in-progress builds from main branch
- `pr-<number>` - Pull request builds for testing

*Note: Images are now published to both Docker Hub and GitHub Container Registry simultaneously.*

### Using npm Package

Choose from multiple registries:

#### npmjs.org (Primary)
```bash
# Install globally
npm install -g youtrack-mcp-tonyzorin

# Or use with npx (no installation required)
npx youtrack-mcp-tonyzorin
```

#### GitHub Packages (New)
```bash
# Configure GitHub registry
npm config set @tonyzorin:registry https://npm.pkg.github.com

# Install globally
npm install -g @tonyzorin/youtrack-mcp

# Or use with npx
npx @tonyzorin/youtrack-mcp
```

## Features

- **Issue Management**: Create, read, update, and delete YouTrack issues
- **Project Management**: Access project information and custom fields
- **Search Capabilities**: Advanced search with filters and custom fields
- **User Management**: Retrieve user information and permissions
- **Attachment Support**: Download and process issue attachments (up to 10MB)
- **Multi-Platform Support**: ARM64/Apple Silicon and AMD64 architecture support
- **Comprehensive API**: Full YouTrack REST API integration

## Development

This project maintains high code quality with comprehensive testing:

- **Test Coverage**: 41% (continuously improving)
- **CI/CD Pipeline**: Automated testing and Docker builds
- **Quality Assurance**: Automated testing on every commit

For development instructions, see the [Automation Scripts Guide](automations/README.md) and [Release Process](automations/RELEASE_INSTRUCTIONS.md).

## Configuration

### Environment Variables

- `YOUTRACK_URL`: Your YouTrack instance URL
- `YOUTRACK_API_TOKEN`: Your YouTrack API token
- `YOUTRACK_VERIFY_SSL`: SSL verification (default: true)

### Example Configuration

```bash
export YOUTRACK_URL="https://prodcamp.youtrack.cloud/"
export YOUTRACK_API_TOKEN="perm-YWRtaW4=.NDMtMg==.JgbpvnDbEu7RSWwAJT6Ab3iXgQyPwu"
export YOUTRACK_VERIFY_SSL="true"
```

## Documentation

- [Development Workflow & Release Process](automations/RELEASE_INSTRUCTIONS.md)
- [Docker Tagging Strategy](automations/DOCKER_TAGGING.md)
- [Testing Guide](tests/README.md)
- [Automation Scripts](automations/README.md)

## Support

For issues and questions:
1. Check the [Issues](https://github.com/tonyzorin/youtrack-mcp/issues) page
2. Review the documentation
3. Submit a new issue with detailed information
4. Contact directly: [t.me/tonyzorin](https://t.me/tonyzorin)

---

*Latest update: Comprehensive custom fields management with 567 test coverage and clean project organization.*

## Version 1.11.1 Released

🎉 **MAJOR FEATURE** - Custom Fields Management Support
- ✅ Complete custom fields CRUD operations (create, read, update, delete)
- ✅ Field validation against project schema (all field types supported)
- ✅ Batch update capabilities for performance
- ✅ Comprehensive error handling with detailed messages
- ✅ 567 tests (+68 new tests) with extensive coverage
- ✅ Clean project organization with `automations/` directory
