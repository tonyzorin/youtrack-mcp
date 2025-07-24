#!/usr/bin/env node

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * YouTrack MCP Server Node.js Wrapper
 * 
 * This wrapper allows the Python-based YouTrack MCP server to be installed
 * and executed via npm/npx, following MCP packaging conventions.
 */
class YouTrackMCPServer {
  constructor() {
    this.pythonPath = null;
    this.serverPath = null;
    this.setupPaths();
  }

  setupPaths() {
    // Use python3 by default, fall back to python
    // The actual existence check will happen when we try to run it
    this.pythonPath = 'python3';

    // Find the server main.py file
    const possiblePaths = [
      join(__dirname, '..', 'main.py'),           // From dist/
      join(__dirname, '..', 'python', 'main.py'), // From python/ directory
      join(__dirname, 'main.py')                   // Current directory
    ];

    for (const path of possiblePaths) {
      if (existsSync(path)) {
        this.serverPath = path;
        break;
      }
    }

    if (!this.serverPath) {
      throw new Error('YouTrack MCP server main.py not found');
    }
  }

  /**
   * Start the YouTrack MCP server
   * @param {string[]} args - Command line arguments to pass to the Python server
   * @param {Object} options - Additional options
   * @returns {Promise<void>}
   */
  async start(args = [], options = {}) {
    console.log('🚀 Starting YouTrack MCP Server...');
    
    // Validate environment variables
    this.validateEnvironment();

    const pythonArgs = [this.serverPath, ...args];
    
    console.log(`📍 Using Python: ${this.pythonPath}`);
    console.log(`📍 Server path: ${this.serverPath}`);
    console.log(`📍 Arguments: ${pythonArgs.slice(1).join(' ')}`);

    return new Promise((resolve, reject) => {
      const child = spawn(this.pythonPath, pythonArgs, {
        stdio: options.stdio || 'inherit',
        env: { ...process.env, ...options.env },
        cwd: options.cwd || process.cwd()
      });

      child.on('error', (error) => {
        console.error('❌ Failed to start YouTrack MCP server:', error.message);
        reject(error);
      });

      child.on('exit', (code) => {
        if (code === 0) {
          console.log('✅ YouTrack MCP server exited successfully');
          resolve();
        } else {
          console.error(`❌ YouTrack MCP server exited with code ${code}`);
          reject(new Error(`Server exited with code ${code}`));
        }
      });

      // Handle graceful shutdown
      process.on('SIGINT', () => {
        console.log('\n🛑 Shutting down YouTrack MCP server...');
        child.kill('SIGINT');
      });

      process.on('SIGTERM', () => {
        console.log('\n🛑 Terminating YouTrack MCP server...');
        child.kill('SIGTERM');
      });
    });
  }

  validateEnvironment() {
    const requiredVars = ['YOUTRACK_URL', 'YOUTRACK_API_TOKEN'];
    const missingVars = requiredVars.filter(varName => !process.env[varName]);
    
    if (missingVars.length > 0) {
      console.warn('⚠️  Warning: Missing environment variables:', missingVars.join(', '));
      console.warn('   The server may not function properly without these variables.');
      console.warn('   Please set them in your environment or .env file.');
    } else {
      console.log('✅ Environment variables validated');
    }
  }

  /**
   * Get server information
   */
  getInfo() {
    return {
      name: 'YouTrack MCP Server',
      version: '1.11.1',
      description: 'A Model Context Protocol server for JetBrains YouTrack',
      pythonPath: this.pythonPath,
      serverPath: this.serverPath,
      homepage: 'https://github.com/tonyzorin/youtrack-mcp'
    };
  }
}

export default YouTrackMCPServer; 