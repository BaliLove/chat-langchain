import { test, expect } from '@playwright/test'

test.describe('Admin Features', () => {
  test.use({
    storageState: 'e2e/.auth/admin.json' // Admin authenticated state
  })

  test.beforeEach(async ({ page }) => {
    // Mock admin user data
    await page.route('**/rest/v1/user_teams**', async route => {
      await route.fulfill({
        status: 200,
        json: {
          email: 'admin@bali.love',
          team_id: 'bali-love-team',
          team_name: 'Bali Love',
          role: 'admin',
          allowed_agents: ['*'],
          allowed_data_sources: ['*'],
        }
      })
    })
  })

  test('should access admin team members page', async ({ page }) => {
    await page.goto('/admin/team-members')

    // Should see team members page
    await expect(page.getByRole('heading', { name: /team members/i })).toBeVisible()
    
    // Should see stats cards
    await expect(page.getByText(/total members/i)).toBeVisible()
    await expect(page.getByText(/teams/i)).toBeVisible()
    await expect(page.getByText(/admins/i)).toBeVisible()
    await expect(page.getByText(/managers/i)).toBeVisible()
  })

  test('should filter team members by role', async ({ page }) => {
    // Mock team members data
    await page.route('**/rest/v1/user_teams**', async route => {
      if (route.request().url().includes('select=*')) {
        await route.fulfill({
          status: 200,
          json: [
            {
              email: 'admin@bali.love',
              team_name: 'Bali Love',
              role: 'admin',
              allowed_agents: ['*'],
              allowed_data_sources: ['*'],
            },
            {
              email: 'manager@bali.love',
              team_name: 'Bali Love',
              role: 'manager',
              allowed_agents: ['chat', 'search', 'message-finder'],
              allowed_data_sources: ['events', 'inbox_messages', 'vendors'],
            },
            {
              email: 'member@bali.love',
              team_name: 'Bali Love',
              role: 'member',
              allowed_agents: ['chat', 'search'],
              allowed_data_sources: ['events', 'inbox_messages'],
            }
          ]
        })
      }
    })

    await page.goto('/admin/team-members')

    // Click Admins filter
    await page.getByRole('button', { name: 'Admins' }).click()

    // Should only show admin users
    await expect(page.getByText('admin@bali.love')).toBeVisible()
    await expect(page.getByText('manager@bali.love')).not.toBeVisible()
    await expect(page.getByText('member@bali.love')).not.toBeVisible()

    // Click Managers filter
    await page.getByRole('button', { name: 'Managers' }).click()

    // Should only show manager users
    await expect(page.getByText('admin@bali.love')).not.toBeVisible()
    await expect(page.getByText('manager@bali.love')).toBeVisible()
    await expect(page.getByText('member@bali.love')).not.toBeVisible()
  })

  test('should view member details', async ({ page }) => {
    await page.goto('/admin/team-members')

    // Click on a team member
    await page.getByText('member@bali.love').click()

    // Should open modal with member details
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByText(/member details/i)).toBeVisible()
    
    // Should show permissions
    await expect(page.getByText(/permissions/i)).toBeVisible()
    await expect(page.getByText(/agent access/i)).toBeVisible()
    await expect(page.getByText(/data source access/i)).toBeVisible()
  })

  test('should search team members', async ({ page }) => {
    await page.goto('/admin/team-members')

    // Search for specific member
    const searchInput = page.getByPlaceholder(/search by email/i)
    await searchInput.fill('manager@bali')

    // Should filter results
    await expect(page.getByText('manager@bali.love')).toBeVisible()
    await expect(page.getByText('member@bali.love')).not.toBeVisible()
  })

  test('non-admin should be redirected from admin pages', async ({ page }) => {
    // Mock non-admin user
    await page.route('**/rest/v1/user_teams**', async route => {
      await route.fulfill({
        status: 200,
        json: {
          email: 'member@bali.love',
          role: 'member',
          allowed_agents: ['chat'],
          allowed_data_sources: ['events'],
        }
      })
    })

    // Try to access admin page
    await page.goto('/admin/team-members')

    // Should redirect to home
    await expect(page).toHaveURL('/')
  })
})

test.describe('Permission-based Access', () => {
  test('member should see limited data sources', async ({ page }) => {
    // Mock member permissions
    await page.route('**/rest/v1/user_teams**', async route => {
      await route.fulfill({
        status: 200,
        json: {
          email: 'member@bali.love',
          role: 'member',
          allowed_agents: ['chat', 'search'],
          allowed_data_sources: ['events', 'inbox_messages'],
        }
      })
    })

    await page.goto('/')

    // Check that only allowed features are visible
    // This would depend on your UI implementation
    // For example, certain menu items or options might be hidden
  })

  test('manager should see extended features', async ({ page }) => {
    // Mock manager permissions
    await page.route('**/rest/v1/user_teams**', async route => {
      await route.fulfill({
        status: 200,
        json: {
          email: 'manager@bali.love',
          role: 'manager',
          allowed_agents: ['chat', 'search', 'message-finder', 'event-analyzer'],
          allowed_data_sources: ['events', 'inbox_messages', 'vendors', 'issues'],
        }
      })
    })

    await page.goto('/')

    // Manager should see additional features
    // This would depend on your UI implementation
  })

  test('admin should have full access', async ({ page }) => {
    // Mock admin permissions
    await page.route('**/rest/v1/user_teams**', async route => {
      await route.fulfill({
        status: 200,
        json: {
          email: 'admin@bali.love',
          role: 'admin',
          allowed_agents: ['*'],
          allowed_data_sources: ['*'],
        }
      })
    })

    await page.goto('/')

    // Admin should see all features
    // Should be able to access admin menu
    await expect(page.getByText(/admin/i)).toBeVisible()
  })
})