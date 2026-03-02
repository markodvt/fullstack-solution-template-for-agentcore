/**
 * AgentTile displays a single agent as a clickable card.
 * 
 * This component:
 * - Displays agent name, description, model, and tools count
 * - Shows deployment status badge (green=deployed, red=failed)
 * - Navigates to agent details page on click
 * - Uses shadcn/ui Card component
 * - Uses Lucide React icons
 * 
 * Note: The 'model' and 'tools' fields are not yet fully implemented in the backend.
 * The component gracefully handles missing fields by showing 'pattern' as model info
 * and displaying a placeholder for tools count.
 * 
 * Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10
 */

import { useNavigate } from 'react-router-dom'
import { Agent } from '@/services/agentDiscoveryService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Bot, CheckCircle2, XCircle, Wrench } from 'lucide-react'

interface AgentTileProps {
  agent: Agent
}

export default function AgentTile({ agent }: AgentTileProps) {
  const navigate = useNavigate()

  const handleClick = () => {
    navigate(`/agents/${encodeURIComponent(agent.name)}`)
  }

  // Determine status badge styling
  const statusConfig = {
    success: {
      icon: CheckCircle2,
      variant: 'default' as const,
      label: 'Deployed',
      className: 'bg-green-100 text-green-800 hover:bg-green-100',
    },
    failed: {
      icon: XCircle,
      variant: 'destructive' as const,
      label: 'Failed',
      className: 'bg-red-100 text-red-800 hover:bg-red-100',
    },
  }

  const status = statusConfig[agent.status] || statusConfig.success
  const StatusIcon = status.icon

  // Display model (use 'model' field if available, otherwise fall back to 'pattern')
  const modelDisplay = agent.model || agent.pattern || 'Unknown'

  // Display tools count (use 'tools' array length if available, otherwise show placeholder)
  const toolsCount = agent.tools?.length ?? 0
  const toolsDisplay = agent.tools ? `${toolsCount} tool${toolsCount !== 1 ? 's' : ''}` : 'Tools info pending'

  return (
    <Card
      className="cursor-pointer transition-all hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]"
      onClick={handleClick}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <Bot className="h-5 w-5 text-primary flex-shrink-0" />
            <CardTitle className="truncate">{agent.displayName}</CardTitle>
          </div>
          <Badge className={status.className}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {status.label}
          </Badge>
        </div>
        <CardDescription className="line-clamp-2 min-h-[2.5rem]">
          {agent.description || 'No description available'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center justify-between">
            <span className="font-medium">Model:</span>
            <span className="truncate ml-2">{modelDisplay}</span>
          </div>
          <div className="flex items-center justify-between">
            <Wrench className="h-4 w-4 flex-shrink-0" />
            <span className="truncate ml-2">{toolsDisplay}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
