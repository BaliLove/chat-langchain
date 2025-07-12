'use client'
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, Session, AuthChangeEvent } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase'

interface UserTeamData {
  email: string
  team_id: string
  team_name: string
  role: string
  allowed_agents: string[]
  allowed_data_sources: string[]
}

interface AuthContextType {
  user: User | null
  userTeamData: UserTeamData | null
  loading: boolean
  isAuthorized: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Configure allowed email domains for your organization
const ALLOWED_EMAIL_DOMAINS = process.env.NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS?.split(',') || ['example.com']

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [userTeamData, setUserTeamData] = useState<UserTeamData | null>(null)
  const [loading, setLoading] = useState(true)
  const [isAuthorized, setIsAuthorized] = useState(false)
  const supabase = createClient()

  const checkUserAuthorization = (user: User): boolean => {
    if (!user.email) return false
    
    // Check if user's email domain is allowed
    const emailDomain = user.email.split('@')[1]
    return ALLOWED_EMAIL_DOMAINS.includes(emailDomain)
  }

  const fetchUserTeamData = async (email: string) => {
    try {
      const { data, error } = await supabase
        .from('user_teams')
        .select('*')
        .eq('email', email.toLowerCase())
        .single()
      
      if (error) {
        console.warn('No team data found for user:', email)
        return null
      }
      
      return data as UserTeamData
    } catch (error) {
      console.error('Error fetching user team data:', error)
      return null
    }
  }

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(async ({ data: { session } }: { data: { session: Session | null } }) => {
      setUser(session?.user ?? null)
      if (session?.user) {
        const authorized = checkUserAuthorization(session.user)
        setIsAuthorized(authorized)
        
        if (!authorized) {
          // Sign out unauthorized users
          supabase.auth.signOut()
        } else if (session.user.email) {
          // Fetch team data for authorized users
          const teamData = await fetchUserTeamData(session.user.email)
          setUserTeamData(teamData)
        }
      }
      setLoading(false)
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event: AuthChangeEvent, session: Session | null) => {
        setUser(session?.user ?? null)
        if (session?.user) {
          // Check if user is authorized
          const authorized = checkUserAuthorization(session.user)
          setIsAuthorized(authorized)
          
          if (!authorized) {
            // Sign out unauthorized users
            await supabase.auth.signOut()
            setUserTeamData(null)
          } else if (session.user.email) {
            // Fetch team data for authorized users
            const teamData = await fetchUserTeamData(session.user.email)
            setUserTeamData(teamData)
          }
        } else {
          setIsAuthorized(false)
          setUserTeamData(null)
        }
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const signOut = async () => {
    await supabase.auth.signOut()
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