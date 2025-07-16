import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
const supabase = createClient(supabaseUrl, supabaseAnonKey)

export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const promptId = params.id
    const body = await request.json()
    const { team } = body
    
    // Increment usage count
    const { data: prompt, error: fetchError } = await supabase
      .from('prompts')
      .select('usage_count')
      .eq('id', promptId)
      .single()
    
    if (fetchError) {
      console.error('Failed to fetch prompt:', fetchError)
      return NextResponse.json({
        success: false,
        error: 'Failed to fetch prompt'
      }, { status: 500 })
    }
    
    const newCount = (prompt?.usage_count || 0) + 1
    
    // Update usage count
    const { error: updateError } = await supabase
      .from('prompts')
      .update({ 
        usage_count: newCount,
        updated_at: new Date().toISOString()
      })
      .eq('id', promptId)
    
    if (updateError) {
      console.error('Failed to update usage:', updateError)
      return NextResponse.json({
        success: false,
        error: 'Failed to update usage'
      }, { status: 500 })
    }
    
    // In the future, we could also:
    // - Log to prompt_analytics table with date and team
    // - Track response times
    // - Store examples of successful uses
    
    return NextResponse.json({
      success: true,
      usage_count: newCount
    })
  } catch (error) {
    console.error('Failed to track usage:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to track usage'
    }, { status: 500 })
  }
}