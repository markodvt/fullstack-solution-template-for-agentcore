/**
 * AgentSystemPrompt displays the agent's system prompt.
 * 
 * This component shows:
 * - System prompt title and description
 * - Pre-formatted system prompt text
 * 
 * Only renders if the agent has a system prompt defined.
 */

import { Agent } from '@/services/agentDiscoveryService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { FileText } from 'lucide-react'

interface AgentSystemPromptProps {
  agent: Agent
}

export default function AgentSystemPrompt({ agent }: AgentSystemPromptProps) {
  // Don't render if no system prompt
  if (!agent.systemPrompt) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-muted-foreground" />
          <CardTitle>System Prompt</CardTitle>
        </div>
        <CardDescription>
          Instructions that define this agent's behavior and personality
        </CardDescription>
      </CardHeader>
      <CardContent>
        <pre className="text-sm bg-muted p-4 rounded-lg overflow-x-auto whitespace-pre-wrap break-words font-mono">
          {agent.systemPrompt}
        </pre>
      </CardContent>
    </Card>
  )
}
