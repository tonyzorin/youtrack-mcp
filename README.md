# YouTrack MCP

[![CI](https://github.com/tonyzorin/youtrack-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/tonyzorin/youtrack-mcp/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/youtrack-mcp-tonyzorin)](https://www.npmjs.com/package/youtrack-mcp-tonyzorin)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Open-source [Model Context Protocol](https://modelcontextprotocol.io) server for [JetBrains YouTrack](https://www.jetbrains.com/youtrack/). You run it locally (Docker, npx, or Python). It talks to **YouTrack Cloud or Server** over the REST API so Cursor, Claude Desktop, and other MCP clients can search, create, and update issues.

This server shipped in **April 2025**, about six months before JetBrains added a Remote MCP to [YouTrack 2025.3](https://blog.jetbrains.com/youtrack/2025/10/youtrack-introduces-a-remote-mcp-server-and-new-apps-2/) (October 2025). It is not a fork of the official server.

## Why this still exists

JetBrains’ [official MCP](https://www.jetbrains.com/help/youtrack/cloud/model-context-protocol-server.html) is built **into YouTrack 2025.3+** (Cloud and Server) at `https://<your-instance>/mcp`. New MCP features from JetBrains (OAuth, time tracking, tags, drafts, custom YouTrack apps) live there. Use that if you are on 2025.3 or newer and want the vendor path.

This project is a **process you run**. It calls the YouTrack REST API — the same API that existed before `/mcp`. That is why it still works on **self-hosted Server that has not upgraded to 2025.3**. There is no published minimum YouTrack version; if your instance can issue a permanent token and serve `/api/issues`, this server can talk to it. Article tools need a YouTrack that has the knowledge base.

| | This MCP | Official (2025.3+) |
| --- | --- | --- |
| History | April 2025, before official existed | Shipped in YouTrack 2025.3 (Oct 2025) |
| Where it runs | Your machine (stdio / Docker) | Inside YouTrack (`/mcp`) |
| YouTrack versions | REST API (including Server before 2025.3) | 2025.3 and newer |
| Cursor / Claude Desktop | Native stdio | Remote HTTP, or `npx mcp-remote` |
| Field updates | Simple strings: `update_issue_state("DEMO-123", "In Progress")` | Fetch field schema, then `update_issue` |
| Stick with this for | Older Server, local stdio, attachments, project admin, tool allow/deny lists | New JetBrains MCP features, OAuth, n8n/Zapier `/mcp` URL |

## Quick start

You need a YouTrack URL and a [permanent API token](https://www.jetbrains.com/help/youtrack/cloud/manage-permanent-tokens.html).

### Cursor / Claude Desktop (Docker)

```json
{
  "mcpServers": {
    "youtrack": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "YOUTRACK_URL=https://your-instance.youtrack.cloud",
        "-e", "YOUTRACK_API_TOKEN=perm-xxx.your-token",
        "tonyzorin/youtrack-mcp:latest"
      ]
    }
  }
}
```

Same image on GHCR: `ghcr.io/tonyzorin/youtrack-mcp:latest`.

`-i` is required for stdio (without it the container exits immediately). Docker does **not** see Cursor/Claude `env` — pass YouTrack vars with `-e` in `args`. To limit tools, add another `-e` line, for example `ENABLED_TOOLS=get_issue,search_issues,create_issue,add_comment`.

### npx (no Docker)

```json
{
  "mcpServers": {
    "youtrack": {
      "command": "npx",
      "args": ["-y", "youtrack-mcp-tonyzorin"],
      "env": {
        "YOUTRACK_URL": "https://your-instance.youtrack.cloud",
        "YOUTRACK_API_TOKEN": "perm-xxx.your-token"
      }
    }
  }
}
```

Requires Node.js 18+ and Python 3.14+. Also published as `@tonyzorin/youtrack-mcp` on GitHub Packages.

### Docker from a terminal

```bash
docker run --rm -i \
  -e YOUTRACK_URL="https://your-instance.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="perm-xxx.your-token" \
  tonyzorin/youtrack-mcp:latest
```

Tag `latest` is the current stable release (**2.0.0**). Pin `tonyzorin/youtrack-mcp:2.0.0` if you want a frozen image. Stay on MCP SDK 1 with `tonyzorin/youtrack-mcp:1.18.0`. WIP and PR tags exist for testing; do not use them in production.

### Docker Compose (HTTP)

Compose does not attach a client to stdin, so stdio exits after startup. Use streamable HTTP and publish the port:

```yaml
services:
  youtrack-mcp:
    image: tonyzorin/youtrack-mcp:latest
    ports:
      - "8000:8000"
    environment:
      YOUTRACK_URL: https://your-instance.youtrack.cloud
      YOUTRACK_API_TOKEN: perm-xxx.your-token
      TRANSPORT: streamable-http
      ENABLED_TOOLS: get_issue,search_issues,get_projects
```

Point Cursor / Claude Code at `http://localhost:8000/mcp`.

Remote HTTP from a terminal:

```bash
docker run --rm -p 8000:8000 \
  -e YOUTRACK_URL="https://your-instance.youtrack.cloud" \
  -e YOUTRACK_API_TOKEN="perm-xxx.your-token" \
  tonyzorin/youtrack-mcp:latest \
  --transport streamable-http --host 0.0.0.0 --port 8000
```

## What you can do

Pass **simple strings** for state, priority, assignee, type, and estimation. Nested `{ "name": "In Progress" }` objects fail.

```python
search_issues("project: DEMO #Unresolved")
get_issue("DEMO-123")
create_issue(project="DEMO", summary="Login fails on special characters", custom_fields={"Assignee": "admin", "Type": "Bug"})

update_issue_state("DEMO-123", "In Progress")
update_issue_priority("DEMO-123", "Critical")
update_issue_assignee("DEMO-123", "admin")
update_issue_type("DEMO-123", "Bug")
update_issue_estimation("DEMO-123", "4h")

add_comment("DEMO-123", "Reproduced on staging")
add_dependency("DEMO-123", "DEMO-124")
```

**Issues:** search, get, create, update, comments, links (relates / depends / duplicates).

**Custom fields:** dedicated helpers above, plus `update_custom_fields`, batch updates, schema and allowed-value lookup.

**Attachments:** list via `get_issue_raw`, download as base64 (`get_attachment_content`), delete.

**Projects:** list/get, create/update, custom-field schemas, subsystems, versions, builds.

**Users:** current user, lookup, permissions.

**Articles:** get, search, create, update, comments.

**Diagnostics:** `diagnose_workflow_restrictions`, `get_help`.

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `YOUTRACK_URL` | yes | YouTrack base URL (Cloud or Server) |
| `YOUTRACK_API_TOKEN` | yes | Permanent token |
| `YOUTRACK_VERIFY_SSL` | no | SSL verification, default `true` |
| `DISABLED_TOOLS` | no | Comma-separated tools to hide (denylist) |
| `ENABLED_TOOLS` | no | Comma-separated tools to keep; hides all others (allowlist) |

Allowlist wins if both are set. Names are case-insensitive; hyphens and underscores are equivalent.

```bash
# Hide write tools
export DISABLED_TOOLS="create_issue,update_issue,delete_attachment"

# Read-only subset
export ENABLED_TOOLS="get_issue,search_issues,get_projects"
```

Self-signed Server: `YOUTRACK_VERIFY_SSL=false`.

## Development

- [Testing](tests/README.md)
- CI: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

## Support

- [GitHub Issues](https://github.com/tonyzorin/youtrack-mcp/issues)
- Telegram: [t.me/tonyzorin](https://t.me/tonyzorin)

MIT. See [LICENSE](LICENSE).
