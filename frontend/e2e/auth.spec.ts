import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('should display login page', async ({ page }) => {
    // Check for login page elements
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()
    await expect(page.getByPlaceholder(/email/i)).toBeVisible()
    await expect(page.getByPlaceholder(/password/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })

  test('should show error for invalid domain email', async ({ page }) => {
    // Try to login with unauthorized domain
    await page.getByPlaceholder(/email/i).fill('test@unauthorized.com')
    await page.getByPlaceholder(/password/i).fill('password123')
    await page.getByRole('button', { name: /sign in/i }).click()

    // Should show error message
    await expect(page.getByText(/not authorized/i)).toBeVisible()
  })

  test('should redirect to main app after successful login', async ({ page }) => {
    // Mock successful login
    await page.route('**/auth/v1/token**', async route => {
      await route.fulfill({
        status: 200,
        json: {
          access_token: 'mock-token',
          token_type: 'bearer',
          expires_in: 3600,
          refresh_token: 'mock-refresh-token',
          user: {
            id: 'user-123',
            email: 'test@bali.love',
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
          email: 'test@bali.love',
          team_id: 'bali-love-team',
          team_name: 'Bali Love',
          role: 'member',
          allowed_agents: ['chat', 'search'],
          allowed_data_sources: ['events', 'inbox_messages'],
        }
      })
    })

    // Perform login
    await page.getByPlaceholder(/email/i).fill('test@bali.love')
    await page.getByPlaceholder(/password/i).fill('password123')
    await page.getByRole('button', { name: /sign in/i }).click()

    // Should redirect to main app
    await expect(page).toHaveURL('/')
    await expect(page.getByText(/test@bali.love/i)).toBeVisible()
  })

  test('should handle login errors gracefully', async ({ page }) => {
    // Mock failed login
    await page.route('**/auth/v1/token**', async route => {
      await route.fulfill({
        status: 400,
        json: {
          error: 'invalid_grant',
          error_description: 'Invalid login credentials'
        }
      })
    })

    // Try to login
    await page.getByPlaceholder(/email/i).fill('test@bali.love')
    await page.getByPlaceholder(/password/i).fill('wrongpassword')
    await page.getByRole('button', { name: /sign in/i }).click()

    // Should show error
    await expect(page.getByText(/invalid login credentials/i)).toBeVisible()
  })

  test('should allow sign out', async ({ page }) => {
    // Navigate to app as authenticated user
    await page.goto('/')
    
    // Mock authenticated state
    await page.evaluate(() => {
      localStorage.setItem('supabase.auth.token', JSON.stringify({
        access_token: 'mock-token',
        expires_at: Date.now() + 3600000,
      }))
    })

    // Find and click sign out button
    await page.getByRole('button', { name: /sign out/i }).click()

    // Should redirect to login
    await expect(page).toHaveURL('/login')
  })
})