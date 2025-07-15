'use client'
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { createClient } from '@/lib/supabase'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { User } from '@supabase/supabase-js'
import { useAuth } from '@/app/contexts/AuthContextStable'

// Force dynamic rendering to avoid window is not defined error
export const dynamic = 'force-dynamic'

// Get allowed domains from environment variable
const ALLOWED_DOMAINS = process.env.NEXT_PUBLIC_ALLOWED_EMAIL_DOMAINS?.split(',') || ['example.com']

export default function LoginPage() {
  const router = useRouter()
  const { isAuthorized } = useAuth()
  const [user, setUser] = useState<User | null>(null)
  const [redirectUrl, setRedirectUrl] = useState<string>('')
  const [authError, setAuthError] = useState<string | null>(null)
  const [supabase, setSupabase] = useState<ReturnType<typeof createClient> | null>(null)

  useEffect(() => {
    // Initialize Supabase client
    try {
      const client = createClient()
      setSupabase(client)
    } catch (error) {
      console.error('Failed to create Supabase client in login page:', error)
      setAuthError('Authentication service is not available. Please check your configuration.')
    }

    // Set redirect URL on client side
    if (typeof window !== 'undefined') {
      setRedirectUrl(`${window.location.origin}/`)
    }
  }, [])

  useEffect(() => {
    if (!supabase) return

    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      setUser(user)
      if (user) {
        if (isAuthorized) {
          router.push('/') // Redirect to home if already logged in and authorized
        } else {
          setAuthError(`Access restricted to ${ALLOWED_DOMAINS.join(', ')} email addresses only.`)
          await supabase.auth.signOut()
        }
      }
    }
    getUser()

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session?.user?.email) {
        const emailDomain = session.user.email.split('@')[1]
        if (!ALLOWED_DOMAINS.includes(emailDomain)) {
          setAuthError(`Access restricted to ${ALLOWED_DOMAINS.join(', ')} email addresses only.`)
          await supabase.auth.signOut()
        }
      }
    })

    return () => subscription.unsubscribe()
  }, [supabase, router, isAuthorized])

  if (user) {
    return <div>Redirecting...</div>
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to LoveGPT
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access restricted to authorized organization members
          </p>
          <p className="mt-1 text-center text-xs text-gray-500">
            Allowed domains: {ALLOWED_DOMAINS.join(', ')}
          </p>
        </div>
        {authError && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Authentication Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{authError}</p>
                </div>
              </div>
            </div>
          </div>
        )}
        <div className="mt-8 space-y-6">
          {supabase ? (
            <Auth
              supabaseClient={supabase}
              appearance={{ theme: ThemeSupa }}
              providers={[]}
              redirectTo={redirectUrl || '/'}
              showLinks={false}
              view="sign_in"
            />
          ) : (
            <div className="text-center text-red-600">
              Authentication service is unavailable. Please check your configuration.
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 