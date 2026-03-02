/**
 * AgentGalleryPage displays all available agents in a responsive grid layout.
 * 
 * This page:
 * - Fetches agents from AgentContext
 * - Displays agents in a responsive grid (1 col mobile, 2-3 cols desktop)
 * - Shows loading skeletons during fetch
 * - Displays error state with retry button
 * - Shows empty state when no agents are available
 * - Allows navigation to agent details page
 * 
 * Requirements: 1.1, 1.2, 1.3, 15.1, 15.2, 15.3
 */

import { useAgents } from '@/contexts/AgentContext'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCw } from 'lucide-react'
import AgentGalleryHeader from '@/components/agent-gallery/AgentGalleryHeader'
import AgentGalleryGrid from '@/components/agent-gallery/AgentGalleryGrid'
import { NavigationBar } from '@/components/navigation/NavigationBar'

export default function AgentGalleryPage() {
  const { agents, loading, error, refetch } = useAgents()

  // Error state with retry button
  if (error && !loading) {
    return (
      <div className="min-h-screen bg-background">
        <NavigationBar />
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] gap-4 p-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-2xl font-semibold">Failed to Load Agents</h2>
          <p className="text-muted-foreground text-center max-w-md">
            {error}
          </p>
          <Button onClick={refetch} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  // Empty state when no agents are available
  if (!loading && agents.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <NavigationBar />
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] gap-4 p-4">
          <h2 className="text-2xl font-semibold">No Agents Available</h2>
          <p className="text-muted-foreground text-center max-w-md">
            There are no agents deployed in your account. Deploy an agent to get started.
          </p>
          <Button onClick={refetch} variant="outline" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <NavigationBar />
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <AgentGalleryHeader />
        <AgentGalleryGrid agents={agents} loading={loading} />
      </div>
    </div>
  )
}
