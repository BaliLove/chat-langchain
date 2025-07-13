import { renderHook, waitFor } from '@testing-library/react'
import { usePermissions } from '@/app/hooks/usePermissions'
import { createClient } from '@/lib/supabase'

// Mock Supabase
jest.mock('@/lib/supabase', () => ({
  createClient: jest.fn(),
}))

// Mock auth context
jest.mock('@/app/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}))

import { useAuth } from '@/app/contexts/AuthContext'

describe('usePermissions', () => {
  const mockSupabase = {
    auth: {
      getUser: jest.fn(),
    },
    from: jest.fn(() => ({
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      single: jest.fn(),
    })),
  }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(createClient as jest.Mock).mockReturnValue(mockSupabase)
  })

  it('should return null permissions when no user is authenticated', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: null,
      loading: false,
    })

    const { result } = renderHook(() => usePermissions())

    expect(result.current.permissions).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.hasAgent('any')).toBe(false)
    expect(result.current.hasDataSource('any')).toBe(false)
  })

  it('should fetch and return user permissions', async () => {
    const mockUser = { id: '123', email: 'test@bali.love' }
    const mockUserTeamData = {
      email: 'test@bali.love',
      team_name: 'general',
      role: 'member',
      allowed_agents: ['general', 'research'],
      allowed_data_sources: ['docs', 'api'],
    }

    ;(useAuth as jest.Mock).mockReturnValue({
      user: mockUser,
      userTeamData: mockUserTeamData,
      loading: false,
    })

    mockSupabase.from().single.mockResolvedValue({
      data: mockUserTeamData,
      error: null,
    })

    const { result } = renderHook(() => usePermissions())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.permissions).toEqual({
      teamName: 'general',
      role: 'member',
      allowedAgents: ['general', 'research'],
      allowedDataSources: ['docs', 'api'],
    })

    expect(result.current.hasAgent('general')).toBe(true)
    expect(result.current.hasAgent('admin')).toBe(false)
    expect(result.current.hasDataSource('docs')).toBe(true)
    expect(result.current.hasDataSource('internal')).toBe(false)
  })

  it('should handle errors gracefully', async () => {
    const mockUser = { id: '123', email: 'test@bali.love' }
    
    ;(useAuth as jest.Mock).mockReturnValue({
      user: mockUser,
      userTeamData: null,
      loading: false,
    })

    mockSupabase.from().single.mockResolvedValue({
      data: null,
      error: new Error('Database error'),
    })

    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

    const { result } = renderHook(() => usePermissions())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.permissions).toBeNull()
    expect(consoleSpy).toHaveBeenCalledWith(
      'Error fetching permissions:',
      expect.any(Error)
    )

    consoleSpy.mockRestore()
  })

  it('should use userTeamData from auth context when available', () => {
    const mockUserTeamData = {
      email: 'test@bali.love',
      team_name: 'admin',
      role: 'admin',
      allowed_agents: ['*'],
      allowed_data_sources: ['*'],
    }

    ;(useAuth as jest.Mock).mockReturnValue({
      user: { id: '123', email: 'test@bali.love' },
      userTeamData: mockUserTeamData,
      loading: false,
    })

    const { result } = renderHook(() => usePermissions())

    expect(result.current.loading).toBe(false)
    expect(result.current.permissions).toEqual({
      teamName: 'admin',
      role: 'admin',
      allowedAgents: ['*'],
      allowedDataSources: ['*'],
    })
    
    // Should not make additional database call
    expect(mockSupabase.from).not.toHaveBeenCalled()
  })
})