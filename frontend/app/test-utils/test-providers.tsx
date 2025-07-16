import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthContext } from '@/app/contexts/AuthContext'
import { User } from '@supabase/supabase-js'

interface MockAuthContextValue {
  user: User | null
  userTeamData: any | null
  loading: boolean
  signIn: jest.Mock
  signOut: jest.Mock
  refreshUserTeamData: jest.Mock
}

export const createMockAuthContext = (overrides?: Partial<MockAuthContextValue>): MockAuthContextValue => ({
  user: null,
  userTeamData: null,
  loading: false,
  signIn: jest.fn(),
  signOut: jest.fn(),
  refreshUserTeamData: jest.fn(),
  ...overrides,
})

export const createMockUser = (overrides?: Partial<User>): User => ({
  id: 'test-user-id',
  aud: 'authenticated',
  role: 'authenticated',
  email: 'test@bali.love',
  email_confirmed_at: '2024-01-01T00:00:00.000Z',
  phone: '',
  confirmed_at: '2024-01-01T00:00:00.000Z',
  created_at: '2024-01-01T00:00:00.000Z',
  updated_at: '2024-01-01T00:00:00.000Z',
  app_metadata: {},
  user_metadata: {},
  ...overrides,
})

export const createMockUserTeamData = (overrides?: Partial<any>): any => ({
  id: 'team-id',
  email: 'test@bali.love',
  team_id: 'bali-love-team',
  team_name: 'Bali Love',
  role: 'member',
  allowed_agents: ['chat', 'search'],
  allowed_data_sources: ['public', 'company_wide'],
  created_at: '2024-01-01T00:00:00.000Z',
  ...overrides,
})

interface TestProvidersProps {
  children: React.ReactNode
  authValue?: MockAuthContextValue
  queryClient?: QueryClient
}

export const TestProviders: React.FC<TestProvidersProps> = ({ 
  children, 
  authValue,
  queryClient 
}) => {
  const testQueryClient = queryClient || new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  const mockAuthValue = authValue || createMockAuthContext()

  return (
    <QueryClientProvider client={testQueryClient}>
      <AuthContext.Provider value={mockAuthValue}>
        {children}
      </AuthContext.Provider>
    </QueryClientProvider>
  )
}

// Custom render function that includes providers
export { render as rtlRender } from '@testing-library/react'
export * from '@testing-library/react'

export const render = (ui: React.ReactElement, options?: any) => {
  const { authValue, queryClient, ...renderOptions } = options || {}
  
  const AllTheProviders = ({ children }: { children: React.ReactNode }) => (
    <TestProviders authValue={authValue} queryClient={queryClient}>
      {children}
    </TestProviders>
  )

  const rtl = require('@testing-library/react')
  return rtl.render(ui, { wrapper: AllTheProviders, ...renderOptions })
}