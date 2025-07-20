#!/usr/bin/env node

import YouTrackMCPServer from '../index.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * YouTrack MCP Server CLI
 * 
 * This CLI tool allows you to run the YouTrack MCP server from the command line
 * after installing it via npm.
 */

function showHelp() {
  console.log(`
📋 YouTrack MCP Server CLI

Usage:
  npx youtrack-mcp-tonyzorin [options] [-- server-args]
  youtrack-mcp-tonyzorin [options] [-- server-args]

Options:
  --help, -h           Show this help message
  --version, -v        Show version information
  --info               Show server information
  --stdio              Use stdio transport (default)
  --http               Use HTTP transport with --host and --port
  --host <host>        Host to bind HTTP server (default: 0.0.0.0)
  --port <port>        Port for HTTP server (default: 8000)

Environment Variables:
  YOUTRACK_URL          Your YouTrack instance URL (required)
  YOUTRACK_API_TOKEN    Your YouTrack API token (required)
  YOUTRACK_VERIFY_SSL   Verify SSL certificates (default: true)

Examples:
  # Run with stdio transport (for Claude Desktop)
  npx youtrack-mcp-tonyzorin

  # Run with HTTP transport
  npx youtrack-mcp-tonyzorin --http --port 8000

  # Pass arguments to the Python server
  npx youtrack-mcp-tonyzorin -- --log-level DEBUG

  # Set environment variables inline
  YOUTRACK_URL=https://your.youtrack.cloud YOUTRACK_API_TOKEN=your-token npx youtrack-mcp-tonyzorin

Configuration for Claude Desktop:
Add this to your Claude Desktop config:
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
`);
}

function showVersion() {
  try {
    const packageJsonPath = join(__dirname, '..', '..', 'package.json');
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf8'));
    console.log(`YouTrack MCP Server v${packageJson.version}`);
  } catch (error) {
    console.log('YouTrack MCP Server v1.11.1');
  }
}

async function main() {
  const args = process.argv.slice(2);
  
  // Handle help and version flags
  if (args.includes('--help') || args.includes('-h')) {
    showHelp();
    return;
  }
  
  if (args.includes('--version') || args.includes('-v')) {
    showVersion();
    return;
  }

  try {
    const server = new YouTrackMCPServer();
    
    if (args.includes('--info')) {
      console.log('📊 Server Information:');
      console.log(JSON.stringify(server.getInfo(), null, 2));
      return;
    }

    // Parse arguments
    const serverArgs = [];
    let useHttp = false;
    let host = '0.0.0.0';
    let port = '8000';
    
    for (let i = 0; i < args.length; i++) {
      const arg = args[i];
      
      if (arg === '--') {
        // Everything after -- goes to the Python server
        serverArgs.push(...args.slice(i + 1));
        break;
      }
      
      switch (arg) {
        case '--stdio':
          useHttp = false;
          break;
        case '--http':
          useHttp = true;
          break;
        case '--host':
          host = args[++i];
          break;
        case '--port':
          port = args[++i];
          break;
        default:
          // Pass unknown args to the Python server
          serverArgs.push(arg);
      }
    }

    // Configure transport
    if (useHttp) {
      serverArgs.push('--transport', 'http', '--host', host);
      console.log(`🌐 Starting HTTP server on http://${host}:${port}`);
    } else {
      serverArgs.push('--transport', 'stdio');
      console.log('📡 Starting stdio transport (for Claude Desktop)');
    }

    // Start the server
    await server.start(serverArgs);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

main().catch(error => {
  console.error('❌ Unexpected error:', error);
  process.exit(1);
}); 