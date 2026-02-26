"""
UMich Agent - A helpful assistant who LOVES the University of Michigan.

This agent has access to HTTP requests and current time tools, making it useful
for fetching web content and providing time-based information.

Built with Strands SDK and integrated with AWS Bedrock AgentCore for memory,
authentication, and runtime deployment.

This is part of the multi-agent orchestration pattern where multiple specialist
agents share backend resources (Memory, Gateway, Code Interpreter, Cognito) but
maintain separate conversation histories using session prefixes.
"""

import json
import os
import sys
import traceback

# Add patterns to path for shared utilities
sys.path.append("/app/patterns")

from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)
from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext
from strands import Agent
from strands.models import BedrockModel
from strands_tools import http_request, current_time

# Import shared utilities from patterns/utils
from utils.auth import extract_user_id_from_context

# Import shared tools from pattern-specific tools directory
sys.path.append("/app")

app = BedrockAgentCoreApp()


class UMichSpecialistAgent:
    """
    UMich specialist agent for handling University of Michigan queries.

    This agent loves the University of Michigan and has access to HTTP request
    and current time tools. It shares long-term memory with other agents but
    maintains its own conversation history using the 'umich_' session prefix.
    """

    def __init__(self, user_id: str, base_session_id: str):
        """
        Initialize the UMich specialist agent.

        Args:
            user_id (str): The unique identifier for the user (actor_id in memory).
                          Extracted from the validated JWT token for security.
            base_session_id (str): The base session identifier that will be prefixed
                                  with 'umich_' for this agent's conversation history.
        """
        self.agent_name = "umich"
        self.user_id = user_id
        self.base_session_id = base_session_id

        # Apply inline session prefixing as specified in the design
        self.session_id = f"{self.agent_name}_{base_session_id}"

        # System prompt defines the agent's personality and behavior
        self.system_prompt = """You are a helpful assistant who LOVES the University of Michigan.

You have access to:
- Short-term memory: Recent conversation history within this session
- Long-term memory: User preferences, important facts, and session summaries across all conversations
- Tools:
  - http_request: Make HTTP GET requests to fetch web content
  - current_time: Get the current date and time

When responding:
- Reference relevant information from past conversations when appropriate
- Learn and remember user preferences
- Build on previous context to provide personalized assistance
- Show enthusiasm for the University of Michigan when relevant
- Use your tools when they can help answer questions:
  - Use http_request to fetch web pages, APIs, or online content
  - Use current_time when users ask about the current time or date"""

        # Configure the Bedrock model
        # Using Claude Sonnet 4.5 for best performance and consistency across agents
        self.bedrock_model = BedrockModel(
            model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        )

        # Get memory ID from environment (set by CDK deployment)
        self.memory_id = os.environ.get("MEMORY_ID")
        if not self.memory_id:
            raise ValueError("MEMORY_ID environment variable is required")

        # Configure AgentCore Memory with long-term memory retrieval
        # This agent shares memory with other agents but has its own conversation history
        # The session_id is prefixed with 'umich_' to distinguish this agent's sessions
        self.agentcore_memory_config = AgentCoreMemoryConfig(
            memory_id=self.memory_id,
            session_id=self.session_id,  # Prefixed session ID
            actor_id=user_id,  # Same user across all agents
            retrieval_config={
                # Retrieve user preferences with high relevance threshold
                "/preferences/{actorId}": RetrievalConfig(top_k=5, relevance_score=0.7),
                # Retrieve facts with lower threshold for broader context
                "/facts/{actorId}": RetrievalConfig(top_k=10, relevance_score=0.3),
                # Retrieve session summaries for context from previous conversations
                "/summaries/{actorId}/{sessionId}": RetrievalConfig(
                    top_k=3, relevance_score=0.5
                ),
            },
        )

        # Create session manager for memory integration
        self.session_manager = AgentCoreMemorySessionManager(
            agentcore_memory_config=self.agentcore_memory_config,
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        )

        print(
            f"[UMICH AGENT] Initializing agent for user: {user_id}, session: {self.session_id}"
        )

        # Create the agent with personality, tools, model, and memory
        self.agent = Agent(
            name="UMichAgent",
            system_prompt=self.system_prompt,
            tools=[http_request, current_time],  # HTTP and time tools from strands_tools
            model=self.bedrock_model,
            session_manager=self.session_manager,
            trace_attributes={
                "user.id": user_id,
                "session.id": self.session_id,
                "agent.type": "umich",
            },
        )

        print("[UMICH AGENT] Agent created successfully")

    async def handle_request(self, user_query: str):
        """
        Process incoming request and stream response.

        Args:
            user_query (str): The user's query/message to process.

        Yields:
            dict: Streaming response events from the agent, including:
                  - status: Event status
                  - data: Response text chunks
                  - tool_use: Tool invocation events
                  - error: Error message if something fails
        """
        print(f"[UMICH AGENT] Processing query: {user_query}")

        try:
            # Stream the agent's response token-by-token for better UX
            # The agent will access memory, use tools as needed, and generate responses
            async for event in self.agent.stream_async(user_query):
                # Convert event to JSON-serializable format and yield
                yield json.loads(json.dumps(dict(event), default=str))

        except Exception as e:
            # Log the error with full traceback for debugging
            print(f"[UMICH AGENT ERROR] Error processing request: {e}")
            traceback.print_exc()

            # Return error to client
            # Following the "fail loudly" principle - don't hide errors
            yield {"status": "error", "error": str(e)}


