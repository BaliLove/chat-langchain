'use client'
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, Session, AuthChangeEvent } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase'

interface UserProfile {
  id: string
  email: string
  name?: string
  role: 'admin' | 'moderator' | 'user'
}

interface AuthContextType {
  user: User | null
  profile: UserProfile | null
  loading: boolean
  isAuthorized: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Configure allowed email domains for your organization
const ALLOWED_EMAIL_DOMAINS = process.env.NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS?.split(',') || ['example.com']

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [isAuthorized, setIsAuthorized] = useState(false)
  const supabase = createClient()

  const checkUserAuthorization = (user: User): boolean => {
    if (!user.email) return false
    
    // Check if user's email domain is allowed
    const emailDomain = user.email.split('@')[1]
    return ALLOWED_EMAIL_DOMAINS.includes(emailDomain)
  }

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }: { data: { session: Session | null } }) => {
      setUser(session?.user ?? null)
      if (session?.user) {
        const authorized = checkUserAuthorization(session.user)
        setIsAuthorized(authorized)
        
        if (authorized) {
          loadUserProfile(session.user.id)
        } else {
          // Sign out unauthorized users
          supabase.auth.signOut()
          setLoading(false)
        }
      } else {
        setLoading(false)
      }
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event: AuthChangeEvent, session: Session | null) => {
        setUser(session?.user ?? null)
        if (session?.user) {
          // Check if user is authorized
          const authorized = checkUserAuthorization(session.user)
          setIsAuthorized(authorized)
          
          if (authorized) {
            await loadUserProfile(session.user.id)
          } else {
            // Sign out unauthorized users
            await supabase.auth.signOut()
            setProfile(null)
          }
        } else {
          setProfile(null)
          setIsAuthorized(false)
          setLoading(false)
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const loadUserProfile = async (userId: string) => {
    try {
      const { data, error } = await supabase
        .from('user_profiles')
        .select('*')
        .eq('id', userId)
        .single()

      if (error) throw error
      setProfile(data)
    } catch (error) {
      console.error('Error loading user profile:', error)
      // If no profile exists yet, create a basic one
      setProfile({
        id: userId,
        email: user?.email || '',
        role: 'user'
      })
    } finally {
      setLoading(false)
    }
  }

  const signOut = async () => {
    await supabase.auth.signOut()
  }

  return (
    <AuthContext.Provider value={{
      user,
      profile,
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