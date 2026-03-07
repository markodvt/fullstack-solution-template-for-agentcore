/**
 * Session Card Component
 * 
 * Displays a single session with:
 * - Session ID, agent name, user ID
 * - Start time, duration, status
 * - Status indicator (colored badge)
 * - Expandable trace viewer with full trace details
 */

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronUp, Clock, Activity, User } from 'lucide-react'
import type { Session } from '@/services/observabilityService'
import InlineTraceViewer from './InlineTraceViewer'

interface SessionCardProps {
  session: Session
}

export default function SessionCard({ session }: SessionCardProps) {
  const [expanded, setExpanded] = useState(false)

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${Math.round(ms)}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp).toLocaleString()
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      case 'in-progress':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getStatusVariant = (status: string): 'default' | 'destructive' | 'secondary' => {
    switch (status) {
      case 'completed':
        return 'default'
      case 'failed':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${getStatusColor(session.status)}`} />
              {session.agentDisplayName}
            </CardTitle>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span className="font-mono text-xs">{session.sessionId.substring(0, 8)}...</span>
              <Badge variant={getStatusVariant(session.status)}>
                {session.status}
              </Badge>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? (
              <>
                <ChevronUp className="h-4 w-4 mr-1" />
                Hide Details
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4 mr-1" />
                Show Details
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="text-sm font-medium">Duration</div>
              <div className="text-sm text-muted-foreground">{formatDuration(session.duration)}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="text-sm font-medium">Started</div>
              <div className="text-sm text-muted-foreground">{formatTimestamp(session.startTime)}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="text-sm font-medium">Spans</div>
              <div className="text-sm text-muted-foreground">{session.spanCount} spans</div>
            </div>
          </div>
        </div>

        {expanded && (
          <div className="mt-4 pt-4 border-t">
            <h4 className="text-sm font-medium mb-3">Trace Details</h4>
            <InlineTraceViewer sessionId={session.sessionId} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
