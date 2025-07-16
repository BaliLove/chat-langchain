import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Force route to be dynamic (not cached)
export const dynamic = 'force-dynamic'

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
const supabase = createClient(supabaseUrl, supabaseAnonKey)

export async function GET() {
  try {
    console.log('Fetching prompts from Supabase...')
    console.log('Supabase URL:', supabaseUrl)
    
    // Fetch only active prompts from Supabase
    const { data: prompts, error } = await supabase
      .from('prompts')
      .select('*')
      .eq('is_active', true)
      .order('name')
    
    console.log('Query result:', { data: prompts?.length, error })
    
    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json({
        prompts: [],
        success: false,
        error: error.message
      })
    }
    
    // Parse context_tags for each prompt if needed
    const formattedPrompts = (prompts || []).map(prompt => {
      if (typeof prompt.context_tags === 'string') {
        try {
          prompt.context_tags = JSON.parse(prompt.context_tags)
        } catch (e) {
          prompt.context_tags = {}
        }
      }
      return {
        ...prompt,
        usage: prompt.usage_count || 0,
        lastUpdated: prompt.last_updated || prompt.updated_at
      }
    })
    
    return NextResponse.json({
      prompts: formattedPrompts,
      success: true
    })
  } catch (error) {
    console.error('Failed to fetch prompts:', error)
    return NextResponse.json(
      { error: 'Failed to fetch prompts', success: false },
      { status: 500 }
    )
  }
}