# Authentication Implementation Guide: Supabase Auth + Bubble.io User Import

## 🎯 Overview

This guide implements Supabase Auth for your Next.js app with user import from Bubble.io and a basic permissions system for 100 users.

**Chosen Solution: Supabase Auth**
- ✅ FREE for up to 50,000 users 
- ✅ Already integrated with your Supabase database
- ✅ Simple Next.js setup
- ✅ User import capabilities
- ✅ Built-in permissions system

---

## 🚀 Phase 1: Supabase Auth Setup (1-2 days)

### Step 1: Install Dependencies

```bash
npm install @supabase/supabase-js @supabase/auth-helpers-nextjs @supabase/auth-ui-react @supabase/auth-ui-shared
```

### Step 2: Environment Variables

Add to your `.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Step 3: Create Supabase Client

```typescript
// lib/supabase.ts
import { createServerComponentClient, createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'

export const createServerSupabaseClient = () => {
  return createServerComponentClient({ cookies })
}

export const createClientSupabaseClient = () => {
  return createClientComponentClient()
}
```

### Step 4: Auth Middleware

```typescript
// middleware.ts
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(req: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })
  const { data: { session } } = await supabase.auth.getSession()

  // Redirect to login if not authenticated and trying to access protected routes
  if (!session && req.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  return res
}

export const config = {
  matcher: ['/dashboard/:path*', '/admin/:path*']
}
```

---

## 🔐 Phase 2: User Import from Bubble.io (2-3 days)

### Step 1: Bubble.io Data Export Script

```typescript
// scripts/import-bubble-users.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

interface BubbleUser {
  email: string
  name?: string
  created_date: string
  // Add other Bubble.io user fields
}

async function fetchBubbleUsers(): Promise<BubbleUser[]> {
  // Using Bubble.io Data API
  const response = await fetch('https://app.bali.love/api/1.1/obj/user', {
    headers: {
      'Authorization': `Bearer ${process.env.BUBBLE_API_TOKEN}`,
      'Content-Type': 'application/json'
    }
  })
  
  const data = await response.json()
  return data.response.results
}

async function importUsers() {
  try {
    console.log('🔄 Fetching users from Bubble.io...')
    const bubbleUsers = await fetchBubbleUsers()
    
    console.log(`📊 Found ${bubbleUsers.length} users to import`)

    for (const user of bubbleUsers) {
      try {
        // Create auth user in Supabase
        const { data: authUser, error: authError } = await supabase.auth.admin.createUser({
          email: user.email,
          email_confirm: true,
          user_metadata: {
            name: user.name,
            imported_from: 'bubble',
            bubble_created_date: user.created_date
          }
        })

        if (authError) {
          console.error(`❌ Failed to create auth user for ${user.email}:`, authError)
          continue
        }

        // Create user profile in your database
        const { error: profileError } = await supabase
          .from('user_profiles')
          .insert({
            id: authUser.user.id,
            email: user.email,
            name: user.name,
            role: 'user', // Default role
            imported_from: 'bubble',
            created_at: user.created_date
          })

        if (profileError) {
          console.error(`❌ Failed to create profile for ${user.email}:`, profileError)
        } else {
          console.log(`✅ Imported user: ${user.email}`)
        }

      } catch (error) {
        console.error(`❌ Error importing user ${user.email}:`, error)
      }
    }

    console.log('✅ User import completed!')
  } catch (error) {
    console.error('❌ Import failed:', error)
  }
}

importUsers()
```

### Step 2: Database Schema for User Profiles

```sql
-- Run in Supabase SQL Editor
CREATE TABLE user_profiles (
  id UUID REFERENCES auth.users PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  role TEXT NOT NULL DEFAULT 'user',
  permissions TEXT[] DEFAULT '{}',
  imported_from TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies
CREATE POLICY "Users can read own profile" ON user_profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
  FOR UPDATE USING (auth.uid() = id);

-- Admin policies (you'll define admin role logic)
CREATE POLICY "Admins can read all profiles" ON user_profiles
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE id = auth.uid() AND role = 'admin'
    )
  );
```

---

## 🛡️ Phase 3: Basic Permissions System (2-3 days)

### Step 1: Role-Based Access Control

```typescript
// lib/permissions.ts
export type UserRole = 'admin' | 'moderator' | 'user'
export type Permission = 'read_all_chats' | 'moderate_content' | 'manage_users' | 'admin_access'

export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  admin: ['read_all_chats', 'moderate_content', 'manage_users', 'admin_access'],
  moderator: ['read_all_chats', 'moderate_content'],
  user: []
}

export function hasPermission(userRole: UserRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[userRole].includes(permission)
}

