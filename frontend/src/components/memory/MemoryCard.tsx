/**
 * MemoryCard displays a single memory record.
 * 
 * This component:
l * - Displays memory content with collapsed/expanded state
 * - Shows agent name, user ID, and timestamp
 * - Displays session ID badge when available
 * - Optimized for use within MemorySection (no redundant type badge)
 * - Formats timestamps in a user-friendly way
 * - Supports expand/collapse for long content
 * - Responds to global expand/collapse all commands
 * 
 * Requirements: 15.4, UX enhancement (tasks 33.3, 34.1, 35.2, 36.2)
 */

import { useState, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Memory } from '@/services/memoryService'
import { Calendar, User, Bot, ChevronDown, ChevronUp, MessageSquare } from 'lucide-react'
import { useMemoryExpand } from '@/contexts/MemoryExpandContext'

interface MemoryCardProps {
  memory: Memory
}

const PREVIEW_LENGTH = 100 // Characters to show in collapsed state

/**
 * Format ISO 8601 timestamp to user-friendly format.
 * 
 * @param timestamp - ISO 8601 timestamp string
 * @returns Formatted date string
 */
function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return timestamp
  }
}

/**
 * Truncate content to preview length with ellipsis.
 * 
 * @param content - Full content string
 * @param maxLength - Maximum length for preview
 * @returns Truncated content with ellipsis if needed
 */
function truncateContent(content: string, maxLength: number): string {
  if (content.length <= maxLength) {
    return content
  }
  
  // Find the last space before maxLength to avoid cutting words
  const truncated = content.slice(0, maxLength)
  const lastSpace = truncated.lastIndexOf(' ')
  
  if (lastSpace > maxLength * 0.8) {
    // If we found a space reasonably close to the end, use it
    return truncated.slice(0, lastSpace) + '...'
  }
  
  // Otherwise just truncate at maxLength
  return truncated + '...'
}

/**
 * Extract short session ID for display.
 * 
 * @param sessionId - Full session ID
 * @returns Shortened session ID (first 8 characters)
 */
function getShortSessionId(sessionId: string): string {
  return sessionId.slice(0, 8)
}

export default function MemoryCard({ memory }: MemoryCardProps) {
  const { cardsExpanded, setCardExpanded, globalExpandState } = useMemoryExpand()
  
  // Initialize expanded state from context (default: false - collapsed)
  const [isExpanded, setIsExpanded] = useState<boolean>(() => {
    // Default to false (collapsed) if not in context
    return cardsExpanded[memory.id] ?? false
  })

  // Sync local state with context
  useEffect(() => {
    if (cardsExpanded[memory.id] !== undefined) {
      setIsExpanded(cardsExpanded[memory.id])
    }
  }, [cardsExpanded, memory.id])

  // Handle global expand/collapse all commands
  useEffect(() => {
    if (globalExpandState === 'expanded') {
      setIsExpanded(true)
      setCardExpanded(memory.id, true)
    } else if (globalExpandState === 'collapsed') {
      setIsExpanded(false)
      setCardExpanded(memory.id, false)
    }
  }, [globalExpandState, memory.id, setCardExpanded])

  const toggleExpanded = () => {
    const newState = !isExpanded
    setIsExpanded(newState)
    setCardExpanded(memory.id, newState)
  }
  
  // Determine if content needs truncation
  const needsTruncation = memory.content.length > PREVIEW_LENGTH
  const displayContent = isExpanded || !needsTruncation
    ? memory.content
    : truncateContent(memory.content, PREVIEW_LENGTH)
  
  return (
    <Card className="transition-all duration-200">
      <CardContent className="pt-3 pb-2 space-y-1.5">
        {/* Header with timestamp and badges */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            {formatTimestamp(memory.timestamp)}
          </div>
          
          {/* Metadata badges */}
          <div className="flex items-center gap-1.5">
            {memory.sessionId && (
              <Badge variant="outline" className="text-xs font-mono py-0 px-1.5 h-5">
                <MessageSquare className="h-3 w-3" />
                {getShortSessionId(memory.sessionId)}
              </Badge>
            )}
          </div>
        </div>
        
        {/* Memory content with optional gradient fade */}
        <div className="relative">
          <p className="text-sm leading-snug whitespace-pre-wrap">
            {displayContent}
          </p>
          
          {/* Gradient fade for collapsed state */}
          {!isExpanded && needsTruncation && (
            <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-background to-transparent pointer-events-none" />
          )}
        </div>
        
        {/* Show more/less button */}
        {needsTruncation && (
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleExpanded}
            className="h-6 px-2 text-xs -ml-2"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-3 w-3 mr-1" />
                Show less
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3 mr-1" />
                Show more
              </>
            )}
          </Button>
        )}
        
        {/* Metadata footer - denser layout */}
        <div className="flex flex-wrap gap-2.5 text-xs text-muted-foreground pt-0.5">
          {memory.agentName && (
            <div className="flex items-center gap-1">
              <Bot className="h-3 w-3" />
              <span>{memory.agentName}</span>
            </div>
          )}
          
          <div className="flex items-center gap-1">
            <User className="h-3 w-3" />
            <span>{memory.userId}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
