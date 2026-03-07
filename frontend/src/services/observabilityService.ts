/**
 * Observability Service
 * Handles fetching session data, metrics, and traces from the backend Observability API
 */

/**
 * Span interface representing a single trace span.
 */
export interface Span {
  spanId: string
  parentSpanId: string | null
  name: string
  spanType: 'agent_invocation' | 'llm_invocation' | 'tool_call' | 'unknown'
  startTime: number
  endTime: number
  duration: number
  status: 'ok' | 'error'
  attributes: Record<string, any>
}

/**
 * Trace interface representing a complete trace with all spans.
 */
export interface Trace {
  traceId: string
  sessionId: string
  spans: Span[]
  startTime: number
  endTime: number
  duration: number
}

/**
 * Response from the Traces API.
 */
export interface TraceResponse {
  trace: Trace
}

/**
 * Session interface representing a single agent session.
 */
export interface Session {
  sessionId: string
  agentName: string  // Internal agent name (e.g., "umich", "coder") - used for filtering
  agentDisplayName: string  // Display name (e.g., "UMich Specialist", "Coder Agent") - used for UI
  agentId: string | null
  startTime: number
  endTime: number
  duration: number
  status: 'completed' | 'failed' | 'in-progress'
  spanCount: number
}

/**
 * Response from the Sessions API.
 */
export interface SessionsResponse {
  sessions: Session[]
  count: number
  nextToken?: string
}

/**
 * Filter options for fetching sessions.
 */
export interface SessionFilters {
  agentName?: string
  startTime?: number
  endTime?: number
  limit?: number
  nextToken?: string
}

/**
 * Metrics interface representing aggregated observability metrics.
 */
export interface Metrics {
  totalSessions: number
  avgDuration: number
  successRate: number
  totalInputTokens: number
  totalOutputTokens: number
  totalTokens: number
  agentBreakdown: AgentMetrics[]
  topTools: ToolUsage[]
}

/**
 * Per-agent metrics breakdown.
 */
export interface AgentMetrics {
  agentName: string
  sessionCount: number
  avgDuration: number
  successRate: number
  inputTokens: number
  outputTokens: number
  totalTokens: number
}

/**
 * Tool usage statistics.
 */
export interface ToolUsage {
  toolName: string
  usageCount: number
}

/**
 * Response from the Metrics API.
 */
export interface MetricsResponse {
  metrics: Metrics
  timeRange: number
  startTime: number
  endTime: number
}

// API URLs loaded from aws-exports.json
let SESSIONS_API_URL = ""
let METRICS_API_URL = ""
let TRACES_API_URL = ""

/**
 * Dynamically load API URLs from aws-exports.json
 */
async function loadApiUrls(): Promise<{ sessionsUrl: string; metricsUrl: string; tracesUrl: string }> {
  if (SESSIONS_API_URL && METRICS_API_URL && TRACES_API_URL) {
    return { sessionsUrl: SESSIONS_API_URL, metricsUrl: METRICS_API_URL, tracesUrl: TRACES_API_URL }
  }

  try {
    const response = await fetch("/aws-exports.json")
    const config = await response.json()
    
    SESSIONS_API_URL = config.observabilitySessionsApiUrl || ""
    METRICS_API_URL = config.observabilityMetricsApiUrl || ""
    TRACES_API_URL = config.observabilityTracesApiUrl || ""
    
    return { sessionsUrl: SESSIONS_API_URL, metricsUrl: METRICS_API_URL, tracesUrl: TRACES_API_URL }
  } catch (error) {
    console.error("Failed to load API URLs from aws-exports.json:", error)
    throw new Error("Observability API URLs not configured")
  }
}

/**
 * Fetches sessions from the Sessions API with optional filters.
 * 
 * @param idToken - JWT ID token for authentication
 * @param filters - Optional filters for the query
 * @returns Promise resolving to the sessions response
 * @throws Error if the API request fails or returns invalid data
 */
export async function fetchSessions(
  idToken: string,
  filters?: SessionFilters
): Promise<SessionsResponse> {
  if (!idToken) {
    throw new Error('ID token is required for fetching sessions')
  }

  const { sessionsUrl } = await loadApiUrls()
  
  if (!sessionsUrl) {
    throw new Error('Sessions API URL not found in configuration')
  }

  // Build query parameters
  const queryParams = new URLSearchParams()
  
  if (filters?.agentName) {
    queryParams.append('agentName', filters.agentName)
  }
  
  if (filters?.startTime) {
    queryParams.append('startTime', filters.startTime.toString())
  }
  
  if (filters?.endTime) {
    queryParams.append('endTime', filters.endTime.toString())
  }
  
  if (filters?.limit) {
    queryParams.append('limit', filters.limit.toString())
  }
  
  if (filters?.nextToken) {
    queryParams.append('nextToken', filters.nextToken)
  }

  // Build full URL with query parameters
  const url = queryParams.toString() 
    ? `${sessionsUrl}?${queryParams.toString()}`
    : sessionsUrl

  // Call the Sessions API
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${idToken}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Failed to fetch sessions: HTTP ${response.status}: ${errorText}`)
  }

  const data: SessionsResponse = await response.json()

  // Validate the response structure
  if (!data.sessions || !Array.isArray(data.sessions)) {
    throw new Error('Invalid sessions response: missing sessions array')
  }

  return data
}

/**
 * Fetches aggregated metrics from the Metrics API.
 * 
 * @param idToken - JWT ID token for authentication
 * @param timeRange - Time range in hours (1, 24, 168, or 720)
 * @returns Promise resolving to the metrics response
 * @throws Error if the API request fails or returns invalid data
 */
export async function fetchMetrics(
  idToken: string,
  timeRange: number = 24
): Promise<MetricsResponse> {
  if (!idToken) {
    throw new Error('ID token is required for fetching metrics')
  }

  const { metricsUrl } = await loadApiUrls()
  
  if (!metricsUrl) {
    throw new Error('Metrics API URL not found in configuration')
  }

  // Build query parameters
  const queryParams = new URLSearchParams()
  queryParams.append('timeRange', timeRange.toString())

  // Build full URL with query parameters
  const url = `${metricsUrl}?${queryParams.toString()}`

  // Call the Metrics API
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${idToken}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Failed to fetch metrics: HTTP ${response.status}: ${errorText}`)
  }

  const data: MetricsResponse = await response.json()

  // Validate the response structure
  if (!data.metrics) {
    throw new Error('Invalid metrics response: missing metrics object')
  }

  return data
}

/**
 * Fetches trace data for a specific session from the Traces API.
 * 
 * @param idToken - JWT ID token for authentication
 * @param sessionId - Session ID to fetch traces for
 * @returns Promise resolving to the trace response
 * @throws Error if the API request fails or returns invalid data
 */
export async function fetchTraces(
  idToken: string,
  sessionId: string
): Promise<TraceResponse> {
  if (!idToken) {
    throw new Error('ID token is required for fetching traces')
  }

  if (!sessionId) {
    throw new Error('Session ID is required for fetching traces')
  }

  const { tracesUrl } = await loadApiUrls()
  
  if (!tracesUrl) {
    throw new Error('Traces API URL not found in configuration')
  }

  // Build full URL with session ID
  const url = `${tracesUrl}/${sessionId}`

  // Call the Traces API
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${idToken}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Failed to fetch traces: HTTP ${response.status}: ${errorText}`)
  }

  const data: TraceResponse = await response.json()

  // Validate the response structure
  if (!data.trace || !data.trace.spans || !Array.isArray(data.trace.spans)) {
    throw new Error('Invalid trace response: missing trace or spans array')
  }

  return data
}
