import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase'
import { headers } from 'next/headers'

export async function POST(request: NextRequest) {
  try {
    // Get authorization header
    const headersList = headers()
    const authorization = headersList.get('authorization')
    
    if (!authorization?.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Verify the user is admin using their token
    const token = authorization.replace('Bearer ', '')
    const supabase = createClient()
    
    // Get user from token
    const { data: { user }, error: userError } = await supabase.auth.getUser(token)
    
    if (userError || !user) {
      return NextResponse.json({ error: 'Invalid token' }, { status: 401 })
    }

    // Check if user is admin
    const { data: userData, error: permError } = await supabase
      .from('user_teams')
      .select('role')
      .eq('email', user.email)
      .single()

    if (permError || userData?.role !== 'admin') {
      return NextResponse.json({ error: 'Admin access required' }, { status: 403 })
    }

    // Execute the sync script
    // In production, you might want to trigger this as a background job
    const response = await fetch(`${process.env.INTERNAL_API_URL || 'http://localhost:8000'}/admin/sync-bubble`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.INTERNAL_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ triggered_by: user.email })
    })

    if (!response.ok) {
      throw new Error('Sync failed')
    }

    const result = await response.json()

    return NextResponse.json({
      success: true,
      message: 'Sync completed',
      stats: result.stats
    })

  } catch (error) {
    console.error('Error in sync-permissions:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}