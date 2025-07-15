'use client'
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { createClient } from '@/lib/supabase'
import { User } from '@supabase/supabase-js'

interface UserTeamData {
  email: string
  team_id: string
  team_name: string
  role: string
  allowed_agents: string[]
  allowed_data_sources: string[]
}

interface AuthContextType {
  user: { email: string; id: string } | null
  userTeamData: UserTeamData | null
  loading: boolean
  isAuthorized: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Configure allowed email domains for your organization
const ALLOWED_EMAIL_DOMAINS = process.env.NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS?.split(',') || ['bali.love']

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<{ email: string; id: string } | null>(null)
  const [userTeamData, setUserTeamData] = useState<UserTeamData | null>(null)
  const [loading, setLoading] = useState(true)
  const [isAuthorized, setIsAuthorized] = useState(false)
  const [supabase] = useState(() => {
    try {
      return createClient()
    } catch (error) {
      console.error('Failed to create Supabase client:', error)
      return null
    }
  })

  const checkUserAuthorization = (email: string): boolean => {
    if (!email) return false
    
    // Check if user's email domain is allowed
    const emailDomain = email.split('@')[1]
    return ALLOWED_EMAIL_DOMAINS.includes(emailDomain)
  }

  const fetchUserTeamData = async (email: string): Promise<UserTeamData | null> => {
    try {
      if (!supabase) {
        console.log('Supabase client not available, using mock data')
        return createMockUserTeamData(email)
      }

      // Try to fetch from user_teams table first
      const { data, error } = await supabase
        .from('user_teams')
        .select('*')
        .eq('email', email.toLowerCase())
        .single()

      if (error || !data) {
        // If not found, create mock data
        console.log('User team data not found, using defaults')
        return createMockUserTeamData(email)
      }

      return data
    } catch (error) {
      console.error('Error fetching user team data:', error)
      return createMockUserTeamData(email)
    }
  }

  const createMockUserTeamData = (email: string): UserTeamData => {
    // Simple team assignment based on email prefix
    const emailPrefix = email.split('@')[0].toLowerCase()
    
    let team_name = 'Bali Love'
    let role = 'member'
    let allowed_agents = ['chat', 'search']
    let allowed_data_sources = ['public', 'company_wide']
    
    // Simple team assignment logic
    if (emailPrefix.includes('admin') || emailPrefix.includes('manager')) {
      role = 'admin'
      allowed_data_sources = ['public', 'company_wide', 'team_specific', 'department_specific']
    } else if (emailPrefix.includes('hr')) {
      team_name = 'HR Team'
      allowed_data_sources = ['public', 'company_wide', 'hr_data']
    } else if (emailPrefix.includes('finance')) {
      team_name = 'Finance Team'
      allowed_data_sources = ['public', 'company_wide', 'finance_data']
    } else if (emailPrefix.includes('training')) {
      team_name = 'Training Team'
      allowed_data_sources = ['public', 'company_wide', 'training_data']
    }
    
    return {
      email: email.toLowerCase(),
      team_id: team_name.toLowerCase().replace(/\s+/g, '_'),
      team_name,
      role,
      allowed_agents,
      allowed_data_sources
    }
  }

  useEffect(() => {
    const initializeAuth = async () => {
      // Set a timeout to prevent infinite loading
      const timeoutId = setTimeout(() => {
        console.warn('Auth initialization timeout - setting loading to false')
        console.log('Supabase URL:', process.env.NEXT_PUBLIC_SUPABASE_URL ? 'Set' : 'Missing')
        console.log('Supabase Anon Key:', process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? 'Set' : 'Missing')
        
        // Force loading to false and clear user state if timeout occurs
        setLoading(false)
        setUser(null)
        setUserTeamData(null)
        setIsAuthorized(false)
      }, 5000) // 5 second timeout

      try {
        // Check if Supabase is configured
        if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
          console.error('Supabase environment variables are not configured')
          console.log('NEXT_PUBLIC_SUPABASE_URL:', process.env.NEXT_PUBLIC_SUPABASE_URL)
          console.log('NEXT_PUBLIC_SUPABASE_ANON_KEY:', process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? 'Set' : 'Missing')
          throw new Error('Missing Supabase configuration')
        }

        if (!supabase) {
          console.error('Supabase client is not initialized')
          throw new Error('Supabase client initialization failed')
        }

        // Get current session from Supabase
        const { data: { session }, error: sessionError } = await supabase.auth.getSession()
        
        if (sessionError) {
          console.error('Session error:', sessionError)
          throw sessionError
        }
        
        console.log('Session check:', session ? 'Session found' : 'No session')
        
        if (session?.user) {
          const email = session.user.email || ''
          const authorized = checkUserAuthorization(email)
          
          console.log('User email:', email)
          console.log('Authorized:', authorized)
          console.log('Allowed domains:', ALLOWED_EMAIL_DOMAINS)
          
          if (authorized) {
            setUser({ email, id: session.user.id })
            setIsAuthorized(true)
            
            // Fetch user team data
            const teamData = await fetchUserTeamData(email)
            if (teamData) {
              setUserTeamData(teamData)
            }
          } else {
            // Unauthorized domain
            console.log('User domain not authorized')
            setIsAuthorized(false)
            await supabase.auth.signOut()
          }
        } else {
          // No session - ensure clean state
          console.log('No active session found')
          setUser(null)
          setUserTeamData(null)
          setIsAuthorized(false)
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        setUser(null)
        setUserTeamData(null)
        setIsAuthorized(false)
      } finally {
        clearTimeout(timeoutId)
        setLoading(false)
      }
    }

    initializeAuth()

    // Listen for auth state changes
    const subscription = supabase?.auth.onAuthStateChange(async (event, session) => {
      console.log('Auth state change:', event)
      
      if (event === 'SIGNED_IN' && session) {
        const email = session.user.email || ''
        const authorized = checkUserAuthorization(email)
        
        if (authorized) {
          setUser({ email, id: session.user.id })
          setIsAuthorized(true)
          
          // Fetch user team data
          const teamData = await fetchUserTeamData(email)
          if (teamData) {
            setUserTeamData(teamData)
          }
        } else {
          setIsAuthorized(false)
          await supabase?.auth.signOut()
        }
      } else if (event === 'SIGNED_OUT') {
        setUser(null)
        setUserTeamData(null)
        setIsAuthorized(false)
      }
    })

    return () => {
      subscription?.data.subscription?.unsubscribe()
    }
  }, [])

  const signOut = async () => {
    try {
      if (supabase) {
        await supabase.auth.signOut()
      }
      setUser(null)
      setUserTeamData(null)
      setIsAuthorized(false)
      
      // Redirect to login page
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

  return (
    <AuthContext.Provider value={{
      user,
      userTeamData,
      loading,
      isAuthorized,
      signOut
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
} 