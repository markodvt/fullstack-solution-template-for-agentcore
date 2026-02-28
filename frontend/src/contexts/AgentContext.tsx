/**
 * AgentContext provides global state management for agent discovery and selection.
 * 
 * This context fetches agents from the Agent Discovery API on mount and provides
 * the agent list, loading state, error state, and refetch functionality to all
 * components in the application.
 * 
 * Usage:
 * ```tsx
 * import { useAgents } from '@/contexts/AgentContext'
 * 
 * function MyComponent() {
 *   const { agents, loading, error, refetch } = useAgents()
 *   // Use agents data...
 * }
 * ```
 */

import { createContext, useContext, useEffect, useState, useCallback, PropsWithChildren } from 'react'
import { useAuth } from 'react-oidc-context'
import { discoverAgents, Agent, AgentDiscoveryResponse } from '@/services/agentDiscoveryService'

/**
 * AgentContextType defines the shape of the agent context.
 * 
 * @property agents - Array of discovered agents
 * @property loading - Whether agents are currently being fetched
 * @property error - Error message if agent discovery failed
 * @property refetch - Function to manually trigger agent discovery
 */
export interface AgentContextType {
  agents: Agent[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

const AgentContext = createContext<AgentContextType | undefined>(undefined)

/**
 * AgentProvider component that wraps the application and provides agent state.
 * 
 * This provider:
 * - Fetches agents from the API on mount
 * - Handles authentication via useAuth hook
 * - Provides loading and error states
 * - Exposes a refetch function for manual updates
 * - Implements retry logic for failed requests
 * 
 * @param children - Child components that will have access to agent context
 */
export function AgentProvider({ children }: PropsWithChildren) {
  const auth = useAuth()
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  /**
   * Fetches agents from the discovery API.
   * 
   * This function:
   * - Validates authentication state
   * - Calls the discovery service with the ID token
   * - Updates state with results or error
   * - Handles errors gracefully
   */
  const fetchAgents = useCallback(async () => {
    // Don't fetch if not authenticated
    if (!auth.isAuthenticated || !auth.user?.id_token) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response: AgentDiscoveryResponse = await discoverAgents(auth.user.id_token)
      setAgents(response.agents)
      setError(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to discover agents'
      console.error('Agent discovery error:', errorMessage)
      setError(errorMessage)
      setAgents([])
    } finally {
      setLoading(false)
    }
  }, [auth.isAuthenticated, auth.user?.id_token])

  /**
   * Refetch function exposed to consumers for manual agent discovery.
   * 
   * This allows components to trigger a fresh fetch of agents,
   * useful for retry buttons or refresh actions.
   */
  const refetch = useCallback(async () => {
    await fetchAgents()
  }, [fetchAgents])

  // Fetch agents on mount and when authentication state changes
  useEffect(() => {
    fetchAgents()
  }, [fetchAgents])

  const value: AgentContextType = {
    agents,
    loading,
    error,
    refetch,
  }

  return <AgentContext.Provider value={value}>{children}</AgentContext.Provider>
}

/**
 * Custom hook to consume the AgentContext.
 * 
 * This hook provides access to the agent state and must be used within
 * an AgentProvider. It will throw an error if used outside the provider.
 * 
 * @returns AgentContextType containing agents, loading, error, and refetch
 * @throws Error if used outside of AgentProvider
 * 
 * @example
 * ```tsx
 * function AgentList() {
 *   const { agents, loading, error, refetch } = useAgents()
 *   
 *   if (loading) return <div>Loading...</div>
 *   if (error) return <div>Error: {error} <button onClick={refetch}>Retry</button></div>
 *   
 *   return (
 *     <ul>
 *       {agents.map(agent => (
 *         <li key={agent.name}>{agent.displayName}</li>
 *       ))}
 *     </ul>
 *   )
 * }
 * ```
 */
export function useAgents(): AgentContextType {
  const context = useContext(AgentContext)
  
  if (context === undefined) {
    throw new Error('useAgents must be used within an AgentProvider')
  }
  
  return context
}
