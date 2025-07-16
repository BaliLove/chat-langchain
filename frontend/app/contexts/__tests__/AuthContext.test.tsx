import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import { AuthProvider, useAuth } from '../AuthContext'
import { mockSupabaseClient, resetSupabaseMocks } from '@/app/test-utils/supabase-mock'
import { createMockUser, createMockUserTeamData } from '@/app/test-utils/test-providers'

// Test component to access auth context
const TestComponent = () => {
  const auth = useAuth()
  return (
    <div>
      <div data-testid="user-email">{auth.user?.email || 'No user'}</div>
      <div data-testid="loading">{auth.loading ? 'Loading' : 'Loaded'}</div>
      <div data-testid="authorized">{auth.isAuthorized ? 'Authorized' : 'Unauthorized'}</div>
      <div data-testid="team-role">{auth.userTeamData?.role || 'No role'}</div>
      <button onClick={auth.signOut}>Sign Out</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    resetSupabaseMocks()
    // Mock environment variable
    process.env.NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS = 'bali.love,example.com'
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('should provide initial auth state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    expect(screen.getByTestId('user-email')).toHaveTextContent('No user')
    expect(screen.getByTestId('loading')).toHaveTextContent('Loading')
    expect(screen.getByTestId('authorized')).toHaveTextContent('Unauthorized')
  })

  it('should load authenticated user with valid domain', async () => {
    const mockUser = createMockUser({ email: 'test@bali.love' })
    const mockTeamData = createMockUserTeamData({ 
      email: 'test@bali.love',
      role: 'admin' 
    })

    mockSupabaseClient.auth.getUser.mockResolvedValueOnce({
      data: { user: mockUser },
      error: null,
    })

    mockSupabaseClient.from().select().eq().single.mockResolvedValueOnce({
      data: mockTeamData,
      error: null,
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Loaded')
    })

    expect(screen.getByTestId('user-email')).toHaveTextContent('test@bali.love')
    expect(screen.getByTestId('authorized')).toHaveTextContent('Authorized')
    expect(screen.getByTestId('team-role')).toHaveTextContent('admin')
  })

  it('should reject user with unauthorized domain', async () => {
    const mockUser = createMockUser({ email: 'test@unauthorized.com' })

    mockSupabaseClient.auth.getUser.mockResolvedValueOnce({
      data: { user: mockUser },
      error: null,
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Loaded')
    })

    expect(screen.getByTestId('user-email')).toHaveTextContent('No user')
    expect(screen.getByTestId('authorized')).toHaveTextContent('Unauthorized')
    expect(mockSupabaseClient.auth.signOut).toHaveBeenCalled()
  })

  it('should handle auth state changes', async () => {
    let authChangeCallback: any

    mockSupabaseClient.auth.onAuthStateChange.mockImplementation((callback) => {
      authChangeCallback = callback
      return {
        data: { subscription: { unsubscribe: jest.fn() } },
      }
    })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    // Simulate auth state change to signed in
    const mockUser = createMockUser({ email: 'test@bali.love' })
    const mockTeamData = createMockUserTeamData()

    mockSupabaseClient.from().select().eq().single.mockResolvedValueOnce({
      data: mockTeamData,
      error: null,
    })

    await act(async () => {
      authChangeCallback('SIGNED_IN', { user: mockUser })
    })

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@bali.love')
    })

    // Simulate sign out
    await act(async () => {
      authChangeCallback('SIGNED_OUT', { user: null })
    })

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('No user')
    })
  })

  it('should handle sign out', async () => {
    const mockUser = createMockUser({ email: 'test@bali.love' })
    const mockTeamData = createMockUserTeamData()

    mockSupabaseClient.auth.getUser.mockResolvedValueOnce({
      data: { user: mockUser },
      error: null,
    })

    mockSupabaseClient.from().select().eq().single.mockResolvedValueOnce({
      data: mockTeamData,
      error: null,
    })

    mockSupabaseClient.auth.signOut.mockResolvedValueOnce({ error: null })

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@bali.love')
    })

    const signOutButton = screen.getByText('Sign Out')
    await act(async () => {
      signOutButton.click()
    })

    await waitFor(() => {
      expect(mockSupabaseClient.auth.signOut).toHaveBeenCalled()
    })
  })

  it('should handle errors when fetching user team data', async () => {
    const mockUser = createMockUser({ email: 'test@bali.love' })

    mockSupabaseClient.auth.getUser.mockResolvedValueOnce({
      data: { user: mockUser },
      error: null,
    })

    mockSupabaseClient.from().select().eq().single.mockResolvedValueOnce({
      data: null,
      error: { message: 'User team data not found' },
    })

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Loaded')
    })

    expect(screen.getByTestId('user-email')).toHaveTextContent('test@bali.love')
    expect(screen.getByTestId('team-role')).toHaveTextContent('No role')
    expect(consoleSpy).toHaveBeenCalledWith(
      'Error fetching user team data:',
      expect.any(Error)
    )

    consoleSpy.mockRestore()
  })

  it('should handle missing supabase client gracefully', async () => {
    // Mock createClient to throw an error
    jest.doMock('@/lib/supabase', () => ({
      createClient: jest.fn(() => {
        throw new Error('Failed to initialize')
      }),
    }))

    const { AuthProvider: AuthProviderWithError } = await import('../AuthContext')

    render(
      <AuthProviderWithError>
        <TestComponent />
      </AuthProviderWithError>
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Loaded')
    })

    expect(screen.getByTestId('user-email')).toHaveTextContent('No user')
    expect(screen.getByTestId('authorized')).toHaveTextContent('Unauthorized')
  })

  it('should throw error when useAuth is used outside provider', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

    expect(() => render(<TestComponent />)).toThrow(
      'useAuth must be used within an AuthProvider'
    )

    consoleSpy.mockRestore()
  })
})