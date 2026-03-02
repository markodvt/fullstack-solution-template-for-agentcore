/**
 * AgentDetailsHeader displays the agent name and deployment status.
 * 
 * This component shows:
 * - Agent display name as the main heading
 * - Deployment status badge (success/failed)
 * 
 * Requirements: 3.2, 3.8
 */

import { Agent } from '@/services/agentDiscoveryService'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, XCircle } from 'lucide-react'

interface AgentDetailsHeaderProps {
  agent: Agent
}

export default function AgentDetailsHeader({ agent }: AgentDetailsHeaderProps) {
  const isDeployed = agent.status === 'success'

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <h1 className="text-3xl font-bold tracking-tight">{agent.displayName}</h1>
        <Badge
          variant={isDeployed ? 'default' : 'destructive'}
          className="gap-1.5 px-3 py-1"
        >
          {isDeployed ? (
            <>
              <CheckCircle2 className="h-3.5 w-3.5" />
              Deployed
            </>
          ) : (
            <>
              <XCircle className="h-3.5 w-3.5" />
              Failed
            </>
          )}
        </Badge>
      </div>
      {agent.description && (
        <p className="text-lg text-muted-foreground">{agent.description}</p>
      )}
      {agent.longDescription && (
        <p className="text-sm text-muted-foreground italic mt-2">{agent.longDescription}</p>
      )}
    </div>
  )
}
