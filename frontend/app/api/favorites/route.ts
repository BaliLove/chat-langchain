import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@/lib/supabase'

export async function GET(request: NextRequest) {
  try {
    const supabase = createServerClient()
    
    // Get authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ success: false, error: 'Not authenticated' }, { status: 401 })
    }

    // Get user's favorites
    const { data: favorites, error } = await supabase
      .from('favorites')
      .select('prompt_id, created_at')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Error fetching favorites:', error)
      return NextResponse.json({ success: false, error: error.message }, { status: 500 })
    }

    return NextResponse.json({ 
      success: true, 
      favorites: favorites || [],
      count: favorites?.length || 0
    })
  } catch (error) {
    console.error('Error in GET /api/favorites:', error)
    return NextResponse.json({ success: false, error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const supabase = createServerClient()
    const body = await request.json()
    const { promptId } = body

    if (!promptId) {
      return NextResponse.json({ success: false, error: 'Prompt ID required' }, { status: 400 })
    }

    // Get authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ success: false, error: 'Not authenticated' }, { status: 401 })
    }

    // Toggle favorite using the database function
    const { data, error } = await supabase
      .rpc('toggle_favorite', { p_prompt_id: promptId })

    if (error) {
      console.error('Error toggling favorite:', error)
      return NextResponse.json({ success: false, error: error.message }, { status: 500 })
    }

    return NextResponse.json({ 
      success: true, 
      isFavorite: data,
      message: data ? 'Added to favorites' : 'Removed from favorites'
    })
  } catch (error) {
    console.error('Error in POST /api/favorites:', error)
    return NextResponse.json({ success: false, error: 'Internal server error' }, { status: 500 })
  }
}