import { test, expect } from '@playwright/test'

test.describe('Chat Interface', () => {
  test.use({
    storageState: 'e2e/.auth/user.json' // Authenticated state
  })

  test.beforeEach(async ({ page }) => {
    // Mock API responses for authenticated user
    await page.route('**/rest/v1/user_teams**', async route => {
      await route.fulfill({
        status: 200,
        json: {
          email: 'test@bali.love',
          team_id: 'bali-love-team',
          team_name: 'Bali Love',
          role: 'member',
          allowed_agents: ['chat', 'search'],
          allowed_data_sources: ['events', 'inbox_messages', 'training'],
        }
      })
    })

    await page.goto('/')
  })

  test('should display chat interface', async ({ page }) => {
    // Check main chat elements
    await expect(page.getByRole('textbox', { name: /message/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /send/i })).toBeVisible()
    
    // Thread history should be visible
    await expect(page.getByText(/conversations/i)).toBeVisible()
  })

  test('should send a message and receive response', async ({ page }) => {
    // Mock thread creation
    await page.route('**/threads', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          json: {
            thread_id: 'thread-123',
            user_id: 'user-123',
            created_at: new Date().toISOString(),
          }
        })
      }
    })

    // Mock message streaming
    await page.route('**/threads/thread-123/runs/stream', async route => {
      await route.fulfill({
        status: 200,
        headers: {
          'content-type': 'text/event-stream',
        },
        body: `data: {"event": "on_chat_model_stream", "data": {"chunk": {"content": "Hello! I can help you with wedding planning."}}}\n\n`
      })
    })

    // Type and send message
    const messageInput = page.getByRole('textbox', { name: /message/i })
    await messageInput.fill('Hello, I need help with wedding planning')
    await page.getByRole('button', { name: /send/i }).click()

    // Check that message appears
    await expect(page.getByText('Hello, I need help with wedding planning')).toBeVisible()
    
    // Check for response
    await expect(page.getByText(/I can help you with wedding planning/i)).toBeVisible()
  })

  test('should search for event information', async ({ page }) => {
    // Mock search results
    await page.route('**/threads/*/runs/stream', async route => {
      await route.fulfill({
        status: 200,
        headers: {
          'content-type': 'text/event-stream',
        },
        body: `data: {"event": "on_chat_model_stream", "data": {"chunk": {"content": "Here's information about event KM150726VV:\\n\\nThe Smith Wedding is scheduled for July 26, 2024 at Beach Club Bali."}}}\n\n`
      })
    })

    // Search for specific event
    const messageInput = page.getByRole('textbox', { name: /message/i })
    await messageInput.fill('Tell me about event KM150726VV')
    await page.getByRole('button', { name: /send/i }).click()

    // Check for event information in response
    await expect(page.getByText(/KM150726VV/)).toBeVisible()
    await expect(page.getByText(/Smith Wedding/i)).toBeVisible()
    await expect(page.getByText(/Beach Club Bali/i)).toBeVisible()
  })

  test('should show permission-based error for restricted content', async ({ page }) => {
    // Mock permission denied response
    await page.route('**/threads/*/runs/stream', async route => {
      await route.fulfill({
        status: 200,
        headers: {
          'content-type': 'text/event-stream',
        },
        body: `data: {"event": "on_chat_model_stream", "data": {"chunk": {"content": "I don't have access to vendor pricing information. This data is restricted to managers and administrators."}}}\n\n`
      })
    })

    // Try to access restricted content
    const messageInput = page.getByRole('textbox', { name: /message/i })
    await messageInput.fill('Show me vendor pricing details')
    await page.getByRole('button', { name: /send/i }).click()

    // Check for permission message
    await expect(page.getByText(/don't have access/i)).toBeVisible()
    await expect(page.getByText(/restricted to managers/i)).toBeVisible()
  })

  test('should handle message errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/threads/*/runs/stream', async route => {
      await route.fulfill({
        status: 500,
        json: {
          error: 'Internal server error'
        }
      })
    })

    // Send message
    const messageInput = page.getByRole('textbox', { name: /message/i })
    await messageInput.fill('Test message')
    await page.getByRole('button', { name: /send/i }).click()

    // Should show error toast
    await expect(page.getByText(/error occurred/i)).toBeVisible()
  })

  test('should disable input while processing', async ({ page }) => {
    // Mock slow response
    await page.route('**/threads/*/runs/stream', async route => {
      // Delay response
      await new Promise(resolve => setTimeout(resolve, 2000))
      await route.fulfill({
        status: 200,
        headers: {
          'content-type': 'text/event-stream',
        },
        body: `data: {"event": "on_chat_model_stream", "data": {"chunk": {"content": "Response"}}}\n\n`
      })
    })

    // Send message
    const messageInput = page.getByRole('textbox', { name: /message/i })
    const sendButton = page.getByRole('button', { name: /send/i })
    
    await messageInput.fill('Test message')
    await sendButton.click()

    // Input should be disabled while processing
    await expect(sendButton).toBeDisabled()
    
    // Wait for response
    await expect(page.getByText('Response')).toBeVisible({ timeout: 5000 })
    
    // Input should be enabled again
    await expect(sendButton).toBeEnabled()
  })
})

test.describe('Thread Management', () => {
  test.use({
    storageState: 'e2e/.auth/user.json'
  })

  test('should display thread history', async ({ page }) => {
    // Mock thread list
    await page.route('**/threads**', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          json: [
            {
              thread_id: 'thread-1',
              name: 'Wedding venue inquiry',
              created_at: '2024-01-15T10:00:00Z',
              updated_at: '2024-01-15T10:30:00Z',
            },
            {
              thread_id: 'thread-2',
              name: 'Catering options',
              created_at: '2024-01-14T15:00:00Z',
              updated_at: '2024-01-14T15:45:00Z',
            }
          ]
        })
      }
    })

    await page.goto('/')

    // Check thread list
    await expect(page.getByText('Wedding venue inquiry')).toBeVisible()
    await expect(page.getByText('Catering options')).toBeVisible()
  })

  test('should switch between threads', async ({ page }) => {
    // Mock thread messages
    await page.route('**/threads/thread-1/messages', async route => {
      await route.fulfill({
        status: 200,
        json: [
          {
            id: 'msg-1',
            content: 'Looking for beach wedding venues',
            role: 'human',
          },
          {
            id: 'msg-2',
            content: 'I recommend Beach Club Bali for your wedding.',
            role: 'assistant',
          }
        ]
      })
    })

    await page.goto('/')

    // Click on a thread
    await page.getByText('Wedding venue inquiry').click()

    // Should load thread messages
    await expect(page.getByText('Looking for beach wedding venues')).toBeVisible()
    await expect(page.getByText('Beach Club Bali')).toBeVisible()
  })

  test('should create new thread', async ({ page }) => {
    await page.goto('/')

    // Click new thread button
    await page.getByRole('button', { name: /new.*conversation/i }).click()

    // Should clear messages and focus input
    const messageInput = page.getByRole('textbox', { name: /message/i })
    await expect(messageInput).toBeFocused()
  })
})