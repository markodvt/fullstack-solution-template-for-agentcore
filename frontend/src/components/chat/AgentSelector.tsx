/**
 * AgentSelector component - Dropdown for selecting which agent to interact with.
 * 
 * This component displays a list of available agents and allows the user to
 * select which agent they want to chat with. The selected agent is persisted
 * in localStorage and used for all subsequent chat interactions.
 */

import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Agent } from '@/services/agentDiscoveryService'
import { Bot } from 'lucide-react'

interface AgentSelectorProps {
  agents: Agent[]
  selectedAgent: Agent | null
  onAgentChange: (agent: Agent) => void
  disabled?: boolean
}

export function AgentSelector({
  agents,
  selectedAgent,
  onAgentChange,
  disabled = false,
}: AgentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)

  // Handle agent selection
  const handleValueChange = (agentName: string) => {
    const agent = agents.find(a => a.name === agentName)
    if (agent) {
      onAgentChange(agent)
    }
  }

  if (agents.length === 0) {
    return null
  }

  return (
    <div className="flex items-center gap-2">
      <Bot className="h-4 w-4 text-gray-500" />
      <Select
        value={selectedAgent?.name || ''}
        onValueChange={handleValueChange}
        disabled={disabled}
        open={isOpen}
        onOpenChange={setIsOpen}
      >
        <SelectTrigger className="w-[240px]">
          <SelectValue placeholder="Select an agent">
            {selectedAgent ? (
              <span className="font-medium">{selectedAgent.displayName}</span>
            ) : (
              'Select an agent'
            )}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {agents.map((agent) => (
            <SelectItem key={agent.name} value={agent.name}>
              <div className="flex flex-col">
                <span className="font-medium">{agent.displayName}</span>
                <span className="text-xs text-gray-500">{agent.description}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
