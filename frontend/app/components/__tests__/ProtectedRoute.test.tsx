import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import ProtectedRoute from '../ProtectedRoute'
import { useAuth } from '@/app/contexts/AuthContextStable'

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

jest.mock('@/app/contexts/AuthContextStable', () => ({
  useAuth: jest.fn(),
}))

describe('ProtectedRoute', () => {
  const mockPush = jest.fn()
  const mockRouter = { push: mockPush }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    // Mock console.log to avoid test output noise
    jest.spyOn(console, 'log').mockImplementation()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('should show loading state when authentication is loading', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: null,
      loading: true,
      isAuthorized: false,
    })

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByText('Loading authentication...')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('should render children when user is authenticated and authorized', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: { email: 'test@bali.love', id: 'user-123' },
      loading: false,
      isAuthorized: true,
    })

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    expect(screen.queryByText('Loading authentication...')).not.toBeInTheDocument()
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('should redirect to login when user is not authenticated', async () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: null,
      loading: false,
      isAuthorized: false,
    })

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('should redirect to login when user is authenticated but not authorized', async () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: { email: 'test@unauthorized.com', id: 'user-123' },
      loading: false,
      isAuthorized: false,
    })

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('should not redirect while loading', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: null,
      loading: true,
      isAuthorized: false,
    })

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    expect(mockPush).not.toHaveBeenCalled()
  })

  it('should handle auth state changes', async () => {
    const { rerender } = render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    // Initially loading
    ;(useAuth as jest.Mock).mockReturnValue({
      user: null,
      loading: true,
      isAuthorized: false,
    })

    rerender(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByText('Loading authentication...')).toBeInTheDocument()

    // Then authenticated
    ;(useAuth as jest.Mock).mockReturnValue({
      user: { email: 'test@bali.love', id: 'user-123' },
      loading: false,
      isAuthorized: true,
    })

    rerender(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })

    // Then logged out
    ;(useAuth as jest.Mock).mockReturnValue({
      user: null,
      loading: false,
      isAuthorized: false,
    })

    rerender(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })
})