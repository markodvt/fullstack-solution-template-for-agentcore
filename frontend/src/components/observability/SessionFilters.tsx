/**
 * Session Filters Component
 * 
 * Provides filtering controls for sessions:
 * - Agent name filter (text input)
 * - Time range selector
 * - Refresh button
 */

import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { RefreshCw, Filter } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Agent } from '@/services/agentDiscoveryService'

interface SessionFiltersProps {
  agents: Agent[]
  agentFilter: string
  onAgentFilterChange: (value: string) => void
  userIdFilter: string
  onUserIdFilterChange: (value: string) => void
  timeRange: number
  onTimeRangeChange: (value: number) => void
  onRefresh: () => void
  loading: boolean
}

const TIME_RANGES = [
  { label: '1h', value: 1 },
  { label: '24h', value: 24 },
  { label: '7d', value: 168 },
  { label: '30d', value: 720 },
]

export default function SessionFilters({
  agents,
  agentFilter,
  onAgentFilterChange,
  userIdFilter,
  onUserIdFilterChange,
  timeRange,
  onTimeRangeChange,
  onRefresh,
  loading,
}: SessionFiltersProps) {
  // Debug logging for agent filter values
  console.log('[SessionFilters] Available agents:', agents.map(a => ({
    name: a.name,
    displayName: a.displayName
  })))
  console.log('[SessionFilters] Current agentFilter value:', agentFilter)

  const handleAgentChange = (value: string) => {
    const filterValue = value === 'all' ? '' : value
    console.log('[SessionFilters] Agent filter changed:', {
      selectedValue: value,
      filterValue: filterValue,
      willSendToAPI: filterValue
    })
    onAgentFilterChange(filterValue)
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Agent Filter Dropdown */}
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select
                value={agentFilter || 'all'}
                onValueChange={handleAgentChange}
              >
                <SelectTrigger className="max-w-sm">
                  <SelectValue placeholder="Filter by agent" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Agents</SelectItem>
                  {agents.map((agent) => (
                    <SelectItem key={agent.name} value={agent.name}>
                      {agent.displayName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* User ID Filter */}
          <div className="flex-1">
            <Input
              placeholder="Filter by user ID..."
              value={userIdFilter}
              onChange={(e) => onUserIdFilterChange(e.target.value)}
              className="max-w-sm"
            />
          </div>

          {/* Time Range */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium whitespace-nowrap">Time Range:</span>
            <div className="flex gap-1">
              {TIME_RANGES.map((range) => (
                <Button
                  key={range.value}
                  variant={timeRange === range.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onTimeRangeChange(range.value)}
                >
                  {range.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Refresh Button */}
          <Button variant="outline" size="sm" onClick={onRefresh} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
