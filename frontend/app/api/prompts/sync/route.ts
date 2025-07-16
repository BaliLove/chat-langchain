import { NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

export async function POST() {
  try {
    // Get the backend directory path
    const backendPath = path.join(process.cwd(), '..', 'backend')
    
    // Run the sync script
    const syncProcess = spawn('python', ['sync_prompts_simple.py'], {
      cwd: backendPath,
      stdio: 'pipe'
    })
    
    let output = ''
    let error = ''
    
    // Collect output and errors
    syncProcess.stdout.on('data', (data) => {
      output += data.toString()
    })
    
    syncProcess.stderr.on('data', (data) => {
      error += data.toString()
    })
    
    // Wait for the process to complete
    const exitCode = await new Promise<number>((resolve) => {
      syncProcess.on('close', (code) => {
        resolve(code || 0)
      })
    })
    
    if (exitCode === 0) {
      // Parse the output to extract sync results
      const lines = output.split('\n')
      const completedLine = lines.find(line => line.includes('Sync completed:'))
      let syncResult = null
      
      if (completedLine) {
        try {
          const resultMatch = completedLine.match(/Sync completed: (.+)/)
          if (resultMatch) {
            syncResult = JSON.parse(resultMatch[1].replace(/'/g, '"'))
          }
        } catch (e) {
          console.error('Failed to parse sync result:', e)
        }
      }
      
      return NextResponse.json({
        success: true,
        message: 'Sync completed successfully',
        result: syncResult,
        output: output
      })
    } else {
      return NextResponse.json({
        success: false,
        message: 'Sync failed',
        error: error,
        output: output
      }, { status: 500 })
    }
    
  } catch (error) {
    console.error('Failed to trigger sync:', error)
    return NextResponse.json({
      success: false,
      message: 'Failed to trigger sync',
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}