'use client'
import { createContext, useContext, useEffect, useState, ReactNode, useRef } from 'react'
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

// Helper to get cached auth state
const getCachedAuthState = () => {
  if (typeof window === 'undefined') return null
  try {
    const cached = sessionStorage.getItem('auth_state')
    if (cached) {
      const parsed = JSON.parse(cached)
      // Check if cache is still valid (24 hours)
      if (Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000) {
        return parsed
      }
    }
  } catch (e) {
    console.error('Error reading cached auth state:', e)
  }
  return null
}

// Helper to cache auth state
const setCachedAuthState = (user: { email: string; id: string } | null, userTeamData: UserTeamData | null, isAuthorized: boolean) => {
  if (typeof window === 'undefined') return
  try {
    sessionStorage.setItem('auth_state', JSON.stringify({
      user,
      userTeamData,
      isAuthorized,
      timestamp: Date.now()
    }))
  } catch (e) {
    console.error('Error caching auth state:', e)
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  // Initialize from cache if available
  const cachedState = getCachedAuthState()
  const [user, setUser] = useState<{ email: string; id: string } | null>(cachedState?.user || null)
  const [userTeamData, setUserTeamData] = useState<UserTeamData | null>(cachedState?.userTeamData || null)
  const [loading, setLoading] = useState(!cachedState) // Only load if no cache
  const [isAuthorized, setIsAuthorized] = useState(cachedState?.isAuthorized || false)
  const initRef = useRef(false)
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
    const emailDomain = email.split('@')[1]
    return ALLOWED_EMAIL_DOMAINS.includes(emailDomain)
  }

  const createMockUserTeamData = (email: string): UserTeamData => {
    const emailPrefix = email.split('@')[0].toLowerCase()
    
    let team_name = 'Bali Love'
    let role = 'member'
    let allowed_agents = ['chat', 'search']
    let allowed_data_sources = ['public', 'company_wide']
    
    if (emailPrefix.includes('admin') || emailPrefix.includes('manager')) {
      role = 'admin'
      allowed_data_sources = ['public', 'company_wide', 'team_specific', 'department_specific']
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

  const fetchUserTeamData = async (email: string): Promise<UserTeamData | null> => {
    try {
      if (!supabase) {
        console.log('Supabase client not available, using mock data')
        return createMockUserTeamData(email)
      }

      const { data, error } = await supabase
        .from('user_teams')
        .select('*')
        .eq('email', email.toLowerCase())
        .single()

      if (error || !data) {
        console.log('User team data not found, using defaults')
        return createMockUserTeamData(email)
      }

      return data
    } catch (error) {
      console.error('Error fetching user team data:', error)
      return createMockUserTeamData(email)
    }
  }

  useEffect(() => {
    // Prevent multiple initializations
    if (initRef.current) return
    initRef.current = true

    // Add a timeout to ensure loading state is resolved
    const timeoutId = setTimeout(() => {
      if (loading) {
        console.error('⏱️ Auth initialization timeout - forcing loading to false')
        setLoading(false)
      }
    }, 10000) // 10 second hard timeout

    const initializeAuth = async () => {
      console.log('🔐 Initializing auth...')
      
      if (!supabase) {
        console.error('❌ Supabase client not available')
        setLoading(false)
        clearTimeout(timeoutId)
        return
      }

      try {
        // Get current session
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('❌ Session error:', error)
          throw error
        }

        if (session?.user) {
          console.log('✅ Found existing session')
          const email = session.user.email || ''
          const authorized = checkUserAuthorization(email)
          
          if (authorized) {
            const userData = { email, id: session.user.id }
            setUser(userData)
            setIsAuthorized(true)
            const teamData = await fetchUserTeamData(email)
            if (teamData) {
              setUserTeamData(teamData)
            }
            // Cache the auth state
            setCachedAuthState(userData, teamData, true)
          } else {
            console.log('❌ User not authorized for this domain')
            await supabase.auth.signOut()
            // Clear cache
            setCachedAuthState(null, null, false)
          }
        } else {
          console.log('ℹ️ No active session')
          // Clear cache if no session
          setCachedAuthState(null, null, false)
        }
      } catch (error) {
        console.error('❌ Auth initialization error:', error)
      } finally {
        setLoading(false)
        clearTimeout(timeoutId)
      }
    }

    // Initialize auth
    initializeAuth()

    // Listen for auth changes
    const authListener = supabase?.auth.onAuthStateChange(async (event, session) => {
      console.log('🔄 Auth state changed:', event)
      
      if (session) {
        const email = session.user.email || ''
        const authorized = checkUserAuthorization(email)
        
        if (authorized) {
          const userData = { email, id: session.user.id }
          setUser(userData)
          setIsAuthorized(true)
          const teamData = await fetchUserTeamData(email)
          if (teamData) {
            setUserTeamData(teamData)
          }
          // Cache the auth state
          setCachedAuthState(userData, teamData, true)
        } else {
          setUser(null)
          setUserTeamData(null)
          setIsAuthorized(false)
          await supabase?.auth.signOut()
          // Clear cache
          setCachedAuthState(null, null, false)
        }
      } else {
        // No session
        setUser(null)
        setUserTeamData(null)
        setIsAuthorized(false)
        // Clear cache
        setCachedAuthState(null, null, false)
      }
      
      setLoading(false)
    })

    return () => {
      clearTimeout(timeoutId)
      authListener?.data?.subscription?.unsubscribe()
    }
  }, []) // Empty deps, only run once

  const signOut = async () => {
    try {
      if (supabase) {
        await supabase.auth.signOut()
      }
      setUser(null)
      setUserTeamData(null)
      setIsAuthorized(false)
      // Clear cache
      setCachedAuthState(null, null, false)
      
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