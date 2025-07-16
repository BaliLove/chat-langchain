# Testing and Monitoring Guide

## Overview

This guide covers the automated testing and monitoring setup for the Bali Love Chat application.

## Automated Testing

### Local Testing

Run all tests:
```bash
npm run test:all
```

Individual test suites:
```bash
npm run test:frontend    # Frontend unit tests
npm run test:backend     # Backend pytest
npm run test:e2e        # Playwright E2E tests
```

### Test Monitoring

Use the test monitor to automatically detect and fix common issues:
```bash
npm run test:monitor
```

This will:
- Run all test suites
- Detect common failures (ESLint, import errors, etc.)
- Attempt auto-fixes
- Generate a detailed report

### Pre-commit Hooks

Tests run automatically before commits via Husky:
- ESLint with auto-fix
- TypeScript checking
- Python linting with Ruff

## CI/CD Monitoring

### GitHub Actions Workflows

1. **Frontend Tests** (`frontend-tests.yml`)
   - Runs on every push/PR
   - Linting, type checking, unit tests
   - Coverage reporting

2. **Auto-Fix Tests** (`auto-fix-tests.yml`)
   - Triggered when Frontend Tests fail
   - Attempts common fixes
   - Creates PR with fixes

3. **CI/CD Monitoring** (`monitoring.yml`)
   - Runs every 6 hours
   - Checks for failed workflows
   - Creates issues for persistent failures
   - Detects flaky tests

### Notifications

Configure notifications by setting environment variables:

```bash
# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Discord  
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Email
EMAIL_NOTIFICATIONS=true
NOTIFICATION_EMAIL=team@bali.love
```

## Dependency Management

### Dependabot

Automated dependency updates weekly:
- Frontend (npm)
- Backend (pip)
- GitHub Actions

PRs are created automatically with:
- Security updates (immediate)
- Version updates (weekly)

### Manual Dependency Check

```bash
# Check for outdated packages
cd frontend && yarn outdated
cd backend && poetry show --outdated
```

## Test Coverage

### Coverage Requirements

- Frontend: 70% lines, 60% branches
- Backend: 70% overall

### View Coverage Reports

```bash
# Frontend
cd frontend && yarn test:coverage
# Report at: frontend/coverage/index.html

# Backend  
cd backend && poetry run pytest --cov-report=html
# Report at: backend/htmlcov/index.html
```

## Troubleshooting

### Common Issues

1. **ESLint Errors**
   ```bash
   npm run fix:lint
   ```

2. **Type Errors**
   ```bash
   cd frontend && yarn tsc --noEmit
   ```

3. **Flaky Tests**
   - Check the monitoring workflow
   - Look for "flaky-test" labeled issues

### Manual Fixes

If auto-fix fails:

1. Check the error logs
2. Run specific test suite in watch mode
3. Fix issues manually
4. Re-run test monitor

## Best Practices

1. **Keep Tests Fast**
   - Mock external services
   - Use test databases
   - Parallelize where possible

2. **Write Reliable Tests**
   - Avoid time-dependent assertions
   - Clean up after tests
   - Use proper async handling

3. **Monitor Trends**
   - Watch coverage trends
   - Track test execution time
   - Review flaky test reports

## Integration with Development

### VS Code Extensions

Recommended extensions for test development:
- Jest Runner
- Python Test Explorer
- ESLint
- Playwright Test for VSCode

### Running Tests in IDE

Most tests can be run directly from VS Code:
- Click the play button next to test names
- Use Test Explorer panel
- Set breakpoints for debugging