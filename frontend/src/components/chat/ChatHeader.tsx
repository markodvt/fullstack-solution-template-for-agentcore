import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { AgentSelector } from "./AgentSelector"
import type { Agent } from "@/services/agentDiscoveryService"

type ChatHeaderProps = {
  title?: string | undefined
  onNewChat: () => void
  canStartNewChat: boolean
  agents: Agent[]
  selectedAgent: Agent | null
  onAgentChange: (agent: Agent) => void
  agentSelectorDisabled?: boolean
}

export function ChatHeader({
  title,
  onNewChat,
  canStartNewChat,
  agents,
  selectedAgent,
  onAgentChange,
  agentSelectorDisabled = false,
}: ChatHeaderProps) {
  return (
    <header className="flex items-center justify-between p-4 border-b w-full">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold">{title || "Chat"}</h1>
        {agents.length > 0 && (
          <AgentSelector
            agents={agents}
            selectedAgent={selectedAgent}
            onAgentChange={onAgentChange}
            disabled={agentSelectorDisabled}
          />
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button onClick={onNewChat} variant="outline" className="gap-2" disabled={!canStartNewChat}>
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>
    </header>
  )
}
