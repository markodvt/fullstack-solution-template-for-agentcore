/**
 * Service for discovering available agents from the backend API.
 * 
 * This service fetches agent metadata from the Agent Discovery API endpoint,
 * which returns information about all deployed agents including their
 * display names, descriptions, runtime ARNs, and availability status.
 */

export interface Agent {
  name: string
  displayName: string
  description: string
  runtimeArn: string
  runtimeId: string
  pattern: string
  isDefault: boolean
  status: 'success' | 'failed'
  sourceCode?: string
  sourceCodeUrl?: string
  systemPrompt?: string
  longDescription?: string
  model?: string
  tools?: string[]
}

export interface AgentDiscoveryResponse {
  agents: Agent[]
  count: number
}

/**
 * Fetches the list of available agents from the discovery API.
 * 
 * @param idToken - JWT ID token for authentication
 * @returns Promise resolving to the agent discovery response
 * @throws Error if the API request fails or returns invalid data
 */
export async function discoverAgents(idToken: string): Promise<AgentDiscoveryResponse> {
  if (!idToken) {
    throw new Error('ID token is required for agent discovery')
  }

  // Load the API URL from aws-exports.json
  const response = await fetch('/aws-exports.json')
  if (!response.ok) {
    throw new Error('Failed to load configuration')
  }
  
  const config = await response.json()
  const feedbackApiUrl = config.feedbackApiUrl
  
  if (!feedbackApiUrl) {
    throw new Error('Feedback API URL not found in configuration')
  }

  // The agent discovery endpoint is at the same base URL as the feedback API
  const agentDiscoveryUrl = `${feedbackApiUrl}agents`

  // Call the agent discovery API
  const agentResponse = await fetch(agentDiscoveryUrl, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${idToken}`,
      'Content-Type': 'application/json',
    },
  })

  if (!agentResponse.ok) {
    const errorText = await agentResponse.text()
    throw new Error(`Failed to discover agents: HTTP ${agentResponse.status}: ${errorText}`)
  }

  const data: AgentDiscoveryResponse = await agentResponse.json()

  // Validate the response structure
  if (!data.agents || !Array.isArray(data.agents)) {
    throw new Error('Invalid agent discovery response: missing agents array')
  }

  // Filter out failed agents and return only successful ones
  const successfulAgents = data.agents.filter(agent => agent.status === 'success')

  return {
    agents: successfulAgents,
    count: successfulAgents.length,
  }
}

/**
 * Gets the default agent from the list of available agents.
 * 
 * @param agents - Array of available agents
 * @returns The default agent, or the first agent if no default is specified
 */
export function getDefaultAgent(agents: Agent[]): Agent | null {
  if (agents.length === 0) {
    return null
  }

  // Find the agent marked as default
  const defaultAgent = agents.find(agent => agent.isDefault)
  
  // Return the default agent, or the first agent if no default is specified
  return defaultAgent || agents[0]
}
