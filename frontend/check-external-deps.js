#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Patterns to search for external dependencies
const patterns = [
  /https?:\/\/[^\s"']+/g,  // HTTP/HTTPS URLs
  /fonts\.googleapis\.com/g,  // Google Fonts
  /fonts\.gstatic\.com/g,     // Google Fonts static
  /@import.*url\(/g,          // CSS @import with URLs
  /next\/font\/google/g,      // Next.js Google fonts
];

// File extensions to check
const extensions = ['.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.json'];

// Directories to exclude
const excludeDirs = ['node_modules', '.next', '.git', 'dist', 'build'];

function shouldExcludeFile(filePath) {
  return excludeDirs.some(dir => filePath.includes(dir));
}

function checkFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const issues = [];
    
    patterns.forEach((pattern, index) => {
      const matches = content.match(pattern);
      if (matches) {
        matches.forEach(match => {
          // Skip some allowed URLs
          if (match.includes('localhost') || 
              match.includes('127.0.0.1') ||
              match.includes('process.env') ||
              match.includes('example.com') ||
              match.includes('chat.openai.com') || // This is intentional for error reporting
              match.includes('ahanait.com') || // Company links are OK
              match.includes('linkedin.com') || // Social links are OK
              match.includes('twitter.com') || // Social links are OK
              match.includes('github.com')) { // Social links are OK
            return;
          }
          
          issues.push({
            pattern: pattern.toString(),
            match: match,
            line: content.split('\n').findIndex(line => line.includes(match)) + 1
          });
        });
      }
    });
    
    return issues;
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error.message);
    return [];
  }
}

function scanDirectory(dir) {
  const results = [];
  
  try {
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      
      if (shouldExcludeFile(fullPath)) {
        continue;
      }
      
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        results.push(...scanDirectory(fullPath));
      } else if (stat.isFile() && extensions.some(ext => item.endsWith(ext))) {
        const issues = checkFile(fullPath);
        if (issues.length > 0) {
          results.push({
            file: fullPath,
            issues: issues
          });
        }
      }
    }
  } catch (error) {
    console.error(`Error scanning directory ${dir}:`, error.message);
  }
  
  return results;
}

function main() {
  console.log('🔍 Checking for external dependencies...\n');
  
  const srcDir = path.join(__dirname, 'src');
  const results = scanDirectory(srcDir);
  
  if (results.length === 0) {
    console.log('✅ No external dependencies found! Your application is ready for offline deployment.');
    return;
  }
  
  console.log('❌ Found potential external dependencies:\n');
  
  results.forEach(result => {
    console.log(`📄 File: ${result.file}`);
    result.issues.forEach(issue => {
      console.log(`   Line ${issue.line}: ${issue.match}`);
    });
    console.log('');
  });
  
  console.log(`\n📊 Summary: Found ${results.length} files with potential external dependencies.`);
  console.log('Please review these and ensure they are either removed or acceptable for your offline environment.');
}

if (require.main === module) {
  main();
} 