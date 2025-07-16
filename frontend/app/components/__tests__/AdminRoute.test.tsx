import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import AdminRoute from '../AdminRoute'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { usePermissions } from '@/app/hooks/usePermissions'

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

jest.mock('@/app/contexts/AuthContextStable', () => ({
  useAuth: jest.fn(),
}))

jest.mock('@/app/hooks/usePermissions', () => ({
  usePermissions: jest.fn(),
}))

describe('AdminRoute', () => {
  const mockPush = jest.fn()
  const mockRouter = { push: mockPush }

  const defaultAuthState = {
    user: { email: 'admin@bali.love', id: 'admin-123' },
    userTeamData: { role: 'admin' },
    loading: false,
  }

  const defaultPermissionsState = {
    permissions: { canManageTeam: true },
    loading: false,
  }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
  })

  it('should show loading state when authentication is loading', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      ...defaultAuthState,
      loading: true,
    })
    ;(usePermissions as jest.Mock).mockReturnValue(defaultPermissionsState)

    render(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
  })

  it('should show loading state when permissions are loading', () => {
    ;(useAuth as jest.Mock).mockReturnValue(defaultAuthState)
    ;(usePermissions as jest.Mock).mockReturnValue({
      ...defaultPermissionsState,
      loading: true,
    })

    render(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
  })

  it('should render children when user is admin', () => {
    ;(useAuth as jest.Mock).mockReturnValue(defaultAuthState)
    ;(usePermissions as jest.Mock).mockReturnValue(defaultPermissionsState)

    render(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    expect(screen.getByTestId('admin-content')).toBeInTheDocument()
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('should redirect to home when user is not authenticated', async () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: null,
      userTeamData: null,
      loading: false,
    })
    ;(usePermissions as jest.Mock).mockReturnValue(defaultPermissionsState)

    render(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })

    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
  })

  it('should redirect to home when user is not admin', async () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      ...defaultAuthState,
      userTeamData: { role: 'member' },
    })
    ;(usePermissions as jest.Mock).mockReturnValue(defaultPermissionsState)

    render(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })

    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
  })

  it('should redirect to home when user is manager', async () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      ...defaultAuthState,
      userTeamData: { role: 'manager' },
    })
    ;(usePermissions as jest.Mock).mockReturnValue(defaultPermissionsState)

    render(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })

    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
  })

  it('should handle auth state changes', async () => {
    const { rerender } = render(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    // Initially loading
    ;(useAuth as jest.Mock).mockReturnValue({
      ...defaultAuthState,
      loading: true,
    })
    ;(usePermissions as jest.Mock).mockReturnValue(defaultPermissionsState)

    rerender(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()

    // Then authenticated as admin
    ;(useAuth as jest.Mock).mockReturnValue(defaultAuthState)

    rerender(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    await waitFor(() => {
      expect(screen.getByTestId('admin-content')).toBeInTheDocument()
    })

    // Then role changed to member
    ;(useAuth as jest.Mock).mockReturnValue({
      ...defaultAuthState,
      userTeamData: { role: 'member' },
    })

    rerender(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })

  it('should handle missing userTeamData', async () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: { email: 'admin@bali.love', id: 'admin-123' },
      userTeamData: null,
      loading: false,
    })
    ;(usePermissions as jest.Mock).mockReturnValue(defaultPermissionsState)

    render(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })

    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
  })

  it('should not redirect during loading states', () => {
    // Auth loading
    ;(useAuth as jest.Mock).mockReturnValue({
      user: null,
      userTeamData: null,
      loading: true,
    })
    ;(usePermissions as jest.Mock).mockReturnValue(defaultPermissionsState)

    render(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    expect(mockPush).not.toHaveBeenCalled()

    // Permissions loading
    ;(useAuth as jest.Mock).mockReturnValue(defaultAuthState)
    ;(usePermissions as jest.Mock).mockReturnValue({
      ...defaultPermissionsState,
      loading: true,
    })

    render(
      <AdminRoute>
        <div data-testid="admin-content">Admin Content</div>
      </AdminRoute>
    )

    expect(mockPush).not.toHaveBeenCalled()
  })
})