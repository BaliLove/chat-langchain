import { createClient } from '@supabase/supabase-js'

export const mockSupabaseClient = {
  auth: {
    getUser: jest.fn().mockResolvedValue({ data: { user: null }, error: null }),
    getSession: jest.fn().mockResolvedValue({ data: { session: null }, error: null }),
    signInWithEmail: jest.fn(),
    signOut: jest.fn().mockResolvedValue({ error: null }),
    onAuthStateChange: jest.fn().mockReturnValue({
      data: { subscription: { unsubscribe: jest.fn() } },
    }),
  },
  from: jest.fn().mockReturnValue({
    select: jest.fn().mockReturnValue({
      eq: jest.fn().mockReturnValue({
        single: jest.fn().mockResolvedValue({ data: null, error: null }),
        maybeSingle: jest.fn().mockResolvedValue({ data: null, error: null }),
      }),
      order: jest.fn().mockReturnValue({
        limit: jest.fn().mockResolvedValue({ data: [], error: null }),
      }),
    }),
    insert: jest.fn().mockResolvedValue({ data: null, error: null }),
    update: jest.fn().mockReturnValue({
      eq: jest.fn().mockResolvedValue({ data: null, error: null }),
    }),
    delete: jest.fn().mockReturnValue({
      eq: jest.fn().mockResolvedValue({ data: null, error: null }),
    }),
  }),
}

// Mock the createClient function
jest.mock('@/lib/supabase', () => ({
  createClient: jest.fn(() => mockSupabaseClient),
}))

// Mock for edge runtime compatibility
jest.mock('@supabase/ssr', () => ({
  createBrowserClient: jest.fn(() => mockSupabaseClient),
}))

export const resetSupabaseMocks = () => {
  Object.values(mockSupabaseClient.auth).forEach((mockFn: any) => {
    if (mockFn.mockClear) mockFn.mockClear()
  })
  
  // Reset from() chain
  const fromMock = mockSupabaseClient.from() as any
  const selectMock = fromMock.select()
  const eqMock = selectMock.eq()
  
  ;[fromMock, selectMock, eqMock, eqMock.single, eqMock.maybeSingle].forEach((mock: any) => {
    if (mock && mock.mockClear) mock.mockClear()
  })
}