/**
 * AgentDetailsActions provides action buttons for the agent.
 * 
 * This component shows:
 * - "Chat" button to initiate conversation with the agent
 * - Button is disabled if agent deployment status is "failed"
 * - Visual indicator for disabled state
 * 
 * Requirements: 3.9, 3.10
 */

import { Agent } from '@/services/agentDiscoveryService'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { MessageSquare, AlertCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface AgentDetailsActionsProps {
  agent: Agent
}

export default function AgentDetailsActions({ agent }: AgentDetailsActionsProps) {
  const navigate = useNavigate()
  const isDeployed = agent.status === 'success'

  const handleChatClick = () => {
    if (!isDeployed) return
    navigate(`/?agent=${agent.name}`)
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="font-semibold">Start a Conversation</h3>
            <p className="text-sm text-muted-foreground">
              {isDeployed
                ? 'Chat with this agent to explore its capabilities'
                : 'This agent is not available for chat due to deployment failure'}
            </p>
          </div>
          <Button
            onClick={handleChatClick}
            disabled={!isDeployed}
            size="lg"
            className="gap-2 w-full sm:w-auto"
          >
            <MessageSquare className="h-4 w-4" />
            Chat with Agent
          </Button>
        </div>

        {!isDeployed && (
          <div className="mt-4 flex items-start gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
            <AlertCircle className="h-4 w-4 text-destructive mt-0.5 shrink-0" />
            <div className="text-sm">
              <p className="font-medium text-destructive">Agent Unavailable</p>
              <p className="text-muted-foreground mt-1">
                This agent failed to deploy and cannot be used for conversations. 
                Check the deployment logs for more information.
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
