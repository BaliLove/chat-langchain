import { renderHook, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { usePermissions } from '@/app/hooks/usePermissions'
import { createClient } from '@/lib/supabase'

// Mock Supabase
vi.mock('@/lib/supabase', () => ({
  createClient: vi.fn(),
}))

// Mock auth context
vi.mock('@/app/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '@/app/contexts/AuthContext'

describe('usePermissions', () => {
  const mockSupabase = {
    auth: {
      getUser: vi.fn(),
    },
    from: vi.fn(() => ({
      select: vi.fn().mockReturnThis(),
      eq: vi.fn().mockReturnThis(),
      single: vi.fn(),
    })),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(createClient).mockReturnValue(mockSupabase)
  })

  it('should return null permissions when no user is authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
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

    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      userTeamData: mockUserTeamData,
      loading: false,
    })

    const { result } = renderHook(() => usePermissions())

    // Should use data from auth context immediately
    expect(result.current.loading).toBe(false)
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
    
    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      userTeamData: null,
      loading: false,
    })

    mockSupabase.from().single.mockResolvedValue({
      data: null,
      error: new Error('Database error'),
    })

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const { result } = renderHook(() => usePermissions())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.permissions).toBeNull()
    expect(consoleSpy).toHaveBeenCalledWith(
      'Error in permission fetch:',
      expect.any(TypeError)
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

    vi.mocked(useAuth).mockReturnValue({
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