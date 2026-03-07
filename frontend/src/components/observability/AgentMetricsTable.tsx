/**
 * Agent Metrics Table Component
 * 
 * Displays a sortable table of per-agent metrics including:
 * - Agent name
 * - Session count
 * - Token usage
 * - Average duration
 * - Success rate
 */

import { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { AgentMetrics } from '@/services/observabilityService'

interface AgentMetricsTableProps {
  agents: AgentMetrics[]
}

type SortField = 'agentName' | 'sessionCount' | 'totalTokens' | 'avgDuration' | 'successRate'
type SortDirection = 'asc' | 'desc'

export default function AgentMetricsTable({ agents }: AgentMetricsTableProps) {
  const [sortField, setSortField] = useState<SortField>('sessionCount')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const sortedAgents = [...agents].sort((a, b) => {
    let aValue: number | string
    let bValue: number | string

    switch (sortField) {
      case 'agentName':
        aValue = a.agentName
        bValue = b.agentName
        break
      case 'sessionCount':
        aValue = a.sessionCount
        bValue = b.sessionCount
        break
      case 'totalTokens':
        aValue = a.totalTokens
        bValue = b.totalTokens
        break
      case 'avgDuration':
        aValue = a.avgDuration
        bValue = b.avgDuration
        break
      case 'successRate':
        aValue = a.successRate
        bValue = b.successRate
        break
      default:
        aValue = 0
        bValue = 0
    }

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortDirection === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue)
    }

    return sortDirection === 'asc' 
      ? (aValue as number) - (bValue as number)
      : (bValue as number) - (aValue as number)
  })

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

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="ml-2 h-4 w-4" />
    }
    return sortDirection === 'asc' 
      ? <ArrowUp className="ml-2 h-4 w-4" />
      : <ArrowDown className="ml-2 h-4 w-4" />
  }

  if (agents.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No agent metrics available
      </div>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <Button
                variant="ghost"
                onClick={() => handleSort('agentName')}
                className="h-8 px-2"
              >
                Agent Name
                <SortIcon field="agentName" />
              </Button>
            </TableHead>
            <TableHead className="text-right">
              <Button
                variant="ghost"
                onClick={() => handleSort('sessionCount')}
                className="h-8 px-2"
              >
                Sessions
                <SortIcon field="sessionCount" />
              </Button>
            </TableHead>
            <TableHead className="text-right">
              <Button
                variant="ghost"
                onClick={() => handleSort('totalTokens')}
                className="h-8 px-2"
              >
                Tokens
                <SortIcon field="totalTokens" />
              </Button>
            </TableHead>
            <TableHead className="text-right">
              <Button
                variant="ghost"
                onClick={() => handleSort('avgDuration')}
                className="h-8 px-2"
              >
                Avg Duration
                <SortIcon field="avgDuration" />
              </Button>
            </TableHead>
            <TableHead className="text-right">
              <Button
                variant="ghost"
                onClick={() => handleSort('successRate')}
                className="h-8 px-2"
              >
                Success Rate
                <SortIcon field="successRate" />
              </Button>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedAgents.map((agent) => (
            <TableRow key={agent.agentName}>
              <TableCell className="font-medium">{agent.agentName}</TableCell>
              <TableCell className="text-right">{agent.sessionCount}</TableCell>
              <TableCell className="text-right">
                <div>{formatNumber(agent.totalTokens)}</div>
                <div className="text-xs text-muted-foreground">
                  {formatNumber(agent.inputTokens)} / {formatNumber(agent.outputTokens)}
                </div>
              </TableCell>
              <TableCell className="text-right">{formatDuration(agent.avgDuration)}</TableCell>
              <TableCell className="text-right">
                <span className={agent.successRate >= 90 ? 'text-green-600' : agent.successRate >= 70 ? 'text-yellow-600' : 'text-red-600'}>
                  {agent.successRate.toFixed(1)}%
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
