/**
 * Metrics Tab Component
 * 
 * Displays aggregated metrics including:
 * - Summary cards (total sessions, tokens, duration, success rate)
 * - Per-agent metrics table
 * - Top tools chart
 * - Time range selector
 * - Auto-refresh functionality
 */

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { fetchMetrics, type MetricsResponse } from '@/services/observabilityService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RefreshCw, Clock, Circle } from 'lucide-react'
import MetricsSummary from './MetricsSummary'
import AgentMetricsTable from './AgentMetricsTable'
import TopToolsChart from './TopToolsChart'
import TimeRangeSelector from './TimeRangeSelector'

const AUTO_REFRESH_INTERVAL = 30000 // 30 seconds

export default function MetricsTab() {
  const { user } = useAuth()
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState<number>(24) // Default: 24 hours
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const loadMetrics = useCallback(async () => {
    if (!user?.id_token) {
      setError('Authentication required')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const data = await fetchMetrics(user.id_token, timeRange)
      setMetrics(data)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Failed to load metrics:', err)
      setError(err instanceof Error ? err.message : 'Failed to load metrics')
    } finally {
      setLoading(false)
    }
  }, [user?.id_token, timeRange])

  // Initial load
  useEffect(() => {
    loadMetrics()
  }, [loadMetrics])

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      loadMetrics()
    }, AUTO_REFRESH_INTERVAL)

    return () => clearInterval(interval)
  }, [autoRefresh, loadMetrics])

  const handleTimeRangeChange = (newTimeRange: number) => {
    setTimeRange(newTimeRange)
  }

  const handleManualRefresh = () => {
    loadMetrics()
  }

  const toggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh)
  }

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-2">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Loading metrics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Error Loading Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
          <Button onClick={handleManualRefresh} className="mt-4">
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!metrics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Metrics Available</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No metrics data available for the selected time range.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <TimeRangeSelector value={timeRange} onChange={handleTimeRangeChange} />
        
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>Updated {lastUpdated.toLocaleTimeString()}</span>
            </div>
          )}
          
          <Button
            variant="outline"
            size="sm"
            onClick={toggleAutoRefresh}
            className={autoRefresh ? 'bg-primary/10' : ''}
          >
            {autoRefresh ? (
              <Circle className="mr-2 h-4 w-4 fill-green-500 text-green-500" />
            ) : (
              <Circle className="mr-2 h-4 w-4" />
            )}
            Auto-refresh {autoRefresh ? 'On' : 'Off'}
          </Button>
          
          <Button variant="outline" size="sm" onClick={handleManualRefresh} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <MetricsSummary metrics={metrics.metrics} />

      {/* Per-Agent Metrics Table */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Performance</CardTitle>
          <CardDescription>
            Detailed metrics breakdown by agent
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AgentMetricsTable agents={metrics.metrics.agentBreakdown} />
        </CardContent>
      </Card>

      {/* Top Tools Chart */}
      {metrics.metrics.topTools.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Top Tools</CardTitle>
            <CardDescription>
              Most frequently used tools across all agents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TopToolsChart tools={metrics.metrics.topTools} />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
