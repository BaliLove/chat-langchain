import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseAnonKey) {
    console.error('Missing Supabase environment variables')
    console.log('NEXT_PUBLIC_SUPABASE_URL:', supabaseUrl || 'NOT SET')
    console.log('NEXT_PUBLIC_SUPABASE_ANON_KEY:', supabaseAnonKey ? 'SET' : 'NOT SET')
    
    // Return a mock client that will fail gracefully
    throw new Error('Supabase client cannot be initialized without proper environment variables')
  }

  return createBrowserClient(
    supabaseUrl,
    supabaseAnonKey,
    {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        storage: typeof window !== 'undefined' ? window.localStorage : undefined,
      }
    }
  )
}