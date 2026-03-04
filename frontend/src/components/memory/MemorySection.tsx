/**
 * MemorySection displays a collapsible section of memories grouped by strategy type.
 * 
 * This component:
 * - Groups memories by strategy (summaries, preferences, facts)
 * - Provides expand/collapse functionality
 * - Persists expand/collapse state in localStorage via context
 * - Color-codes section headers by strategy type
 * - Responds to global expand/collapse all commands
 * 
 * Requirements: UX enhancement for better information organization (task 36.2)
 */

import { useState, useEffect } from 'react'
import { Memory } from '@/services/memoryService'
import MemoryCard from './MemoryCard'
import { ChevronDown, ChevronRight, BookOpen, Heart, Lightbulb, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useMemoryExpand } from '@/contexts/MemoryExpandContext'

interface MemorySectionProps {
  strategyType: 'summary' | 'preference' | 'fact' | 'event'
  memories: Memory[]
}

/**
 * Get display name for strategy type.
 */
function getStrategyDisplayName(type: MemorySectionProps['strategyType']): string {
  switch (type) {
    case 'summary':
      return 'Summaries'
    case 'preference':
      return 'Preferences'
    case 'fact':
      return 'Facts'
    case 'event':
      return 'Events'
    default:
      return type
  }
}

/**
 * Get color classes for strategy type.
 */
function getStrategyColorClasses(type: MemorySectionProps['strategyType']): string {
  switch (type) {
    case 'summary':
      return 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800'
    case 'preference':
      return 'bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-800'
    case 'fact':
      return 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800'
    case 'event':
      return 'bg-gray-50 dark:bg-gray-950 border-gray-200 dark:border-gray-800'
    default:
      return 'bg-gray-50 dark:bg-gray-950 border-gray-200 dark:border-gray-800'
  }
}

/**
 * Get icon component and color for strategy type.
 * Colors match the MemoryStats component badges.
 */
function getStrategyIcon(type: MemorySectionProps['strategyType']): { Icon: typeof BookOpen; colorClass: string } {
  switch (type) {
    case 'summary':
      return { Icon: BookOpen, colorClass: 'text-blue-500' }
    case 'preference':
      return { Icon: Heart, colorClass: 'text-pink-500' }
    case 'fact':
      return { Icon: Lightbulb, colorClass: 'text-yellow-500' }
    case 'event':
      return { Icon: FileText, colorClass: 'text-gray-500' }
    default:
      return { Icon: FileText, colorClass: 'text-gray-500' }
  }
}

export default function MemorySection({ strategyType, memories }: MemorySectionProps) {
  const { sectionsExpanded, setSectionExpanded, globalExpandState } = useMemoryExpand()
  
  // Initialize expanded state from context (default: true if not set)
  const [isExpanded, setIsExpanded] = useState<boolean>(() => {
    return sectionsExpanded[strategyType] !== undefined 
      ? sectionsExpanded[strategyType] 
      : true
  })

  // Sync local state with context
  useEffect(() => {
    if (sectionsExpanded[strategyType] !== undefined) {
      setIsExpanded(sectionsExpanded[strategyType])
    }
  }, [sectionsExpanded, strategyType])

  // Handle global expand/collapse all commands
  useEffect(() => {
    if (globalExpandState === 'expanded') {
      setIsExpanded(true)
      setSectionExpanded(strategyType, true)
    } else if (globalExpandState === 'collapsed') {
      setIsExpanded(false)
      setSectionExpanded(strategyType, false)
    }
  }, [globalExpandState, strategyType, setSectionExpanded])

  const toggleExpanded = () => {
    const newState = !isExpanded
    setIsExpanded(newState)
    setSectionExpanded(strategyType, newState)
  }

  const displayName = getStrategyDisplayName(strategyType)
  const colorClasses = getStrategyColorClasses(strategyType)
  const { Icon, colorClass } = getStrategyIcon(strategyType)

  return (
    <div className="space-y-2">
      {/* Section Header */}
      <div className={`rounded-lg border p-3 ${colorClasses}`}>
        <Button
          variant="ghost"
          className="w-full flex items-center justify-between p-0 h-auto hover:bg-transparent"
          onClick={toggleExpanded}
        >
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            <Icon className={`h-4 w-4 ${colorClass}`} />
            <h3 className="text-base font-semibold">{displayName}</h3>
            <span className="text-sm text-muted-foreground">
              ({memories.length})
            </span>
          </div>
        </Button>
      </div>

      {/* Memory Cards (with smooth animation) */}
      {isExpanded && (
        <div className="space-y-2.5 animate-in fade-in-50 duration-200">
          {memories.map((memory) => (
            <MemoryCard key={memory.id} memory={memory} />
          ))}
        </div>
      )}
    </div>
  )
}
