/**
 * AgentDetailsPage displays comprehensive information about a single agent.
 * 
 * This page:
 * - Extracts agent name from route params
 * - Fetches agent data from AgentContext
 * - Displays agent metadata (name, description, model, tools, status, ARN)
 * - Shows agent Python source code with syntax highlighting
 * - Provides a "Chat" button to initiate conversation
 * - Includes breadcrumb navigation back to Agent Gallery
 * 
 * Requirements: 3.1, 3.2
 */

import { useParams, useNavigate } from 'react-router-dom'
import { useAgents } from '@/contexts/AgentContext'
import { NavigationBar } from '@/components/navigation/NavigationBar'
import { Button } from '@/components/ui/button'
import { AlertCircle, ArrowLeft } from 'lucide-react'
import AgentDetailsHeader from '@/components/agent-details/AgentDetailsHeader'
import AgentDetailsOverview from '@/components/agent-details/AgentDetailsOverview'
import AgentSystemPrompt from '@/components/agent-details/AgentSystemPrompt'
import AgentCodeViewer from '@/components/agent-details/AgentCodeViewer'
import AgentDetailsActions from '@/components/agent-details/AgentDetailsActions'

export default function AgentDetailsPage() {
  const { agentName } = useParams<{ agentName: string }>()
  const navigate = useNavigate()
  const { agents, loading } = useAgents()

  // Find the agent by name from route params
  const agent = agents.find(a => a.name === agentName)

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <NavigationBar />
        <div className="container mx-auto px-4 py-8 max-w-5xl">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-muted rounded w-1/3" />
            <div className="h-64 bg-muted rounded" />
            <div className="h-96 bg-muted rounded" />
          </div>
        </div>
      </div>
    )
  }

  // Agent not found state
  if (!agent) {
    return (
      <div className="min-h-screen bg-background">
        <NavigationBar />
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] gap-4 p-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-2xl font-semibold">Agent Not Found</h2>
          <p className="text-muted-foreground text-center max-w-md">
            The agent "{agentName}" could not be found. It may have been removed or the name is incorrect.
          </p>
          <Button onClick={() => navigate('/agents')} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Agent Gallery
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <NavigationBar />
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        {/* Breadcrumb navigation */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate('/agents')}
            className="gap-2 -ml-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Agent Gallery
          </Button>
        </div>

        {/* Agent details sections */}
        <div className="space-y-6">
          <AgentDetailsHeader agent={agent} />
          <AgentDetailsOverview agent={agent} />
          <AgentSystemPrompt agent={agent} />
          <AgentCodeViewer agent={agent} />
          <AgentDetailsActions agent={agent} />
        </div>
      </div>
    </div>
  )
}
