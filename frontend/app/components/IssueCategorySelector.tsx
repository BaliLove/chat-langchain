'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from './ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { 
  Briefcase, 
  Building, 
  Megaphone, 
  DollarSign, 
  Cpu, 
  HeadphonesIcon, 
  Users,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react'

interface IssueCategorySelectorProps {
  onCategorySelect: (category: string, period?: string) => void
  onStartReview: () => void
}

const ISSUE_CATEGORIES = [
  { 
    value: 'operations', 
    label: 'Operations', 
    icon: Briefcase,
    description: 'Workflow, processes, and efficiency',
    color: 'bg-blue-500'
  },
  { 
    value: 'venue', 
    label: 'Venue', 
    icon: Building,
    description: 'Partner venues and locations',
    color: 'bg-purple-500'
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
  },
  { 
    value: 'team', 
    label: 'Team', 
    icon: Users,
    description: 'People and culture',
    color: 'bg-orange-500'
  }
]

const REVIEW_PERIODS = [
  { value: '7', label: 'Last 7 days' },
  { value: '14', label: 'Last 14 days' },
  { value: '30', label: 'Last 30 days' },
  { value: 'all', label: 'All active issues' }
]

export default function IssueCategorySelector({ 
  onCategorySelect, 
  onStartReview 
}: IssueCategorySelectorProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedPeriod, setSelectedPeriod] = useState<string>('7')
  const [viewMode, setViewMode] = useState<'grid' | 'dropdown'>('grid')

  const handleCategorySelect = (category: string) => {
    setSelectedCategory(category)
    onCategorySelect(category, selectedPeriod)
  }

  const handleStartReview = () => {
    if (selectedCategory) {
      onStartReview()
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-foreground">Issue Category Review</h2>
        <p className="text-muted-foreground mt-2">
          Select a category to review your team&apos;s issues
        </p>
      </div>

      {/* View Mode Toggle */}
      <div className="flex justify-center gap-2">
        <Button
          size="sm"
          variant={viewMode === 'grid' ? 'default' : 'outline'}
          onClick={() => setViewMode('grid')}
        >
          Grid View
        </Button>
        <Button
          size="sm"
          variant={viewMode === 'dropdown' ? 'default' : 'outline'}
          onClick={() => setViewMode('dropdown')}
        >
          Dropdown
        </Button>
      </div>

      {/* Category Selection */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {ISSUE_CATEGORIES.map((category) => {
            const Icon = category.icon
            const isSelected = selectedCategory === category.value
            
            return (
              <Card
                key={category.value}
                className={`cursor-pointer transition-all ${
                  isSelected 
                    ? 'ring-2 ring-primary shadow-lg' 
                    : 'hover:shadow-md'
                }`}
                onClick={() => handleCategorySelect(category.value)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className={`p-2 rounded-lg ${category.color} bg-opacity-10`}>
                      <Icon className={`h-5 w-5 ${category.color} text-opacity-100`} />
                    </div>
                    {isSelected && (
                      <CheckCircle className="h-5 w-5 text-primary" />
                    )}
                  </div>
                  <CardTitle className="text-lg mt-2">{category.label}</CardTitle>
                  <CardDescription className="text-sm">
                    {category.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            )
          })}
        </div>
      ) : (
        <div className="max-w-md mx-auto space-y-4">
          <Select value={selectedCategory} onValueChange={handleCategorySelect}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select a category" />
            </SelectTrigger>
            <SelectContent>
              {ISSUE_CATEGORIES.map((category) => (
                <SelectItem key={category.value} value={category.value}>
                  <div className="flex items-center gap-2">
                    <category.icon className="h-4 w-4" />
                    <span>{category.label}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Period Selection */}
      {selectedCategory && (
        <div className="max-w-md mx-auto space-y-4">
          <label className="text-sm font-medium">Review Period</label>
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {REVIEW_PERIODS.map((period) => (
                <SelectItem key={period.value} value={period.value}>
                  {period.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Start Review Button */}
      {selectedCategory && (
        <div className="flex justify-center">
          <Button
            size="lg"
            onClick={handleStartReview}
            className="min-w-[200px]"
          >
            <FileText className="h-5 w-5 mr-2" />
            Start Review
          </Button>
        </div>
      )}

      {/* Quick Stats Preview (optional) */}
      {selectedCategory && (
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="text-lg">Quick Preview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-primary">12</div>
                <div className="text-sm text-muted-foreground">Active Issues</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-600">3</div>
                <div className="text-sm text-muted-foreground">Need Attention</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">5</div>
                <div className="text-sm text-muted-foreground">Resolved This Week</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}