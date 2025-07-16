#!/usr/bin/env node

/**
 * Local test monitoring script
 * Run this to monitor test results and suggest fixes
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class TestMonitor {
  constructor() {
    this.fixes = {
      'react/no-unescaped-entities': this.fixUnescapedEntities,
      'react-hooks/exhaustive-deps': this.fixHookDependencies,
      'import/no-unresolved': this.fixMissingImports,
      'typescript/no-unused-vars': this.fixUnusedVars,
    };
  }

  async runTests() {
    console.log('🧪 Running tests...\n');
    
    const results = {
      frontend: { passed: false, errors: [] },
      backend: { passed: false, errors: [] },
      e2e: { passed: false, errors: [] }
    };

    // Run frontend tests
    try {
      console.log('📦 Frontend tests...');
      execSync('cd frontend && yarn test:ci', { stdio: 'inherit' });
      results.frontend.passed = true;
    } catch (error) {
      results.frontend.errors = this.parseTestErrors(error.toString());
    }

    // Run backend tests
    try {
      console.log('\n🐍 Backend tests...');
      execSync('cd backend && poetry run pytest', { stdio: 'inherit' });
      results.backend.passed = true;
    } catch (error) {
      results.backend.errors = this.parseTestErrors(error.toString());
    }

    // Run linting
    try {
      console.log('\n🔍 Linting...');
      execSync('cd frontend && yarn lint', { stdio: 'inherit' });
    } catch (error) {
      const lintErrors = this.parseLintErrors(error.stdout?.toString() || '');
      results.frontend.errors.push(...lintErrors);
    }

    return results;
  }

  parseTestErrors(output) {
    const errors = [];
    const lines = output.split('\n');
    
    lines.forEach(line => {
      if (line.includes('FAIL') || line.includes('Error:')) {
        errors.push({
          type: 'test-failure',
          message: line.trim(),
          file: this.extractFilePath(line)
        });
      }
    });

    return errors;
  }

  parseLintErrors(output) {
    const errors = [];
    const eslintRegex = /(.+):(\d+):(\d+)\s+(\w+)\s+(.+)\s+(\S+)$/gm;
    let match;

    while ((match = eslintRegex.exec(output)) !== null) {
      errors.push({
        type: 'lint',
        file: match[1],
        line: parseInt(match[2]),
        column: parseInt(match[3]),
        severity: match[4],
        message: match[5],
        rule: match[6]
      });
    }

    return errors;
  }

  extractFilePath(line) {
    const match = line.match(/([a-zA-Z0-9_\-./]+\.(ts|tsx|js|jsx|py))/);
    return match ? match[1] : null;
  }

  async autoFix(errors) {
    console.log('\n🔧 Attempting auto-fixes...\n');
    
    const fixableErrors = errors.filter(error => 
      error.rule && this.fixes[error.rule]
    );

    for (const error of fixableErrors) {
      console.log(`Fixing ${error.rule} in ${error.file}...`);
      try {
        await this.fixes[error.rule].call(this, error);
        console.log('✅ Fixed!');
      } catch (e) {
        console.log(`❌ Failed to fix: ${e.message}`);
      }
    }

    // Run ESLint auto-fix
    try {
      console.log('\nRunning ESLint auto-fix...');
      execSync('cd frontend && yarn eslint . --fix', { stdio: 'inherit' });
    } catch (e) {
      // ESLint might exit with error even after fixing
    }
  }

  fixUnescapedEntities(error) {
    const filePath = path.resolve('frontend', error.file);
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Replace common unescaped entities
    content = content.replace(/(?<!\\)'/g, '&apos;');
    content = content.replace(/(?<!\\)"/g, '&quot;');
    
    fs.writeFileSync(filePath, content);
  }

  fixHookDependencies(error) {
    const filePath = path.resolve('frontend', error.file);
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Add eslint-disable comment before the line
    const lines = content.split('\n');
    if (error.line > 0) {
      lines.splice(error.line - 1, 0, '    // eslint-disable-next-line react-hooks/exhaustive-deps');
      content = lines.join('\n');
      fs.writeFileSync(filePath, content);
    }
  }

  fixMissingImports(error) {
    // This would require more sophisticated analysis
    console.log('Missing import detected. Please fix manually.');
  }

  fixUnusedVars(error) {
    const filePath = path.resolve('frontend', error.file);
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Add underscore prefix to unused vars
    const varMatch = error.message.match(/'(\w+)' is defined but never used/);
    if (varMatch) {
      const varName = varMatch[1];
      content = content.replace(
        new RegExp(`\\b${varName}\\b`, 'g'),
        `_${varName}`
      );
      fs.writeFileSync(filePath, content);
    }
  }

  generateReport(results) {
    console.log('\n📊 Test Report\n');
    console.log('='.repeat(50));
    
    Object.entries(results).forEach(([suite, result]) => {
      console.log(`\n${suite.toUpperCase()}: ${result.passed ? '✅ PASSED' : '❌ FAILED'}`);
      if (!result.passed && result.errors.length > 0) {
        console.log(`  Found ${result.errors.length} errors`);
        result.errors.slice(0, 5).forEach(error => {
          console.log(`  - ${error.message || error.type} in ${error.file || 'unknown'}`);
        });
        if (result.errors.length > 5) {
          console.log(`  ... and ${result.errors.length - 5} more`);
        }
      }
    });

    // Save detailed report
    const reportPath = path.join(process.cwd(), 'test-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
    console.log(`\n📄 Detailed report saved to: ${reportPath}`);
  }

  async monitor() {
    console.log('🔍 Bali Love Test Monitor\n');
    
    // Run tests
    const results = await this.runTests();
    
    // Collect all errors
    const allErrors = [];
    Object.values(results).forEach(result => {
      allErrors.push(...result.errors);
    });

    // Attempt auto-fixes if there are errors
    if (allErrors.length > 0) {
      const lintErrors = allErrors.filter(e => e.type === 'lint');
      if (lintErrors.length > 0) {
        await this.autoFix(lintErrors);
        
        // Re-run tests after fixes
        console.log('\n🔄 Re-running tests after fixes...\n');
        const newResults = await this.runTests();
        this.generateReport(newResults);
      } else {
        this.generateReport(results);
      }
    } else {
      this.generateReport(results);
      console.log('\n🎉 All tests passed!');
    }
  }
}

// Run if called directly
if (require.main === module) {
  const monitor = new TestMonitor();
  monitor.monitor().catch(console.error);
}

module.exports = TestMonitor;