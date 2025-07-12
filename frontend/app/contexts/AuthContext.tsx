'use client'
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

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

  const checkUserAuthorization = (email: string): boolean => {
    if (!email) return false
    
    // Check if user's email domain is allowed
    const emailDomain = email.split('@')[1]
    return ALLOWED_EMAIL_DOMAINS.includes(emailDomain)
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
    // Simple organization-based authentication
    // In a real implementation, you'd integrate with your existing auth system
    
    // For now, we'll use a simple approach that works for your organization
    const initializeAuth = async () => {
      try {
        // Check if user is already logged in (you can adapt this to your auth system)
        const currentUser = localStorage.getItem('bali_love_user')
        
        if (currentUser) {
          const userData = JSON.parse(currentUser)
          const authorized = checkUserAuthorization(userData.email)
          
          if (authorized) {
            setUser(userData)
            setIsAuthorized(true)
            setUserTeamData(createMockUserTeamData(userData.email))
          } else {
            // Clear unauthorized user
            localStorage.removeItem('bali_love_user')
          }
        } else {
          // For demo purposes, create a default user
          // In production, you'd redirect to login or use your auth system
          const defaultUser = {
            email: 'tom@bali.love',
            id: 'default-user-id'
          }
          
          setUser(defaultUser)
          setIsAuthorized(true)
          setUserTeamData(createMockUserTeamData(defaultUser.email))
          localStorage.setItem('bali_love_user', JSON.stringify(defaultUser))
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        // Fallback to unauthorized state
        setIsAuthorized(false)
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const signOut = async () => {
    localStorage.removeItem('bali_love_user')
    setUser(null)
    setUserTeamData(null)
    setIsAuthorized(false)
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