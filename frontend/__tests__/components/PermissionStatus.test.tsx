import { render, screen } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import PermissionStatus from '@/app/components/PermissionStatus'
import { usePermissions } from '@/app/hooks/usePermissions'
import { AuthProvider } from '@/app/contexts/AuthContext'

// Mock the usePermissions hook
vi.mock('@/app/hooks/usePermissions')

describe('PermissionStatus', () => {
  const mockUsePermissions = vi.mocked(usePermissions)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should show loading state', () => {
    mockUsePermissions.mockReturnValue({
      permissions: null,
      loading: true,
      hasAgent: vi.fn(),
      hasDataSource: vi.fn(),
    })

    render(
      <AuthProvider>
        <PermissionStatus />
      </AuthProvider>
    )
    
    expect(screen.getByText('Loading permissions...')).toBeInTheDocument()
  })

  it('should display user permissions correctly', () => {
    mockUsePermissions.mockReturnValue({
      permissions: {
        teamName: 'Engineering',
        role: 'member',
        allowedAgents: ['general', 'research'],
        allowedDataSources: ['docs', 'api'],
      },
      loading: false,
      hasAgent: vi.fn(),
      hasDataSource: vi.fn(),
    })

    render(
      <AuthProvider>
        <PermissionStatus />
      </AuthProvider>
    )
    
    expect(screen.getByText(/Team: Engineering/)).toBeInTheDocument()
    expect(screen.getByText(/Role: member/)).toBeInTheDocument()
    expect(screen.getByText(/general/)).toBeInTheDocument()
    expect(screen.getByText(/research/)).toBeInTheDocument()
    expect(screen.getByText(/docs/)).toBeInTheDocument()
    expect(screen.getByText(/api/)).toBeInTheDocument()
  })

  it('should display admin permissions with wildcard', () => {
    mockUsePermissions.mockReturnValue({
      permissions: {
        teamName: 'Admin',
        role: 'admin',
        allowedAgents: ['*'],
        allowedDataSources: ['*'],
      },
      loading: false,
      hasAgent: vi.fn(),
      hasDataSource: vi.fn(),
    })

    render(
      <AuthProvider>
        <PermissionStatus />
      </AuthProvider>
    )
    
    expect(screen.getByText(/Team: Admin/)).toBeInTheDocument()
    expect(screen.getByText(/Role: admin/)).toBeInTheDocument()
    expect(screen.getByText('All Agents')).toBeInTheDocument()
    expect(screen.getByText('All Data Sources')).toBeInTheDocument()
  })

  it('should show no permissions message when user has none', () => {
    mockUsePermissions.mockReturnValue({
      permissions: {
        teamName: 'Guest',
        role: 'guest',
        allowedAgents: [],
        allowedDataSources: [],
      },
      loading: false,
      hasAgent: vi.fn(),
      hasDataSource: vi.fn(),
    })

    render(
      <AuthProvider>
        <PermissionStatus />
      </AuthProvider>
    )
    
    expect(screen.getByText(/No agents available/)).toBeInTheDocument()
    expect(screen.getByText(/No data sources available/)).toBeInTheDocument()
  })

  it('should handle null permissions gracefully', () => {
    mockUsePermissions.mockReturnValue({
      permissions: null,
      loading: false,
      hasAgent: vi.fn(() => false),
      hasDataSource: vi.fn(() => false),
    })

    render(
      <AuthProvider>
        <PermissionStatus />
      </AuthProvider>
    )
    
    expect(screen.getByText(/No permissions found/)).toBeInTheDocument()
  })
})