# Testing Strategy for Chat LangChain

## Overview
A comprehensive testing approach covering unit, integration, and end-to-end tests for both frontend and backend.

## Testing Structure

### 1. Frontend Testing (React/Next.js)

#### Unit Tests
```
frontend/
├── __tests__/
│   ├── components/
│   │   ├── ChatLangChain.test.tsx
│   │   ├── PermissionStatus.test.tsx
│   │   ├── AdminRoute.test.tsx
│   │   └── ui/
│   │       ├── Button.test.tsx
│   │       └── Dialog.test.tsx
│   ├── hooks/
│   │   ├── usePermissions.test.tsx
│   │   ├── useThreads.test.tsx
│   │   └── useUser.test.tsx
│   ├── contexts/
│   │   ├── AuthContext.test.tsx
│   │   └── GraphContext.test.tsx
│   └── utils/
│       ├── convert_messages.test.ts
│       └── cookies.test.ts
├── jest.config.js
├── jest.setup.js
└── __mocks__/
    ├── @supabase/
    └── next/

```

#### Testing Libraries
- **Jest**: Test runner
- **React Testing Library**: Component testing
- **MSW (Mock Service Worker)**: API mocking
- **@testing-library/react-hooks**: Hook testing

### 2. Backend Testing (Python/LangGraph)

#### Unit Tests
```
backend/
├── tests/
│   ├── unit/
│   │   ├── test_retrieval_graph.py
│   │   ├── test_researcher_graph.py
│   │   ├── test_embeddings.py
│   │   ├── test_parser.py
│   │   └── test_configuration.py
│   ├── integration/
│   │   ├── test_graph_flow.py
│   │   ├── test_permissions.py
│   │   └── test_bubble_sync.py
│   └── e2e/
│       └── test_e2e.py
├── conftest.py
└── pytest.ini
```

#### Testing Libraries
- **pytest**: Test runner
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking
- **pytest-cov**: Coverage reports

## Test Categories

### 1. Unit Tests (70% coverage target)

#### Frontend Unit Tests
```typescript
// Example: usePermissions.test.tsx
import { renderHook } from '@testing-library/react-hooks'
import { usePermissions } from '@/app/hooks/usePermissions'

describe('usePermissions', () => {
  it('should return default permissions when no user', () => {
    const { result } = renderHook(() => usePermissions())
    expect(result.current.permissions).toBeNull()
    expect(result.current.loading).toBe(true)
  })

  it('should check agent access correctly', () => {
    const { result } = renderHook(() => usePermissions())
    // Mock data setup
    expect(result.current.hasAgent('general')).toBe(true)
  })
})
```

#### Backend Unit Tests
```python
# Example: test_retrieval_graph.py
import pytest
from backend.retrieval_graph.graph import create_graph

@pytest.mark.asyncio
async def test_graph_node_routing():
    graph = create_graph()
    result = await graph.ainvoke({
        "messages": [{"role": "user", "content": "Hello"}],
        "user_info": {"email": "test@example.com"}
    })
    assert "route" in result
```

### 2. Integration Tests (15% coverage target)

```python
# Example: test_permissions.py
@pytest.mark.asyncio
async def test_permission_filtering():
    # Test that users only see allowed data sources
    result = await retrieval_with_permissions(
        query="test query",
        user_permissions={"allowed_data_sources": ["docs"]}
    )
    assert all(doc.metadata["source"] == "docs" for doc in result)
```

### 3. E2E Tests (10% coverage target)

```typescript
// Example: chat-flow.e2e.ts
import { test, expect } from '@playwright/test'

test('complete chat interaction', async ({ page }) => {
  await page.goto('/')
  await page.fill('[data-testid="chat-input"]', 'What is LangChain?')
  await page.click('[data-testid="send-button"]')
  
  await expect(page.locator('[data-testid="message"]')).toContainText('LangChain')
})
```

## Testing Priorities

### Critical Paths to Test First:
1. **Authentication Flow**
   - Login/logout
   - Permission checking
   - Protected routes

2. **Chat Functionality**
   - Message sending/receiving
   - Streaming responses
   - Error handling

3. **Permission System**
   - Access control
   - Data filtering
   - Admin functions

4. **Data Retrieval**
   - Vector search
   - Context building
   - Source attribution

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
      - run: cd frontend && yarn install
      - run: cd frontend && yarn test:ci
      - run: cd frontend && yarn test:coverage

  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
      - run: poetry install
      - run: poetry run pytest --cov
```

## Coverage Goals

- **Overall**: 80% coverage
- **Critical paths**: 95% coverage
- **UI Components**: 70% coverage
- **Utilities**: 90% coverage

## Mock Data Strategy

### Frontend Mocks
```typescript
// __mocks__/supabase.ts
export const mockSupabase = {
  auth: {
    getUser: jest.fn(),
    signIn: jest.fn(),
    signOut: jest.fn()
  },
  from: jest.fn(() => ({
    select: jest.fn().mockReturnThis(),
    eq: jest.fn().mockReturnThis(),
    single: jest.fn()
  }))
}
```

### Backend Fixtures
```python
# conftest.py
@pytest.fixture
def mock_user():
    return {
        "email": "test@bali.love",
        "team": "general",
        "role": "member"
    }

@pytest.fixture
def mock_permissions():
    return {
        "allowed_agents": ["general"],
        "allowed_data_sources": ["docs", "api"]
    }
```

## Implementation Steps

1. **Phase 1**: Set up testing infrastructure
   - Install testing libraries
   - Configure Jest and pytest
   - Set up coverage reporting

2. **Phase 2**: Critical path tests
   - Auth flow tests
   - Permission checks
   - Basic chat functionality

3. **Phase 3**: Component tests
   - UI component tests
   - Hook tests
   - Utility function tests

4. **Phase 4**: Integration tests
   - API integration tests
   - Database interaction tests
   - Graph flow tests

5. **Phase 5**: E2E tests
   - Full user journeys
   - Cross-browser testing
   - Performance tests