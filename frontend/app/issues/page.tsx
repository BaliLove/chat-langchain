'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import ProtectedRoute from '@/app/components/ProtectedRoute'
import IssueCategorySelector from '@/app/components/IssueCategorySelector'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { Alert, AlertDescription } from '@/app/components/ui/alert'
import { Button } from '@/app/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card'
import { ArrowLeft, AlertCircle } from 'lucide-react'

export default function IssuesPage() {
  const router = useRouter()
  const { userTeamData } = useAuth()
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedPeriod, setSelectedPeriod] = useState<string>('7')

  const handleCategorySelect = (category: string, period?: string) => {
    setSelectedCategory(category)
    if (period) {
      setSelectedPeriod(period)
    }
  }

  const handleStartReview = () => {
    // Navigate to chat with the specific issue review prompt
    const promptId = `bali-love-issue-${selectedCategory}-review`
    const context = {
      category: selectedCategory,
      period: selectedPeriod,
      owner: userTeamData?.email || 'all',
      team: userTeamData?.team_name || 'Unknown'
    }
    
    // Encode context as URL params
    const contextParams = new URLSearchParams({
      prompt: promptId,
      category: selectedCategory,
      period: selectedPeriod,
      context: JSON.stringify(context)
    }).toString()
    
    router.push(`/?${contextParams}`)
  }

  return (
    <ProtectedRoute>
      <div className="flex-1 overflow-y-auto">
        <div className="p-8 max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/agents')}
              className="mb-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Agents
            </Button>
            
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-3xl font-bold text-foreground">Issue Reviews</h1>
                <p className="text-muted-foreground mt-2">
                  Weekly category reviews for issue management
                </p>
              </div>
            </div>
          </div>

          {/* Info Alert */}
          <Alert className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Weekly Review Process:</strong> Select your category below to generate a comprehensive 
              review of all issues. This helps category owners stay on top of their responsibilities 
              and identify patterns or bottlenecks.
            </AlertDescription>
          </Alert>

          {/* Category Selector */}
          <IssueCategorySelector
            onCategorySelect={handleCategorySelect}
            onStartReview={handleStartReview}
          />

          {/* Additional Resources */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">How It Works</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>1. Select your issue category</p>
                <p>2. Choose the review period (default: last 7 days)</p>
                <p>3. Click &quot;Start Review&quot; to generate your report</p>
                <p>4. The AI will analyze all issues and provide actionable insights</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">What You&apos;ll Get</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>• Priority issues requiring immediate attention</p>
                <p>• Status summary with trends</p>
                <p>• Quick wins you can tackle today</p>
                <p>• Direct links to each issue in Bubble</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}