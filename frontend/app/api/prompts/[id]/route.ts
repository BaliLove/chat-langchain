import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Force route to be dynamic (not cached)
export const dynamic = 'force-dynamic'

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
const supabase = createClient(supabaseUrl, supabaseAnonKey)

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const promptId = params.id
    console.log('Fetching prompt with ID:', promptId)
    
    // Fetch prompt from Supabase
    const { data: prompt, error } = await supabase
      .from('prompts')
      .select('*')
      .eq('id', promptId)
      .single()
    
    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json(
        { error: 'Prompt not found', success: false },
        { status: 404 }
      )
    }
    
    if (!prompt) {
      return NextResponse.json(
        { error: 'Prompt not found', success: false },
        { status: 404 }
      )
    }
    
    // Parse context_tags if it's a string
    if (typeof prompt.context_tags === 'string') {
      try {
        prompt.context_tags = JSON.parse(prompt.context_tags)
      } catch (e) {
        prompt.context_tags = {}
      }
    }
    
    // Add empty analytics for now (will be implemented later)
    const promptDetail = {
      ...prompt,
      analytics: {
        daily: [],
        byTeam: {},
        avgResponseTime: 0,
        successRate: 0
      },
      examples: [],
      versions: [
        { 
          version: prompt.version || 1, 
          date: prompt.created_at, 
          modifiedBy: prompt.last_modified_by || 'system', 
          changes: 'Initial version' 
        }
      ]
    }
    
    return NextResponse.json({
      prompt: promptDetail,
      success: true
    })
  } catch (error) {
    console.error('Failed to fetch prompt details:', error)
    return NextResponse.json(
      { error: 'Failed to fetch prompt details', success: false },
      { status: 500 }
    )
  }
}