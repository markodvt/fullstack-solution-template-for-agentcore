/**
 * MemoryPageHeader displays the title and description for the Memory page.
 * 
 * This component provides context about what memories are and how they work.
 * Includes expand/collapse all controls for sections and cards.
 * 
 * Requirements: 15.2, UX enhancement (task 36.2)
 */

import { Button } from '@/components/ui/button'
import { ChevronsDown, ChevronsUp } from 'lucide-react'
import { useMemoryExpand } from '@/contexts/MemoryExpandContext'

export default function MemoryPageHeader() {
  const { expandAll, collapseAll } = useMemoryExpand()

  return (
    <div className="mb-5">
      <div className="flex items-start justify-between gap-4 mb-1.5">
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Agent Memories</h1>
        </div>
        
        {/* Expand/Collapse All Controls */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={expandAll}
            className="gap-1.5"
          >
            <ChevronsDown className="h-4 w-4" />
            Expand All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={collapseAll}
            className="gap-1.5"
          >
            <ChevronsUp className="h-4 w-4" />
            Collapse All
          </Button>
        </div>
      </div>
      
      <p className="text-sm text-muted-foreground">
        View memories stored by agents across conversations, including summaries, preferences, and facts.
      </p>
    </div>
  )
}
