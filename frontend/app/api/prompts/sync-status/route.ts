import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
const supabase = createClient(supabaseUrl, supabaseAnonKey)

export async function GET() {
  try {
    // Get the latest sync status
    const { data: syncStatus, error } = await supabase
      .from('prompt_sync_status')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(1)
      .single()
    
    if (error) {
      console.error('Failed to fetch sync status:', error)
      if (error.code === '42P01') { // Table doesn't exist
        return NextResponse.json({
          success: true,
          syncStatus: {
            last_sync_at: null,
            sync_status: 'tables_not_created',
            prompts_synced: 0,
            error_message: 'Database tables not yet created. Please run the migration.'
          }
        })
      }
      if (error.code !== 'PGRST116') { // PGRST116 = no rows returned
        return NextResponse.json({
          success: false,
          error: 'Failed to fetch sync status'
        }, { status: 500 })
      }
    }
    
    return NextResponse.json({
      success: true,
      syncStatus: syncStatus || {
        last_sync_at: null,
        sync_status: 'never',
        prompts_synced: 0
      }
    })
  } catch (error) {
    console.error('Failed to fetch sync status:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to fetch sync status'
    }, { status: 500 })
  }
}