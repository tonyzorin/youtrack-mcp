#!/usr/bin/env node

import { spawn } from 'child_process';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');

/**
 * Test script for YouTrack MCP npm package
 * 
 * This script validates that:
 * 1. The package builds correctly
 * 2. The Python server can be found and started
 * 3. Basic functionality works
 */

console.log('🧪 Testing YouTrack MCP npm package...');

async function runCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      stdio: 'pipe',
      cwd: rootDir,
      ...options
    });

    let stdout = '';
    let stderr = '';

    child.stdout?.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr?.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('close', (code) => {
      resolve({ code, stdout, stderr });
    });

    child.on('error', reject);
  });
}

async function test() {
  let passed = 0;
  let failed = 0;

  function logTest(name, success, message = '') {
    if (success) {
      console.log(`✅ ${name}`);
      passed++;
    } else {
      console.log(`❌ ${name}: ${message}`);
      failed++;
    }
  }

  // Test 1: Check if dist directory exists
  const distExists = existsSync(join(rootDir, 'dist'));
  logTest('Distribution directory exists', distExists, 'Run npm run build first');

  if (!distExists) {
    console.log('\n🔨 Building package first...');
    const buildResult = await runCommand('npm', ['run', 'build']);
    logTest('Build successful', buildResult.code === 0, buildResult.stderr);
  }

  // Test 2: Check if main files exist
  const mainFiles = [
    'dist/index.js',
    'dist/bin/youtrack-mcp.js',
    'dist/python/main.py',
    'dist/python/youtrack_mcp'
  ];

  for (const file of mainFiles) {
    const exists = existsSync(join(rootDir, file));
    logTest(`File exists: ${file}`, exists);
  }

  // Test 3: Test CLI help command
  try {
    const helpResult = await runCommand('node', ['dist/bin/youtrack-mcp.js', '--help']);
    logTest('CLI help command works', helpResult.code === 0 && helpResult.stdout.includes('YouTrack MCP Server CLI'));
  } catch (error) {
    logTest('CLI help command works', false, error.message);
  }

  // Test 4: Test version command
  try {
    const versionResult = await runCommand('node', ['dist/bin/youtrack-mcp.js', '--version']);
    logTest('CLI version command works', versionResult.code === 0 && versionResult.stdout.includes('YouTrack MCP Server'));
  } catch (error) {
    logTest('CLI version command works', false, error.message);
  }

  // Test 5: Test info command
  try {
    const infoResult = await runCommand('node', ['dist/bin/youtrack-mcp.js', '--info']);
    logTest('CLI info command works', infoResult.code === 0 && infoResult.stdout.includes('Server Information'));
  } catch (error) {
    logTest('CLI info command works', false, error.message);
  }

  // Test 6: Test Python import
  try {
    const pythonTest = await runCommand('python3', ['-c', 'import sys; sys.path.append("dist/python"); import youtrack_mcp; print("Import successful")']);
    logTest('Python import works', pythonTest.code === 0 && pythonTest.stdout.includes('Import successful'));
  } catch (error) {
    // Try with python instead of python3
    try {
      const pythonTest2 = await runCommand('python', ['-c', 'import sys; sys.path.append("dist/python"); import youtrack_mcp; print("Import successful")']);
      logTest('Python import works', pythonTest2.code === 0 && pythonTest2.stdout.includes('Import successful'));
    } catch (error2) {
      logTest('Python import works', false, 'Python not found or import failed');
    }
  }

  // Test 7: Check package.json validity
  try {
    const { readFileSync } = await import('fs');
    const packageJsonContent = readFileSync(join(rootDir, 'package.json'), 'utf8');
    const packageJson = JSON.parse(packageJsonContent);
    const hasRequiredFields = packageJson.name && packageJson.version && packageJson.main && packageJson.bin;
    logTest('package.json is valid', hasRequiredFields);
  } catch (error) {
    logTest('package.json is valid', false, error.message);
  }

  // Summary
  console.log('\n📊 Test Results:');
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%`);

  if (failed === 0) {
    console.log('\n🎉 All tests passed! Package is ready for publishing.');
    console.log('\n📦 To publish:');
    console.log('  npm publish --access public');
  } else {
    console.log('\n🔧 Some tests failed. Please fix the issues before publishing.');
    process.exit(1);
  }
}

test().catch(error => {
  console.error('❌ Test runner error:', error);
  process.exit(1);
}); 