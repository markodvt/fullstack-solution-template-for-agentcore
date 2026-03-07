/**
 * Metrics Summary Component
 * 
 * Displays summary cards for key metrics:
 * - Total sessions
 * - Total tokens
 * - Average duration
 * - Success rate
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, Zap, Clock, CheckCircle } from 'lucide-react'
import type { Metrics } from '@/services/observabilityService'

interface MetricsSummaryProps {
  metrics: Metrics
}

export default function MetricsSummary({ metrics }: MetricsSummaryProps) {
  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${Math.round(ms)}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Total Sessions */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Sessions</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.totalSessions}</div>
          <p className="text-xs text-muted-foreground">
            Agent invocations
          </p>
        </CardContent>
      </Card>

      {/* Total Tokens */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatNumber(metrics.totalTokens)}</div>
          <p className="text-xs text-muted-foreground">
            {formatNumber(metrics.totalInputTokens)} in / {formatNumber(metrics.totalOutputTokens)} out
          </p>
        </CardContent>
      </Card>

      {/* Average Duration */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatDuration(metrics.avgDuration)}</div>
          <p className="text-xs text-muted-foreground">
            Per session
          </p>
        </CardContent>
      </Card>

      {/* Success Rate */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          <CheckCircle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.successRate.toFixed(1)}%</div>
          <p className="text-xs text-muted-foreground">
            Successful completions
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
