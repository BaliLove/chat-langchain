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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<{ email: string; id: string } | null>(null)
  const [userTeamData, setUserTeamData] = useState<UserTeamData | null>(null)
  const [loading, setLoading] = useState(true)
  const [isAuthorized, setIsAuthorized] = useState(false)
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

    const initializeAuth = async () => {
      console.log('🔐 Initializing auth...')
      
      if (!supabase) {
        console.error('❌ Supabase client not available')
        setLoading(false)
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
            setUser({ email, id: session.user.id })
            setIsAuthorized(true)
            const teamData = await fetchUserTeamData(email)
            if (teamData) {
              setUserTeamData(teamData)
            }
          } else {
            console.log('❌ User not authorized for this domain')
            await supabase.auth.signOut()
          }
        } else {
          console.log('ℹ️ No active session')
        }
      } catch (error) {
        console.error('❌ Auth initialization error:', error)
      } finally {
        setLoading(false)
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
          setUser({ email, id: session.user.id })
          setIsAuthorized(true)
          const teamData = await fetchUserTeamData(email)
          if (teamData) {
            setUserTeamData(teamData)
          }
        } else {
          setUser(null)
          setUserTeamData(null)
          setIsAuthorized(false)
          await supabase?.auth.signOut()
        }
      } else {
        // No session
        setUser(null)
        setUserTeamData(null)
        setIsAuthorized(false)
      }
      
      setLoading(false)
    })

    return () => {
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