/**
 * AgentGalleryGrid displays agents in a responsive grid layout.
 * 
 * This component:
 * - Renders agents in a responsive grid (1 col mobile, 2-3 cols desktop)
 * - Shows loading skeletons during fetch
 * - Renders AgentTile for each agent
 * 
 * Requirements: 1.3, 15.1, 15.2, 15.3
 */

import { Agent } from '@/services/agentDiscoveryService'
import AgentTile from './AgentTile'
import { Skeleton } from '@/components/ui/skeleton'

interface AgentGalleryGridProps {
  agents: Agent[]
  loading: boolean
}

export default function AgentGalleryGrid({ agents, loading }: AgentGalleryGridProps) {
  // Show loading skeletons
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, index) => (
          <div key={index} className="space-y-3">
            <Skeleton className="h-48 w-full rounded-lg" />
          </div>
        ))}
      </div>
    )
  }

  // Render agent tiles
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {agents.map((agent) => (
        <AgentTile key={agent.name} agent={agent} />
      ))}
    </div>
  )
}
