/**
 * Sessions Tab Component
 * 
 * Displays a list of agent sessions with:
 * - Filtering by agent name and time range
 * - Session cards showing key information
 * - Expandable trace viewer (inline)
 * - Status indicators (completed, failed, in-progress)
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useAgents } from '@/contexts/AgentContext'
import { fetchSessions, type Session } from '@/services/observabilityService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'
import SessionFilters from './SessionFilters'
import SessionList from './SessionList'

export default function SessionsTab() {
  const { user } = useAuth()
  const { agents } = useAgents()
  const [allSessions, setAllSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [agentFilter, setAgentFilter] = useState<string>('')
  const [userIdFilter, setUserIdFilter] = useState<string>('')
  const [timeRangeHours, setTimeRangeHours] = useState<number>(24)

  const loadSessions = useCallback(async () => {
    if (!user?.id_token) {
      setError('Authentication required')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      // Calculate time range
      const endTime = Date.now()
      const startTime = endTime - (timeRangeHours * 60 * 60 * 1000)
      
      // Fetch all sessions without agent filter (we'll filter client-side)
      const data = await fetchSessions(user.id_token, {
        startTime,
        endTime,
        limit: 100, // Increased limit to get more sessions
      })
      
      // Debug: Log first session to see structure
      if (data.sessions.length > 0) {
        console.log('[SessionsTab] Sample session from API:', data.sessions[0])
        console.log('[SessionsTab] All unique agentNames in sessions:', 
          [...new Set(data.sessions.map(s => s.agentName))]
        )
      }
      
      setAllSessions(data.sessions)
    } catch (err) {
      console.error('Failed to load sessions:', err)
      setError(err instanceof Error ? err.message : 'Failed to load sessions')
    } finally {
      setLoading(false)
    }
  }, [user?.id_token, timeRangeHours]) // Only re-query when time range changes

  // Client-side filtering with useMemo for performance
  const filteredSessions = useMemo(() => {
    console.log('Filtering sessions:', {
      totalSessions: allSessions.length,
      agentFilter,
      userIdFilter
    })
    
    return allSessions.filter(session => {
      // Filter by agent name
      if (agentFilter && session.agentName !== agentFilter) {
        console.log(`Filtering out session ${session.sessionId}: agentName ${session.agentName} !== ${agentFilter}`)
        return false
      }
      
      // Filter by user ID (if implemented in session data)
      if (userIdFilter && !session.sessionId.includes(userIdFilter)) {
        return false
      }
      
      return true
    })
  }, [allSessions, agentFilter, userIdFilter])

  // Debug logging
  useEffect(() => {
    console.log('SessionsTab State:', {
      allSessionsCount: allSessions.length,
      filteredSessionsCount: filteredSessions.length,
      agentFilter,
      allSessions: allSessions.map(s => ({ id: s.sessionId, agent: s.agentName })),
      filteredSessions: filteredSessions.map(s => ({ id: s.sessionId, agent: s.agentName }))
    })
  }, [allSessions, filteredSessions, agentFilter])

  // Initial load
  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  const handleRefresh = () => {
    loadSessions()
  }

  if (loading && allSessions.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-2">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Loading sessions...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Error Loading Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
          <Button onClick={handleRefresh} className="mt-4">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <SessionFilters
        agents={agents}
        agentFilter={agentFilter}
        onAgentFilterChange={setAgentFilter}
        userIdFilter={userIdFilter}
        onUserIdFilterChange={setUserIdFilter}
        timeRange={timeRangeHours}
        onTimeRangeChange={setTimeRangeHours}
        onRefresh={handleRefresh}
        loading={loading}
      />

      {/* Sessions List */}
      {filteredSessions.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No Sessions Found</CardTitle>
            <CardDescription>
              {allSessions.length === 0 
                ? 'No sessions available in the selected time range.'
                : 'No sessions match the current filters. Try adjusting the agent or user filter.'}
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <SessionList sessions={filteredSessions} />
      )}
    </div>
  )
}
