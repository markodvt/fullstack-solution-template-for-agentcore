"use client"

import { useEffect, useRef, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { ChatHeader } from "./ChatHeader"
import { ChatInput } from "./ChatInput"
import { ChatMessages } from "./ChatMessages"
import { Message, MessageSegment, ToolCall } from "./types"

import { useGlobal } from "@/app/context/GlobalContext"
import { AgentCoreClient } from "@/lib/agentcore-client"
import type { AgentPattern } from "@/lib/agentcore-client"
import { submitFeedback } from "@/services/feedbackService"
import { useAuth } from "react-oidc-context"
import { useDefaultTool } from "@/hooks/useToolRenderer"
import { ToolCallDisplay } from "./ToolCallDisplay"
import { discoverAgents, getDefaultAgent, type Agent } from "@/services/agentDiscoveryService"

/**
 * Main chat interface component with multi-agent support.
 * 
 * This component manages:
 * - Agent discovery and selection
 * - Separate conversation histories per agent
 * - Session management per agent
 * - AgentCore client initialization and updates
 */
export default function ChatInterface() {
  // URL query parameters for agent selection
  const [searchParams, setSearchParams] = useSearchParams()
  
  // Agent management state
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [agentDiscoveryError, setAgentDiscoveryError] = useState<string | null>(null)

  // Conversation state per agent
  const [conversationHistories, setConversationHistories] = useState<Map<string, Message[]>>(new Map())
  const [sessionIds, setSessionIds] = useState<Map<string, string>>(new Map())

  // Current conversation state
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [client, setClient] = useState<AgentCoreClient | null>(null)

  const { isLoading, setIsLoading } = useGlobal()
  const auth = useAuth()

  // Ref for message container to enable auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Register default tool renderer (wildcard "*")
  useDefaultTool(({ name, args, status, result }) => (
    <ToolCallDisplay name={name} args={args} status={status} result={result} />
  ))

  /**
   * Get or create a session ID for the specified agent.
   * Session IDs are persisted in localStorage and the sessionIds state map.
   * 
   * @param agentName - Name of the agent
   * @returns Session ID for the agent
   */
  const getSessionIdForAgent = (agentName: string): string => {
    // Check if we already have a session ID for this agent
    if (sessionIds.has(agentName)) {
      return sessionIds.get(agentName)!
    }

    // Try to load from localStorage
    const storedSessionIds = localStorage.getItem('agentSessionIds')
    if (storedSessionIds) {
      try {
        const parsed = JSON.parse(storedSessionIds)
        if (parsed[agentName]) {
          sessionIds.set(agentName, parsed[agentName])
          return parsed[agentName]
        }
      } catch (err) {
        console.error('Failed to parse stored session IDs:', err)
      }
    }

    // Generate new session ID
    const newSessionId = crypto.randomUUID()
    sessionIds.set(agentName, newSessionId)

    // Persist to localStorage
    const allSessionIds: Record<string, string> = {}
    sessionIds.forEach((id, name) => {
      allSessionIds[name] = id
    })
    localStorage.setItem('agentSessionIds', JSON.stringify(allSessionIds))

    return newSessionId
  }

  /**
   * Initialize AgentCore client for the selected agent.
   * 
   * @param agent - Agent to initialize client for
   */
  const initializeClientForAgent = async (agent: Agent) => {
    try {
      // Load configuration for pattern and region
      const response = await fetch("/aws-exports.json")
      if (!response.ok) {
        throw new Error("Failed to load configuration")
      }
      const config = await response.json()

      // Create client with selected agent's runtime ARN
      const agentClient = new AgentCoreClient({
        runtimeArn: agent.runtimeArn,
        region: config.awsRegion || "us-east-1",
        pattern: agent.pattern as AgentPattern,
      })

      setClient(agentClient)
      setError(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error"
      setError(`Failed to initialize agent client: ${errorMessage}`)
      console.error("Failed to initialize agent client:", err)
    }
  }

  /**
   * Handle agent selection change.
   * Saves current conversation, loads new agent's conversation, updates client, and updates URL.
   * 
   * @param agent - Newly selected agent
   */
  const handleAgentChange = async (agent: Agent) => {
    if (!agent || agent.name === selectedAgent?.name) {
      return
    }

    // Save current conversation to history map
    if (selectedAgent) {
      conversationHistories.set(selectedAgent.name, [...messages])
      setConversationHistories(new Map(conversationHistories))
    }

    // Load conversation history for new agent
    const agentHistory = conversationHistories.get(agent.name) || []
    setMessages(agentHistory)

    // Update selected agent
    setSelectedAgent(agent)
    localStorage.setItem('selectedAgentName', agent.name)

    // Update URL query parameter
    setSearchParams({ agent: agent.name })

    // Initialize client for new agent
    await initializeClientForAgent(agent)

    // Clear any errors
    setError(null)
  }

  // Discover agents and initialize on mount
  useEffect(() => {
    async function discoverAndInitialize() {
      try {
        // Wait for authentication
        if (!auth.isAuthenticated || !auth.user?.id_token) {
          return
        }

        // Discover available agents
        const discoveryResult = await discoverAgents(auth.user.id_token)

        if (discoveryResult.agents.length === 0) {
          setAgentDiscoveryError('No agents available. Please contact your administrator.')
          return
        }

        setAgents(discoveryResult.agents)

        // Determine which agent to select (priority order):
        // 1. URL query parameter (?agent=name)
        // 2. localStorage (previously selected agent)
        // 3. Default agent
        const urlAgentName = searchParams.get('agent')
        let agentToSelect: Agent | null = null

        // First, try URL query parameter
        if (urlAgentName) {
          agentToSelect = discoveryResult.agents.find(a => a.name === urlAgentName) || null
          if (!agentToSelect) {
            console.warn(`Agent "${urlAgentName}" from URL not found, falling back to default`)
          }
        }

        // Second, try localStorage
        if (!agentToSelect) {
          const storedAgentName = localStorage.getItem('selectedAgentName')
          if (storedAgentName) {
            agentToSelect = discoveryResult.agents.find(a => a.name === storedAgentName) || null
          }
        }

        // Third, use default agent
        if (!agentToSelect) {
          agentToSelect = getDefaultAgent(discoveryResult.agents)
        }

        if (agentToSelect) {
          setSelectedAgent(agentToSelect)
          localStorage.setItem('selectedAgentName', agentToSelect.name)
          
          // Update URL to reflect selected agent
          setSearchParams({ agent: agentToSelect.name }, { replace: true })
          
          await initializeClientForAgent(agentToSelect)
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unknown error"
        setAgentDiscoveryError(`Failed to discover agents: ${errorMessage}`)
        console.error("Failed to discover agents:", err)

        // Fall back to single-agent mode using aws-exports.json
        try {
          const response = await fetch("/aws-exports.json")
          if (!response.ok) {
            throw new Error("Failed to load configuration")
          }
          const config = await response.json()

          if (config.agentRuntimeArn) {
            const fallbackAgent: Agent = {
              name: 'default',
              displayName: 'Default Agent',
              description: 'Fallback agent from configuration',
              runtimeArn: config.agentRuntimeArn,
              runtimeId: 'default',
              pattern: 'basic',
              isDefault: true,
              status: 'success',
            }

            setAgents([fallbackAgent])
            setSelectedAgent(fallbackAgent)
            await initializeClientForAgent(fallbackAgent)
            setAgentDiscoveryError(null)
          }
        } catch (fallbackErr) {
          console.error("Fallback to single-agent mode failed:", fallbackErr)
        }
      }
    }

    discoverAndInitialize()
  }, [auth.isAuthenticated, auth.user?.access_token, searchParams, setSearchParams])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const sendMessage = async (userMessage: string) => {
    if (!userMessage.trim() || !client || !selectedAgent) return

    // Get session ID for current agent
    const sessionId = getSessionIdForAgent(selectedAgent.name)

    // Clear any previous errors
    setError(null)

    // Add user message to chat
    const newUserMessage: Message = {
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, newUserMessage])
    setInput("")
    setIsLoading(true)

    // Create placeholder for assistant response
    const assistantResponse: Message = {
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, assistantResponse])

    try {
      // Get auth token from react-oidc-context
      const accessToken = auth.user?.access_token

      if (!accessToken) {
        throw new Error("Authentication required. Please log in again.")
      }

      const segments: MessageSegment[] = [];
      const toolCallMap = new Map<string, ToolCall>();

      const updateMessage = () => {
        // Build content from text segments for backward compat
        const content = segments
          .filter((s): s is Extract<MessageSegment, { type: "text" }> => s.type === "text")
          .map((s) => s.content)
          .join("");

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content,
            segments: [...segments],
          };
          return updated;
        });
      };

      // User identity is extracted server-side from the validated JWT token,
      // not passed as a parameter — prevents impersonation via prompt injection.
      await client.invoke(
        userMessage,
        sessionId,
        accessToken,
        (event) => {
          switch (event.type) {
            case "text": {
              // If text arrives after a tool segment, mark all pending tools as complete
              const prev = segments[segments.length - 1];
              if (prev && prev.type === "tool") {
                for (const tc of toolCallMap.values()) {
                  if (tc.status === "streaming" || tc.status === "executing") {
                    tc.status = "complete";
                  }
                }
              }
              // Append to last text segment, or create new one
              const last = segments[segments.length - 1];
              if (last && last.type === "text") {
                last.content += event.content;
              } else {
                segments.push({ type: "text", content: event.content });
              }
              updateMessage();
              break;
            }
            case "tool_use_start": {
              const tc: ToolCall = {
                toolUseId: event.toolUseId,
                name: event.name,
                input: "",
                status: "streaming",
              };
              toolCallMap.set(event.toolUseId, tc);
              segments.push({ type: "tool", toolCall: tc });
              updateMessage();
              break;
            }
            case "tool_use_delta": {
              const tc = toolCallMap.get(event.toolUseId);
              if (tc) {
                tc.input += event.input;
              }
              updateMessage();
              break;
            }
            case "tool_result": {
              const tc = toolCallMap.get(event.toolUseId);
              if (tc) {
                tc.result = event.result;
                tc.status = "complete";
              }
              updateMessage();
              break;
            }
            case "message": {
              if (event.role === "assistant") {
                for (const tc of toolCallMap.values()) {
                  if (tc.status === "streaming") tc.status = "executing";
                }
                updateMessage();
              }
              break;
            }
          }
        }
      )
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error"
      setError(`Failed to get response: ${errorMessage}`)
      console.error("Error invoking AgentCore:", err)

      // Update the assistant message with error
      setMessages((prev) => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content:
            "I apologize, but I encountered an error processing your request. Please try again.",
        }
        return updated
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    sendMessage(input)
  }

  // Handle feedback submission
  const handleFeedbackSubmit = async (
    messageContent: string,
    feedbackType: "positive" | "negative",
    comment: string
  ) => {
    if (!selectedAgent) return

    try {
      // Use ID token for API Gateway Cognito authorizer (not access token)
      const idToken = auth.user?.id_token

      if (!idToken) {
        throw new Error("Authentication required. Please log in again.")
      }

      // Get session ID for current agent
      const sessionId = getSessionIdForAgent(selectedAgent.name)

      await submitFeedback(
        {
          sessionId,
          message: messageContent,
          feedbackType,
          comment: comment || undefined,
        },
        idToken
      )

      console.log("Feedback submitted successfully")
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error"
      console.error("Error submitting feedback:", err)
      setError(`Failed to submit feedback: ${errorMessage}`)
    }
  }

  // Start a new chat (clears current agent's conversation history)
  const startNewChat = () => {
    if (!selectedAgent) return

    // Clear current messages
    setMessages([])
    setInput("")
    setError(null)

    // Remove from conversation histories
    conversationHistories.delete(selectedAgent.name)
    setConversationHistories(new Map(conversationHistories))

    // Generate new session ID for this agent
    const newSessionId = crypto.randomUUID()
    sessionIds.set(selectedAgent.name, newSessionId)
    setSessionIds(new Map(sessionIds))

    // Update localStorage
    const allSessionIds: Record<string, string> = {}
    sessionIds.forEach((id, name) => {
      allSessionIds[name] = id
    })
    localStorage.setItem('agentSessionIds', JSON.stringify(allSessionIds))
  }

  // Check if this is the initial state (no messages)
  const isInitialState = messages.length === 0

  // Check if there are any assistant messages
  const hasAssistantMessages = messages.some((message) => message.role === "assistant")

  return (
    <div className="flex flex-col h-screen w-full">
      {/* Fixed header */}
      <div className="flex-none">
        <ChatHeader
          onNewChat={startNewChat}
          canStartNewChat={hasAssistantMessages}
          agents={agents}
          selectedAgent={selectedAgent}
          onAgentChange={handleAgentChange}
          agentSelectorDisabled={isLoading}
        />
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mx-4 mt-2">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
        {agentDiscoveryError && (
          <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 mx-4 mt-2">
            <p className="text-sm text-yellow-700">{agentDiscoveryError}</p>
          </div>
        )}
      </div>

      {/* Conditional layout based on whether there are messages */}
      {isInitialState ? (
        // Initial state - input in the middle
        <>
          {/* Empty space above */}
          <div className="grow" />

          {/* Centered welcome message */}
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Welcome to FAST Chat</h2>
            <p className="text-gray-600 mt-2">Ask me anything to get started</p>
          </div>

          {/* Centered input */}
          <div className="px-4 mb-16 max-w-4xl mx-auto w-full">
            <ChatInput
              input={input}
              setInput={setInput}
              handleSubmit={handleSubmit}
              isLoading={isLoading}
            />
          </div>

          {/* Empty space below */}
          <div className="grow" />
        </>
      ) : (
        // Chat in progress - normal layout
        <>
          {/* Scrollable message area */}
          <div className="grow overflow-hidden">
            <div className="max-w-4xl mx-auto w-full h-full">
              <ChatMessages
                messages={messages}
                messagesEndRef={messagesEndRef}
                sessionId={selectedAgent ? getSessionIdForAgent(selectedAgent.name) : ''}
                onFeedbackSubmit={handleFeedbackSubmit}
              />
            </div>
          </div>

          {/* Fixed input area at bottom */}
          <div className="flex-none">
            <div className="max-w-4xl mx-auto w-full">
              <ChatInput
                input={input}
                setInput={setInput}
                handleSubmit={handleSubmit}
                isLoading={isLoading}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
