/**
 * MemoryPage displays agent memories with filtering and sorting capabilities.
 * 
 * This page:
 * - Fetches memories from the Memory API
 * - Provides filtering by agent name and user ID
 * - Provides sorting by timestamp
 * - Shows loading skeletons during fetch
 * - Displays error state with retry button
 * - Shows empty state when no memories are found
 * 
 * Requirements: 15.1, 15.2, 15.3, 15.4
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useAuth } from 'react-oidc-context'
import { useAgents } from '@/contexts/AgentContext'
import { MemoryExpandProvider } from '@/contexts/MemoryExpandContext'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { NavigationBar } from '@/components/navigation/NavigationBar'
import MemoryPageHeader from '@/components/memory/MemoryPageHeader'
import MemoryStats from '@/components/memory/MemoryStats'
import MemoryFilters from '@/components/memory/MemoryFilters'
import MemoryList from '@/components/memory/MemoryList'
import { fetchMemories, Memory, MemoryFilters as MemoryFiltersType } from '@/services/memoryService'

export default function MemoryPage() {
  const auth = useAuth()
  const { agents } = useAgents()
  
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<MemoryFiltersType>({
    sortOrder: 'desc',
    limit: 50,
  })

  /**
   * Fetches memories from the API (without filters - we filter client-side).
   */
  const loadMemories = useCallback(async () => {
    // Don't fetch if not authenticated
    if (!auth.isAuthenticated || !auth.user?.id_token) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Fetch all memories without filters (client-side filtering is faster)
      const response = await fetchMemories(auth.user.id_token, {
        sortOrder: filters.sortOrder,
        limit: filters.limit,
      })
      setMemories(response.memories)
      setError(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch memories'
      console.error('Memory fetch error:', errorMessage)
      setError(errorMessage)
      setMemories([])
    } finally {
      setLoading(false)
    }
  }, [auth.isAuthenticated, auth.user?.id_token, filters.sortOrder, filters.limit])

  /**
   * Refetch memories when sort order or limit changes.
   */
  useEffect(() => {
    loadMemories()
  }, [loadMemories])

  /**
   * Handle filter changes.
   */
  const handleFiltersChange = (newFilters: MemoryFiltersType) => {
    setFilters(newFilters)
  }

  /**
   * Filter memories client-side for display.
   */
  const filteredMemories = useMemo(() => {
    let filtered = memories

    // Filter by agent name (exact match)
    if (filters.agentName) {
      filtered = filtered.filter((memory) => memory.agentName === filters.agentName)
    }

    // Filter by user ID (partial match, case-insensitive)
    if (filters.userId) {
      const userIdLower = filters.userId.toLowerCase()
      filtered = filtered.filter((memory) =>
        memory.userId.toLowerCase().includes(userIdLower)
      )
    }

    return filtered
  }, [memories, filters.agentName, filters.userId])

  // Error state with retry button
  if (error && !loading) {
    return (
      <div className="min-h-screen bg-background">
        <NavigationBar />
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] gap-4 p-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-2xl font-semibold">Failed to Load Memories</h2>
          <p className="text-muted-foreground text-center max-w-md">
            {error}
          </p>
          <Button onClick={loadMemories} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <NavigationBar />
      <MemoryExpandProvider>
        <div className="container mx-auto px-4 py-6 max-w-5xl">
          <MemoryPageHeader />
          <MemoryStats memories={filteredMemories} />
          <MemoryFilters
            agents={agents}
            filters={filters}
            onFiltersChange={handleFiltersChange}
          />
          <MemoryList 
            memories={filteredMemories} 
            loading={loading} 
          />
        </div>
      </MemoryExpandProvider>
    </div>
  )
}