@app.entrypoint
async def agent_stream(payload: dict, context: RequestContext):
    """
    Main entrypoint for the UMich agent using streaming.

    This function is called by AgentCore Runtime when the agent receives a request.
    It extracts the user's query from the payload, securely obtains the user ID from
    the validated JWT token in the request context, creates the UMich agent with
    memory integration and tools, and streams the response back token-by-token.

    The user ID is extracted from the JWT token (via RequestContext) rather than
    trusting the payload body, which could be manipulated by clients.

    Args:
        payload (dict): Input payload containing:
                       - prompt: The user's query/message
                       - runtimeSessionId: The session identifier
        context (RequestContext): RequestContext containing the validated JWT token
                                 with user identity

    Yields:
        dict: Streaming response events from the agent, including:
              - status: Event status
              - data: Response text chunks
              - tool_use: Tool invocation events
              - error: Error message if something fails

    Example payload:
        {
            "prompt": "What time is it?",
            "runtimeSessionId": "session-123"
        }
    """
    # Extract required fields from payload
    user_query = payload.get("prompt")
    base_session_id = payload.get("runtimeSessionId")

    # Validate required fields
    if not all([user_query, base_session_id]):
        yield {
            "status": "error",
            "error": "Missing required fields: prompt or runtimeSessionId",
        }
        return

    try:
        # Extract user ID securely from the validated JWT token
        # This ensures we use the authenticated user's identity, not a potentially
        # manipulated value from the request body
        user_id = extract_user_id_from_context(context)

        print(
            f"[UMICH STREAM] Starting streaming invocation for user: {user_id}, "
            f"base_session: {base_session_id}"
        )
        print(f"[UMICH STREAM] Query: {user_query}")

        # Create the UMich specialist agent with memory, tools, and personality
        umich_agent = UMichSpecialistAgent(
            user_id=user_id, base_session_id=base_session_id
        )

        # Stream the agent's response
        async for event in umich_agent.handle_request(user_query):
            yield event

    except Exception as e:
        # Log the error with full traceback for debugging
        print(f"[UMICH STREAM ERROR] Error in agent_stream: {e}")
        traceback.print_exc()

        # Return error to client
        # Following the "fail loudly" principle - don't hide errors
        yield {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # Run the AgentCore app when executed directly
    # This is used by AgentCore Runtime to start the agent service
    app.run()
