/**
 * Service for fetching agent memories from the backend Memory API.
 * 
 * This service fetches memory records from the Memory API endpoint,
 * which returns memories from AgentCore Memory including summaries,
 * preferences, facts, and conversation events.
 */

/**
 * Memory record interface representing a single memory item.
 * 
 * @property id - Unique identifier (recordId or eventId)
 * @property type - Memory type: "summary", "preference", "fact", or "event"
 * @property content - Memory content text
 * @property timestamp - ISO 8601 timestamp
 * @property userId - User identifier (actorId)
 * @property sessionId - Session identifier (optional)
 * @property agentName - Agent name (optional)
 */
export interface Memory {
  id: string
  type: 'summary' | 'preference' | 'fact' | 'event'
  content: string
  timestamp: string
  userId: string
  sessionId?: string
  agentName?: string
}

/**
 * Response from the Memory API.
 * 
 * @property memories - Array of memory records
 * @property count - Number of memories returned
 * @property nextToken - Pagination token for next page (optional)
 */
export interface MemoryResponse {
  memories: Memory[]
  count: number
  nextToken?: string
}

/**
 * Filter options for fetching memories.
 * 
 * @property agentName - Filter by agent name (optional)
 * @property userId - Filter by user ID (optional)
 * @property sortOrder - Sort order: "asc" or "desc" (optional, default: "desc")
 * @property limit - Maximum results per page (optional, default: 50, max: 100)
 * @property nextToken - Pagination token (optional)
 */
export interface MemoryFilters {
  agentName?: string
  userId?: string
  sortOrder?: 'asc' | 'desc'
  limit?: number
  nextToken?: string
}

/**
 * Fetches memories from the Memory API with optional filters.
 * 
 * @param idToken - JWT ID token for authentication
 * @param filters - Optional filters for the query
 * @returns Promise resolving to the memory response
 * @throws Error if the API request fails or returns invalid data
 */
export async function fetchMemories(
  idToken: string,
  filters?: MemoryFilters
): Promise<MemoryResponse> {
  if (!idToken) {
    throw new Error('ID token is required for fetching memories')
  }

  // Load the API URL from aws-exports.json
  const response = await fetch('/aws-exports.json')
  if (!response.ok) {
    throw new Error('Failed to load configuration')
  }
  
  const config = await response.json()
  const memoryApiUrl = config.memoryApiUrl
  
  if (!memoryApiUrl) {
    throw new Error('Memory API URL not found in configuration')
  }

  // Build query parameters
  const queryParams = new URLSearchParams()
  
  if (filters?.agentName) {
    queryParams.append('agentName', filters.agentName)
  }
  
  if (filters?.userId) {
    queryParams.append('userId', filters.userId)
  }
  
  if (filters?.sortOrder) {
    queryParams.append('sortOrder', filters.sortOrder)
  }
  
  if (filters?.limit) {
    queryParams.append('limit', filters.limit.toString())
  }
  
  if (filters?.nextToken) {
    queryParams.append('nextToken', filters.nextToken)
  }

  // Build full URL with query parameters
  const url = queryParams.toString() 
    ? `${memoryApiUrl}?${queryParams.toString()}`
    : memoryApiUrl

  // Call the Memory API
  const memoryResponse = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${idToken}`,
      'Content-Type': 'application/json',
    },
  })

  if (!memoryResponse.ok) {
    const errorText = await memoryResponse.text()
    throw new Error(`Failed to fetch memories: HTTP ${memoryResponse.status}: ${errorText}`)
  }

  const data: MemoryResponse = await memoryResponse.json()

  // Validate the response structure
  if (!data.memories || !Array.isArray(data.memories)) {
    throw new Error('Invalid memory response: missing memories array')
  }

  return data
}
