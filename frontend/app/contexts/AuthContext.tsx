'use client'
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, Session, AuthChangeEvent } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase'

interface AuthContextType {
  user: User | null
  loading: boolean
  isAuthorized: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Configure allowed email domains for your organization
const ALLOWED_EMAIL_DOMAINS = process.env.NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS?.split(',') || ['example.com']

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
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
        
        if (!authorized) {
          // Sign out unauthorized users
          supabase.auth.signOut()
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
          }
        } else {
          setIsAuthorized(false)
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