#!/usr/bin/env node

import { copyFileSync, mkdirSync, existsSync, readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');
const distDir = join(rootDir, 'dist');

/**
 * Build script for YouTrack MCP npm package
 * 
 * This script:
 * 1. Creates the dist directory
 * 2. Copies Node.js source files
 * 3. Copies Python files
 * 4. Creates executable permissions for CLI
 */

async function build() {
console.log('🔨 Building YouTrack MCP npm package...');

// Clean and create dist directory
if (existsSync(distDir)) {
  console.log('🧹 Cleaning existing dist directory...');
  // Simple recursive remove - in production you might want to use a proper library
  await import('fs').then(fs => fs.rmSync(distDir, { recursive: true, force: true }));
}

mkdirSync(distDir, { recursive: true });
mkdirSync(join(distDir, 'bin'), { recursive: true });

// Copy Node.js files
console.log('📄 Copying Node.js source files...');
copyFileSync(join(rootDir, 'src', 'index.js'), join(distDir, 'index.js'));
copyFileSync(join(rootDir, 'src', 'bin', 'youtrack-mcp.js'), join(distDir, 'bin', 'youtrack-mcp.js'));

// Create python directory in dist and copy Python files
console.log('🐍 Copying Python source files...');
const pythonDistDir = join(distDir, 'python');
mkdirSync(pythonDistDir, { recursive: true });

// Copy main Python files
const filesToCopy = [
  'main.py',
  'requirements.txt'
];

for (const file of filesToCopy) {
  if (existsSync(join(rootDir, file))) {
    copyFileSync(join(rootDir, file), join(pythonDistDir, file));
    console.log(`  ✓ ${file}`);
  }
}

// Copy youtrack_mcp directory
const youtrackMcpSource = join(rootDir, 'youtrack_mcp');
const youtrackMcpDest = join(pythonDistDir, 'youtrack_mcp');

if (existsSync(youtrackMcpSource)) {
  console.log('📁 Copying youtrack_mcp directory...');
  
  // Simple directory copy function
  async function copyDir(src, dest) {
    mkdirSync(dest, { recursive: true });
    
    const { readdirSync, statSync } = await import('fs');
    const entries = readdirSync(src);
    
    for (const entry of entries) {
      const srcPath = join(src, entry);
      const destPath = join(dest, entry);
      
      if (statSync(srcPath).isDirectory()) {
        await copyDir(srcPath, destPath);
      } else {
        copyFileSync(srcPath, destPath);
      }
    }
  }
  
  await copyDir(youtrackMcpSource, youtrackMcpDest);
}

// Update the index.js to point to the correct Python path
console.log('🔧 Updating Python paths...');
const indexPath = join(distDir, 'index.js');
let indexContent = readFileSync(indexPath, 'utf8');

// Update the setupPaths method to use the correct python directory
indexContent = indexContent.replace(
  /join\(__dirname, '\.\.', 'main\.py'\)/g,
  "join(__dirname, 'python', 'main.py')"
);

writeFileSync(indexPath, indexContent);

// Make CLI executable
console.log('⚡ Setting executable permissions...');
try {
  const { chmodSync } = await import('fs');
  chmodSync(join(distDir, 'bin', 'youtrack-mcp.js'), 0o755);
} catch (error) {
  console.warn('⚠️  Could not set executable permissions:', error.message);
}

console.log('✅ Build completed successfully!');
console.log(`📦 Distribution created in: ${distDir}`);

// Show what was built
console.log('\n📋 Build contents:');
console.log('  dist/');
console.log('  ├── index.js (main Node.js wrapper)');
console.log('  ├── bin/youtrack-mcp.js (CLI executable)');
console.log('  └── python/ (Python MCP server)');
console.log('      ├── main.py');
console.log('      ├── requirements.txt');
console.log('      └── youtrack_mcp/ (Python package)');

console.log('\n🎯 Next steps:');
console.log('  1. Test locally: npm start');
console.log('  2. Publish to npm: npm publish');
console.log('  3. Install globally: npm install -g youtrack-mcp-tonyzorin');
}

build().catch(error => {
  console.error('❌ Build error:', error);
  process.exit(1);
}); 