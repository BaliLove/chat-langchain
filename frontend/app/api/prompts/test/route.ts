import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    // Try with anon key first
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    
    const anonClient = createClient(supabaseUrl, supabaseAnonKey)
    
    const { data: anonData, error: anonError } = await anonClient
      .from('prompts')
      .select('id, name')
      .limit(1)
    
    // Check if service role key is available
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY
    let serviceData = null
    let serviceError = null
    
    if (serviceRoleKey) {
      const serviceClient = createClient(supabaseUrl, serviceRoleKey)
      const result = await serviceClient
        .from('prompts')
        .select('id, name')
        .limit(1)
      
      serviceData = result.data
      serviceError = result.error
    }
    
    return NextResponse.json({
      anonKey: {
        hasData: !!anonData && anonData.length > 0,
        count: anonData?.length || 0,
        error: anonError?.message || null
      },
      serviceKey: {
        available: !!serviceRoleKey,
        hasData: !!serviceData && serviceData.length > 0,
        count: serviceData?.length || 0,
        error: serviceError?.message || null
      },
      debug: {
        supabaseUrl,
        hasAnonKey: !!supabaseAnonKey,
        hasServiceKey: !!serviceRoleKey
      }
    })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}