export function hasAnyPermission(userRole: UserRole, permissions: Permission[]): boolean {
  return permissions.some(permission => hasPermission(userRole, permission))
}
```

### Step 2: Auth Context Provider

```typescript
// contexts/AuthContext.tsx
'use client'
import { createContext, useContext, useEffect, useState } from 'react'
import { User } from '@supabase/supabase-js'
import { createClientSupabaseClient } from '@/lib/supabase'
import { UserRole, Permission, hasPermission } from '@/lib/permissions'

interface UserProfile {
  id: string
  email: string
  name?: string
  role: UserRole
  permissions: string[]
}

interface AuthContextType {
  user: User | null
  profile: UserProfile | null
  loading: boolean
  hasPermission: (permission: Permission) => boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const supabase = createClientSupabaseClient()

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      if (session?.user) {
        loadUserProfile(session.user.id)
      } else {
        setLoading(false)
      }
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setUser(session?.user ?? null)
        if (session?.user) {
          await loadUserProfile(session.user.id)
        } else {
          setProfile(null)
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
    } finally {
      setLoading(false)
    }
  }

  const checkPermission = (permission: Permission): boolean => {
    if (!profile) return false
    return hasPermission(profile.role, permission)
  }

  const signOut = async () => {
    await supabase.auth.signOut()
  }

  return (
    <AuthContext.Provider value={{
      user,
      profile,
      loading,
      hasPermission: checkPermission,
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
```

---

## 🎨 Phase 4: Auth UI Components (1-2 days)

### Step 1: Login Component

```typescript
// components/auth/LoginForm.tsx
'use client'
import { useState } from 'react'
import { createClientSupabaseClient } from '@/lib/supabase'
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'

export default function LoginForm() {
  const supabase = createClientSupabaseClient()

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-md">
      <h1 className="text-2xl font-bold text-center mb-6">Sign In</h1>
      <Auth
        supabaseClient={supabase}
        appearance={{ theme: ThemeSupa }}
        providers={['google']} // Optional: add OAuth providers
        redirectTo={`${window.location.origin}/dashboard`}
      />
    </div>
  )
}
```

### Step 2: Protected Route Component

```typescript
// components/auth/ProtectedRoute.tsx
import { useAuth } from '@/contexts/AuthContext'
import { Permission } from '@/lib/permissions'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredPermission?: Permission
  fallback?: React.ReactNode
}

export default function ProtectedRoute({ 
  children, 
  requiredPermission,
  fallback = <div>Access denied</div>
}: ProtectedRouteProps) {
  const { user, profile, loading, hasPermission } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  if (loading) {
    return <div>Loading...</div>
  }

  if (!user) {
    return null
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}
```

---

## 🔧 Phase 5: Integration with Existing App (1-2 days)

### Step 1: Update Your Layout

```typescript
// app/layout.tsx
import { AuthProvider } from '@/contexts/AuthContext'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
```

### Step 2: Update Chat Interface

```typescript
// app/components/ChatLangChain.tsx
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/auth/ProtectedRoute'

export default function ChatLangChain() {
  const { profile } = useAuth()

  return (
    <ProtectedRoute>
      <div className="chat-interface">
        <div className="user-info">
          Welcome, {profile?.name || profile?.email}!
          {profile?.role === 'admin' && (
            <span className="admin-badge">Admin</span>
          )}
        </div>
        {/* Your existing chat interface */}
      </div>
    </ProtectedRoute>
  )
}
```

---

## 📊 Implementation Timeline

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1** | 1-2 days | ✅ Supabase Auth setup, basic login/logout |
| **Phase 2** | 2-3 days | ✅ User import script, database schema |
| **Phase 3** | 2-3 days | ✅ Permissions system, RLS policies |
| **Phase 4** | 1-2 days | ✅ Auth UI components |
| **Phase 5** | 1-2 days | ✅ Integration with existing app |
| **Total** | **7-12 days** | 🎯 **Complete auth system with 100 users** |

---

## 🔒 Security Features

1. **Row Level Security (RLS)** - Database-level permissions
2. **JWT Tokens** - Secure session management  
3. **Role-based Access Control** - Granular permissions
4. **Email Verification** - Confirmed user accounts
5. **Password Requirements** - Configurable security rules

---

## 🚀 Next Steps After Implementation

1. **Set up admin dashboard** for user management
2. **Add more granular permissions** (per-feature access)
3. **Implement team/workspace concept** 
4. **Add audit logging** for admin actions
5. **Progressive enhancement** - add features from Dust analysis

This gives you a solid foundation that can scale from 100 to 10,000+ users without changing the core architecture! 