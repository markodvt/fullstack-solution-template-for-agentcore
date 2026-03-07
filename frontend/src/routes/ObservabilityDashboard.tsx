/**
 * Observability Dashboard Page
 * 
 * Provides comprehensive observability for agent sessions and metrics.
 * Features two tabs:
 * - Metrics: Aggregated metrics with charts and breakdowns
 * - Sessions: List of agent sessions with filtering and trace viewing
 */

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { NavigationBar } from '@/components/navigation/NavigationBar'
import MetricsTab from '@/components/observability/MetricsTab'
import SessionsTab from '@/components/observability/SessionsTab'

export default function ObservabilityDashboard() {
  const [activeTab, setActiveTab] = useState<string>('metrics')

  return (
    <>
      <NavigationBar />
      <div className="container mx-auto p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Observability Dashboard</h1>
        <p className="text-muted-foreground">
          Monitor agent performance, sessions, and system metrics
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="sessions">Sessions</TabsTrigger>
        </TabsList>

        <TabsContent value="metrics" className="space-y-6">
          <MetricsTab />
        </TabsContent>

        <TabsContent value="sessions" className="space-y-6">
          <SessionsTab />
        </TabsContent>
      </Tabs>
    </div>
    </>
  )
}
