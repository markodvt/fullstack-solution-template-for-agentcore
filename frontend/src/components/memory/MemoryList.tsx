/**
 * MemoryList displays memories grouped by strategy type with collapsible sections.
 * 
 * This component:
 * - Groups memories by type (summaries, preferences, facts, events)
 * - Renders MemorySection for each strategy with memories
 * - Shows loading skeletons during fetch
 * - Displays empty state when no memories are found
 * - Persists expand/collapse state in localStorage
 * 
 * Note: Filtering is now done in MemoryPage before passing memories to this component.
 * 
 * Requirements: 15.2, UX enhancement for better information organization
 */

import { Memory } from '@/services/memoryService'
import MemorySection from './MemorySection'
import { Skeleton } from '@/components/ui/skeleton'
import { Brain } from 'lucide-react'

interface MemoryListProps {
  memories: Memory[]
  loading: boolean
}

/**
 * Group memories by their type (strategy).
 * 
 * @param memories - Array of memory records
 * @returns Object with memories grouped by type
 */
function groupMemoriesByType(memories: Memory[]): Record<Memory['type'], Memory[]> {
  const grouped: Record<Memory['type'], Memory[]> = {
    summary: [],
    preference: [],
    fact: [],
    event: [],
  }

  memories.forEach((memory) => {
    if (grouped[memory.type]) {
      grouped[memory.type].push(memory)
    }
  })

  return grouped
}

export default function MemoryList({ memories, loading }: MemoryListProps) {
  // Show loading skeletons
  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(6)].map((_, index) => (
          <div key={index} className="space-y-3">
            <Skeleton className="h-40 w-full rounded-lg" />
          </div>
        ))}
      </div>
    )
  }

  // Show empty state
  if (memories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4">
        <Brain className="h-12 w-12 text-muted-foreground" />
        <h3 className="text-lg font-semibold">No Memories Found</h3>
        <p className="text-muted-foreground text-center max-w-md">
          No memories match your current filters. Try adjusting your filters or start a conversation with an agent to create memories.
        </p>
      </div>
    )
  }

  // Group memories by type
  const groupedMemories = groupMemoriesByType(memories)

  // Define the order of sections to display
  const sectionOrder: Array<Memory['type']> = ['summary', 'preference', 'fact', 'event']

  // Render memory sections (only show sections with memories)
  return (
    <div className="space-y-4">
      {sectionOrder.map((type) => {
        const memoriesForType = groupedMemories[type]
        
        // Only render section if it has memories
        if (memoriesForType.length === 0) {
          return null
        }

        return (
          <MemorySection
            key={type}
            strategyType={type}
            memories={memoriesForType}
          />
        )
      })}
    </div>
  )
}
