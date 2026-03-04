/**
 * MemoryStats displays statistics about agent memories.
 * 
 * This component:
 * - Displays total memory count
 * - Displays count by strategy (summaries, preferences, facts)
 * - Uses shadcn/ui Card components
 * - Shows icons for each strategy type
 * - Displays as horizontal row of stat cards
 * - Animates stat changes with subtle transitions
 * 
 * Requirements: UX enhancement for better usability and information density
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Memory } from '@/services/memoryService'
import { FileText, Heart, Lightbulb, Database } from 'lucide-react'
import { useEffect, useState } from 'react'

interface MemoryStatsProps {
  memories: Memory[]
}

/**
 * Calculate memory counts by type.
 * 
 * @param memories - Array of memory records
 * @returns Object with counts for each type
 */
function calculateStats(memories: Memory[]) {
  const stats = {
    total: memories.length,
    summaries: 0,
    preferences: 0,
    facts: 0,
    events: 0,
  }

  memories.forEach((memory) => {
    switch (memory.type) {
      case 'summary':
        stats.summaries++
        break
      case 'preference':
        stats.preferences++
        break
      case 'fact':
        stats.facts++
        break
      case 'event':
        stats.events++
        break
    }
  })

  return stats
}

export default function MemoryStats({ memories }: MemoryStatsProps) {
  const stats = calculateStats(memories)
  const [animateStats, setAnimateStats] = useState(false)

  // Trigger animation when stats change
  useEffect(() => {
    setAnimateStats(true)
    const timer = setTimeout(() => setAnimateStats(false), 300)
    return () => clearTimeout(timer)
  }, [stats.total, stats.summaries, stats.preferences, stats.facts])

  return (
    <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
      {/* Total Memories */}
      <Card>
        <CardHeader className="pb-2 pt-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              Total Memories
            </CardTitle>
            <Database className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent className="pb-3">
          <div 
            className={`text-xl font-bold transition-all duration-300 ${
              animateStats ? 'scale-110 text-primary' : 'scale-100'
            }`}
          >
            {stats.total}
          </div>
        </CardContent>
      </Card>

      {/* Summaries */}
      <Card>
        <CardHeader className="pb-2 pt-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              Summaries
            </CardTitle>
            <FileText className="h-3.5 w-3.5 text-blue-500" />
          </div>
        </CardHeader>
        <CardContent className="pb-3">
          <div 
            className={`text-xl font-bold transition-all duration-300 ${
              animateStats ? 'scale-110 text-blue-500' : 'scale-100'
            }`}
          >
            {stats.summaries}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Conversation summaries
          </p>
        </CardContent>
      </Card>

      {/* Preferences */}
      <Card>
        <CardHeader className="pb-2 pt-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              Preferences
            </CardTitle>
            <Heart className="h-3.5 w-3.5 text-pink-500" />
          </div>
        </CardHeader>
        <CardContent className="pb-3">
          <div 
            className={`text-xl font-bold transition-all duration-300 ${
              animateStats ? 'scale-110 text-pink-500' : 'scale-100'
            }`}
          >
            {stats.preferences}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            User preferences
          </p>
        </CardContent>
      </Card>

      {/* Facts */}
      <Card>
        <CardHeader className="pb-2 pt-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              Facts
            </CardTitle>
            <Lightbulb className="h-3.5 w-3.5 text-yellow-500" />
          </div>
        </CardHeader>
        <CardContent className="pb-3">
          <div 
            className={`text-xl font-bold transition-all duration-300 ${
              animateStats ? 'scale-110 text-yellow-500' : 'scale-100'
            }`}
          >
            {stats.facts}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Semantic facts
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
