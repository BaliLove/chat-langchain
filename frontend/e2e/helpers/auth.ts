import { Page } from '@playwright/test'

export async function loginAs(page: Page, role: 'member' | 'manager' | 'admin') {
  const users = {
    member: {
      email: 'member@bali.love',
      password: 'member123',
      permissions: {
        role: 'member',
        allowed_agents: ['chat', 'search'],
        allowed_data_sources: ['events', 'inbox_messages', 'training'],
      }
    },
    manager: {
      email: 'manager@bali.love',
      password: 'manager123',
      permissions: {
        role: 'manager',
        allowed_agents: ['chat', 'search', 'message-finder', 'event-analyzer'],
        allowed_data_sources: ['events', 'inbox_messages', 'vendors', 'issues', 'training'],
      }
    },
    admin: {
      email: 'admin@bali.love',
      password: 'admin123',
      permissions: {
        role: 'admin',
        allowed_agents: ['*'],
        allowed_data_sources: ['*'],
      }
    }
  }

  const user = users[role]

  // Mock successful authentication
  await page.route('**/auth/v1/token**', async route => {
    await route.fulfill({
      status: 200,
      json: {
        access_token: `mock-token-${role}`,
        token_type: 'bearer',
        expires_in: 3600,
        refresh_token: `mock-refresh-${role}`,
        user: {
          id: `user-${role}-123`,
          email: user.email,
          email_confirmed_at: new Date().toISOString(),
        }
      }
    })
  })

  // Mock user team data
  await page.route('**/rest/v1/user_teams**', async route => {
    await route.fulfill({
      status: 200,
      json: {
        email: user.email,
        team_id: 'bali-love-team',
        team_name: 'Bali Love',
        ...user.permissions,
        created_at: new Date().toISOString(),
      }
    })
  })

  // Navigate to login and authenticate
  await page.goto('/login')
  await page.getByPlaceholder(/email/i).fill(user.email)
  await page.getByPlaceholder(/password/i).fill(user.password)
  await page.getByRole('button', { name: /sign in/i }).click()

  // Wait for redirect
  await page.waitForURL('/')
}

export async function setupAuthState(page: Page, role: 'member' | 'manager' | 'admin') {
  // Set up localStorage with auth token
  await page.context().addInitScript((role) => {
    const mockAuth = {
      access_token: `mock-token-${role}`,
      token_type: 'bearer',
      expires_at: Date.now() + 3600000,
      refresh_token: `mock-refresh-${role}`,
      user: {
        id: `user-${role}-123`,
        email: `${role}@bali.love`,
      }
    }
    localStorage.setItem('supabase.auth.token', JSON.stringify(mockAuth))
  }, role)
}

export async function mockApiResponses(page: Page) {
  // Mock common API endpoints
  
  // Threads endpoint
  await page.route('**/threads**', async route => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        json: []
      })
    } else if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 201,
        json: {
          thread_id: 'new-thread-123',
          user_id: 'user-123',
          created_at: new Date().toISOString(),
        }
      })
    }
  })

  // Health check
  await page.route('**/health**', async route => {
    await route.fulfill({
      status: 200,
      json: { status: 'ok' }
    })
  })
}

export async function waitForChat(page: Page) {
  // Wait for chat interface to be ready
  await page.waitForSelector('[role="textbox"][name*="message" i]', { state: 'visible' })
  await page.waitForSelector('[role="button"][name*="send" i]', { state: 'visible' })
}