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
    { name: 'Client Exp', id: '1683764027028x314003986352177150' },
    { name: 'Weddings', id: '1693533657343x969937389721485300' },
    { name: 'Guests & Accom', id: '1741142526992x988389256100053000' },
    { name: 'Event Requests', id: '1718583276371x601530858772889600' },
    { name: 'Vendor & Product Requests', id: '1683764063723x899495422051483600' },
    { name: 'Catalog', id: '1683764033628x667123255737843700' },
    { name: 'Accounts', id: '1683764048683x626863668112916500' },
    { name: 'Metabase', id: '1742966612846x527561452523880450' },
    { name: 'App Requests', id: '1698451776177x772559502883684400' },
    { name: 'App Updates', id: '1717457649476x806368590729052200' },
    { name: 'Digital', id: '1738915817674x528837169408639000' },
    { name: 'Revenue', id: '1683764078523x515115226215481340' },
    { name: 'People', id: '1740104677509x760140252792750100' },
    { name: 'Leaders', id: '1744589859864x437635632404889600' },
    { name: 'AI Workflows', id: '1745224797844x667612769532248000' },
    { name: 'Venues', id: '1747016792559x455050911166758900' },
    { name: 'Content', id: '1747283209160x324311400399765500' },
    { name: 'Styling', id: '1750390525543x913410424778522600' },
    { name: 'Vehicles', id: '1752649475036x855202485836447700' }
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