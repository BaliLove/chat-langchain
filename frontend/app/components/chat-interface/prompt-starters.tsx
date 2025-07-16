'use client'

import { Button } from '@/app/components/ui/button'

interface PromptStartersProps {
  promptId: string
  onSelectOption: (option: string) => void
}

export function PromptStarters({ promptId, onSelectOption }: PromptStartersProps) {
  // Only show for issue review prompt
  if (promptId !== 'bali-love-issue-review') {
    return null
  }

  const categories = [
    { name: 'Client Exp', id: '1683764063723x899495422051483600' },
    { name: 'Weddings', id: '1683764078523x515115226215481340' },
    { name: 'Guests & Accom', id: '1698451776177x772559502883684400' },
    { name: 'Event Requests', id: '1683764027028x314003986352177150' },
    { name: 'Vendor & Product Requests', id: '1683764033628x667123255737843700' },
    { name: 'Catalog', id: '1683764048683x626863668112916500' },
    { name: 'Accounts', id: '1698451776177x772559502883684401' },
    { name: 'Metabase', id: '1698451776177x772559502883684402' },
    { name: 'App Requests', id: '1698451776177x772559502883684403' },
    { name: 'App Updates', id: '1698451776177x772559502883684404' },
    { name: 'Digital', id: '1698451776177x772559502883684405' },
    { name: 'Revenue', id: '1698451776177x772559502883684406' },
    { name: 'People', id: '1698451776177x772559502883684407' },
    { name: 'Leaders', id: '1698451776177x772559502883684408' },
    { name: 'AI Workflows', id: '1698451776177x772559502883684409' },
    { name: 'Venues', id: '1698451776177x772559502883684410' },
    { name: 'Content', id: '1698451776177x772559502883684411' },
    { name: 'Styling', id: '1698451776177x772559502883684412' },
    { name: 'Vehicles', id: '1698451776177x772559502883684413' }
  ]

  return (
    <div className="mb-4">
      <p className="text-sm text-muted-foreground mb-3">Select a category to review:</p>
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => (
          <Button
            key={category.id}
            variant="outline"
            onClick={() => onSelectOption(`I'd like to review ${category.name} issues (Category ID: ${category.id})`)}
          >
            {category.name}
          </Button>
        ))}
        <Button
          variant="ghost"
          onClick={() => onSelectOption("Show me all issues across all categories")}
        >
          All Categories
        </Button>
      </div>
    </div>
  )
}