'use client'

import { Button } from '@/app/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card'
import { 
  Briefcase, 
  Building, 
  Megaphone, 
  DollarSign, 
  Cpu, 
  HeadphonesIcon, 
  Users,
  ArrowRight
} from 'lucide-react'

interface PromptStartersProps {
  promptId: string
  onSelectOption: (option: string) => void
}

const ISSUE_CATEGORIES = [
  { 
    value: 'venue', 
    label: 'Venue', 
    icon: Building,
    description: 'Partner venues and locations',
    color: 'bg-purple-500'
  },
  { 
    value: 'operations', 
    label: 'Operations', 
    icon: Briefcase,
    description: 'Workflow and processes',
    color: 'bg-blue-500'
  },
  { 
    value: 'marketing', 
    label: 'Marketing', 
    icon: Megaphone,
    description: 'Campaigns and brand',
    color: 'bg-pink-500'
  },
  { 
    value: 'finance', 
    label: 'Finance', 
    icon: DollarSign,
    description: 'Payments and budgets',
    color: 'bg-green-500'
  },
  { 
    value: 'technology', 
    label: 'Technology', 
    icon: Cpu,
    description: 'Systems and tools',
    color: 'bg-indigo-500'
  },
  { 
    value: 'customer_service', 
    label: 'Customer Service', 
    icon: HeadphonesIcon,
    description: 'Guest experience',
    color: 'bg-yellow-500'
  }
]

export function PromptStarters({ promptId, onSelectOption }: PromptStartersProps) {
  // Only show for issue review prompt
  if (promptId !== 'bali-love-issue-review') {
    return null
  }

  return (
    <Card className="mb-4 shadow-sm">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg">Select a Category to Review</CardTitle>
        <CardDescription>
          Choose which issue category you'd like to review this week
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {ISSUE_CATEGORIES.map((category) => {
            const Icon = category.icon
            return (
              <Button
                key={category.value}
                variant="outline"
                className="h-auto flex flex-col items-center gap-2 p-4 hover:shadow-md transition-all"
                onClick={() => onSelectOption(`I'd like to review ${category.label.toLowerCase()} issues`)}
              >
                <div className={`p-2 rounded-lg ${category.color} bg-opacity-10`}>
                  <Icon className={`h-5 w-5 ${category.color} text-opacity-100`} />
                </div>
                <div className="text-center">
                  <div className="font-medium">{category.label}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {category.description}
                  </div>
                </div>
              </Button>
            )
          })}
        </div>
        <div className="mt-4 text-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onSelectOption("Show me all issues across all categories")}
          >
            Review All Categories
            <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}