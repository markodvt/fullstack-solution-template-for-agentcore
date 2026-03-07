/**
 * Inline Trace Viewer Component
 * 
 * Displays trace data for a session with:
 * - Span timeline visualization
 * - Span details (name, duration, type, attributes)
 * - Color-coded spans by type
 * - Expandable span details
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronUp, Clock, Zap, Wrench, Bot, AlertCircle } from 'lucide-react'
import { fetchTraces, type Span, type Trace } from '@/services/observabilityService'
import { useAuth } from '@/hooks/useAuth'

interface InlineTraceViewerProps {
  sessionId: string
}

export default function InlineTraceViewer({ sessionId }: InlineTraceViewerProps) {
  const { user } = useAuth()
  const [trace, setTrace] = useState<Trace | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedSpans, setExpandedSpans] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadTrace()
  }, [sessionId])

  const loadTrace = async () => {
    if (!user?.id_token) {
      setError('Authentication required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetchTraces(user.id_token, sessionId)
      setTrace(response.trace)
    } catch (err) {
      console.error('Failed to load trace:', err)
      setError(err instanceof Error ? err.message : 'Failed to load trace data')
    } finally {
      setLoading(false)
    }
  }

  const toggleSpan = (spanId: string) => {
    const newExpanded = new Set(expandedSpans)
    if (newExpanded.has(spanId)) {
      newExpanded.delete(spanId)
    } else {
      newExpanded.add(spanId)
    }
    setExpandedSpans(newExpanded)
  }

  const formatDuration = (ms: number): string => {
    if (ms < 1) return `${(ms * 1000).toFixed(0)}μs`
    if (ms < 1000) return `${Math.round(ms)}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
    return `${(ms / 60000).toFixed(2)}m`
  }

  const getSpanIcon = (spanType: string) => {
    switch (spanType) {
      case 'agent_invocation':
        return <Bot className="h-4 w-4" />
      case 'llm_invocation':
        return <Zap className="h-4 w-4" />
      case 'tool_call':
        return <Wrench className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const getSpanColor = (spanType: string): string => {
    switch (spanType) {
      case 'agent_invocation':
        return 'bg-purple-500'
      case 'llm_invocation':
        return 'bg-green-500'
      case 'tool_call':
        return 'bg-blue-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getSpanBadgeVariant = (spanType: string): 'default' | 'secondary' | 'outline' => {
    switch (spanType) {
      case 'agent_invocation':
        return 'default'
      case 'llm_invocation':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  const buildSpanTree = (spans: Span[]): Span[] => {
    // Sort spans by start time
    return [...spans].sort((a, b) => a.startTime - b.startTime)
  }

  const getSpanDepth = (span: Span, spans: Span[]): number => {
    let depth = 0
    let currentSpan = span
    
    while (currentSpan.parentSpanId) {
      depth++
      const parent = spans.find(s => s.spanId === currentSpan.parentSpanId)
      if (!parent) break
      currentSpan = parent
    }
    
    return depth
  }

  if (loading) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <Clock className="h-6 w-6 animate-spin mx-auto mb-2" />
        Loading trace data...
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 border border-destructive rounded-md bg-destructive/10">
        <div className="flex items-center gap-2 text-destructive mb-2">
          <AlertCircle className="h-5 w-5" />
          <span className="font-medium">Failed to load trace</span>
        </div>
        <p className="text-sm text-muted-foreground">{error}</p>
        <Button
          variant="outline"
          size="sm"
          onClick={loadTrace}
          className="mt-2"
        >
          Retry
        </Button>
      </div>
    )
  }

  if (!trace || trace.spans.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        No trace data available for this session
      </div>
    )
  }

  const sortedSpans = buildSpanTree(trace.spans)

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-muted-foreground">
          <span className="font-medium">{trace.spans.length}</span> spans
          <span className="mx-2">•</span>
          <span>Total duration: {formatDuration(trace.duration)}</span>
        </div>
      </div>

      <div className="space-y-2">
        {sortedSpans.map((span) => {
          const depth = getSpanDepth(span, trace.spans)
          const isExpanded = expandedSpans.has(span.spanId)
          const hasAttributes = Object.keys(span.attributes || {}).length > 0

          return (
            <Card key={span.spanId} className="overflow-hidden">
              <CardHeader className="py-3 px-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2" style={{ marginLeft: `${depth * 20}px` }}>
                    <span className={`h-2 w-2 rounded-full ${getSpanColor(span.spanType)}`} />
                    {getSpanIcon(span.spanType)}
                    <CardTitle className="text-sm font-medium">{span.name}</CardTitle>
                    <Badge variant={getSpanBadgeVariant(span.spanType)} className="text-xs">
                      {span.spanType.replace('_', ' ')}
                    </Badge>
                    {span.status === 'error' && (
                      <Badge variant="destructive" className="text-xs">
                        Error
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-muted-foreground">
                      {formatDuration(span.duration)}
                    </span>
                    {hasAttributes && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleSpan(span.spanId)}
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>

              {isExpanded && hasAttributes && (
                <CardContent className="py-3 px-4 pt-0 border-t">
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Span Attributes</h4>
                    <div className="bg-muted p-3 rounded-md">
                      <dl className="space-y-1 text-xs font-mono">
                        {Object.entries(span.attributes).map(([key, value]) => (
                          <div key={key} className="grid grid-cols-3 gap-2">
                            <dt className="text-muted-foreground truncate">{key}:</dt>
                            <dd className="col-span-2 break-all">
                              {typeof value === 'object' 
                                ? JSON.stringify(value, null, 2) 
                                : String(value)}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          )
        })}
      </div>
    </div>
  )
}
