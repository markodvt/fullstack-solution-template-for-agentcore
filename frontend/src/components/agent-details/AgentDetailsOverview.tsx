/**
 * AgentDetailsOverview displays agent metadata including model, tools, and runtime information.
 * 
 * This component shows:
 * - Agent model specification
 * - Complete tools list (expandable if many tools)
 * - Runtime ARN with copy-to-clipboard functionality
 * - Agent pattern information
 * 
 * Requirements: 3.3, 3.4, 3.5, 3.7
 */

import { Agent } from '@/services/agentDiscoveryService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Copy, Check, Cpu, Wrench, Server, FolderTree } from 'lucide-react'
import { useState } from 'react'

interface AgentDetailsOverviewProps {
  agent: Agent
}

export default function AgentDetailsOverview({ agent }: AgentDetailsOverviewProps) {
  const [copiedArn, setCopiedArn] = useState(false)

  const handleCopyArn = async () => {
    try {
      await navigator.clipboard.writeText(agent.runtimeArn)
      setCopiedArn(true)
      setTimeout(() => setCopiedArn(false), 2000)
    } catch (err) {
      console.error('Failed to copy ARN:', err)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent Configuration</CardTitle>
        <CardDescription>
          Technical details and configuration for this agent
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Model Section */}
        {agent.model && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Cpu className="h-4 w-4 text-muted-foreground" />
              Model
            </div>
            <div className="pl-6">
              <Badge variant="secondary" className="font-mono">
                {agent.model}
              </Badge>
            </div>
          </div>
        )}

        {/* Tools Section */}
        {agent.tools && agent.tools.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Wrench className="h-4 w-4 text-muted-foreground" />
              Tools ({agent.tools.length})
            </div>
            <div className="pl-6 flex flex-wrap gap-2">
              {agent.tools.map((tool, index) => (
                <Badge key={index} variant="outline">
                  {tool}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Pattern Section */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <FolderTree className="h-4 w-4 text-muted-foreground" />
            Pattern
          </div>
          <div className="pl-6">
            <Badge variant="secondary">{agent.pattern}</Badge>
          </div>
        </div>

        {/* Runtime ARN Section */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Server className="h-4 w-4 text-muted-foreground" />
            Runtime ARN
          </div>
          <div className="pl-6 flex items-center gap-2">
            <code className="flex-1 text-xs bg-muted px-3 py-2 rounded font-mono break-all">
              {agent.runtimeArn}
            </code>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyArn}
              className="gap-2 shrink-0"
            >
              {copiedArn ? (
                <>
                  <Check className="h-3.5 w-3.5" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  Copy
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Runtime ID Section */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Server className="h-4 w-4 text-muted-foreground" />
            Runtime ID
          </div>
          <div className="pl-6">
            <code className="text-xs bg-muted px-3 py-2 rounded font-mono">
              {agent.runtimeId}
            </code>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
