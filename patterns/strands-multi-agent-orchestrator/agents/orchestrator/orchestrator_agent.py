"""
Orchestrator Agent - Routes user queries to appropriate specialist agents.

This agent acts as the central hub in a multi-agent orchestration system,
analyzing user queries and routing them to the most appropriate specialist
agent (Colorado, UMich, or Coder). The orchestrator can invoke specialists
as tools and include their responses in its own response.

Built with Strands SDK and integrated with AWS Bedrock AgentCore for memory,
authentication, and runtime deployment.
"""

import json
import os
import sys
import traceback

from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)
from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# Add patterns to path for shared utils
sys.path.append("/app/patterns")

from utils.auth import extract_user_id_from_context, get_gateway_access_token
from utils.ssm import get_ssm_parameter

# Import specialist invocation tools
sys.path.append("/app")
from tools.invoke_specialist import SpecialistInvocationTools

app = BedrockAgentCoreApp()

@tool
def tap():
    return 11

def create_gateway_mcp_client(access_token: str) -> MCPClient:
    """
    Create MCP client for AgentCore Gateway with OAuth2 authentication.

    MCP (Model Context Protocol) is how agents communicate with tool providers.
    This creates a client that can talk to the AgentCore Gateway using the provided
    access token for authentication. The Gateway then provides access to Lambda-based tools.

    Args:
        access_token (str): OAuth2 access token for Gateway authentication.

    Returns:
        MCPClient: Configured MCP client for Gateway tool access.

    Raises:
        ValueError: If STACK_NAME environment variable is not set or has invalid format.
    """
    stack_name = os.environ.get("STACK_NAME")
    if not stack_name:
        raise ValueError("STACK_NAME environment variable is required")

    # Validate stack name format to prevent injection
    if not stack_name.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Invalid STACK_NAME format")

    print(f"[ORCHESTRATOR] Creating Gateway MCP client for stack: {stack_name}")

    # Fetch Gateway URL from SSM
    gateway_url = get_ssm_parameter(f"/{stack_name}/gateway_url")
    print(f"[ORCHESTRATOR] Gateway URL from SSM: {gateway_url}")

    # Create MCP client with Bearer token authentication
    gateway_client = MCPClient(
        lambda: streamablehttp_client(
            url=gateway_url, headers={"Authorization": f"Bearer {access_token}"}
        ),
        prefix="gateway",
    )

    print("[ORCHESTRATOR] Gateway MCP client created successfully")
    return gateway_client


def create_orchestrator_agent(user_id: str, session_id: str, user_jwt_token: str) -> Agent:
    """
    Create the orchestrator agent with specialist invocation tools and memory integration.

    This agent analyzes user queries and routes them to appropriate specialist agents.
    It has access to:
    - Gateway MCP tools for general functionality
    - Specialist invocation tools (Colorado, UMich, Coder)
    - Short-term conversation history (session-specific)
    - Long-term memory shared across all agents (preferences, facts, summaries)

    The orchestrator maintains the same actor_id when calling specialists to ensure
    shared long-term memory, but uses agent-specific session IDs to maintain separate
    conversation histories.

    Args:
        user_id (str): The unique identifier for the user (actor_id in memory).
                       Extracted from the validated JWT token for security.
        session_id (str): The unique identifier for this conversation session.
                          Will be prefixed with 'orchestrator_' to distinguish from specialists.
        user_jwt_token (str): The user's JWT token from Cognito authentication.
                              Used for authenticating requests to specialist agents.

    Returns:
        Agent: Configured Strands agent with routing capabilities and memory integration.

    Raises:
        ValueError: If MEMORY_ID environment variable is not set.
        RuntimeError: If Gateway connection fails or agent creation fails.
    """
    # System prompt defines the orchestrator's role and routing logic
    system_prompt = """You are an orchestrator agent that routes user queries to appropriate specialist agents.

You have access to three specialist agents:
1. Colorado Agent - A teacher who moved to Denver, excited about teaching, education program, and cat Napoleon
2. UMich Agent - Specialized for University of Michigan queries and information
3. Coder Agent - Specialized for coding assistance and technical queries

You also have access to:
- Gateway tools for general functionality
- Short-term memory: Recent conversation history within this session
- Long-term memory: User preferences, important facts, and session summaries across all conversations

When responding:
- Analyze the user's query to determine if it should be routed to a specialist
- If the query is about Colorado/Denver/teaching/education, invoke the Colorado agent
- If the query is about University of Michigan, invoke the UMich agent
- If the query is about coding/programming/technical topics, invoke the Coder agent
- For general queries, respond directly using your own capabilities
- Include specialist responses in your response when you invoke them
- Reference relevant information from past conversations when appropriate
- Learn and remember user preferences

When you invoke a specialist:
- Pass the user's query to the specialist
- The specialist will have access to the same user's long-term memory
- Include the specialist's response in your own response
- You can add context or clarification around the specialist's response"""

    # Configure the Bedrock model
    # Using Claude Sonnet 4.5 for best performance and consistency across agents
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        temperature=0.1,  # Lower temperature for more consistent routing decisions
    )

    # Get memory ID from environment (set by CDK deployment)
    memory_id = os.environ.get("MEMORY_ID")
    if not memory_id:
        raise ValueError("MEMORY_ID environment variable is required")

    # Configure AgentCore Memory with long-term memory retrieval
    # Session prefixing is done inline using string concatenation
    prefixed_session_id = f"orchestrator_{session_id}"

    agentcore_memory_config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=prefixed_session_id,  # Unique session prefix for orchestrator
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
    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=agentcore_memory_config,
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )

    try:
        print(
            "[ORCHESTRATOR] Starting agent creation with Gateway tools and specialists..."
        )

        # Get OAuth2 access token and create Gateway MCP client
        print("[ORCHESTRATOR] Step 1: Getting OAuth2 access token...")
        access_token = get_gateway_access_token()
        print(f"[ORCHESTRATOR] Got access token: {access_token[:20]}...")

        # Create Gateway MCP client with authentication
        print("[ORCHESTRATOR] Step 2: Creating Gateway MCP client...")
        gateway_client = create_gateway_mcp_client(access_token)
        print("[ORCHESTRATOR] Gateway MCP client created successfully")

        # Create bound versions of specialist invocation tools with session_id and actor_id
        # The LLM will only need to provide the 'query' parameter
        print("[ORCHESTRATOR] Step 3: Creating specialist invocation tools...")
        specialist_tools = SpecialistInvocationTools(
            session_id=session_id,
            actor_id=user_id,
            access_token=user_jwt_token  # Pass user's JWT token for specialist authentication
        )

        print("[ORCHESTRATOR] Step 4: Creating Agent with all tools...")

        # Create the agent with all tools:
        # - Gateway MCP client for general tools
        # - Specialist invocation tools (Colorado, UMich, Coder)
        agent = Agent(
            name="OrchestratorAgent",
            system_prompt=system_prompt,
            tools=[
                gateway_client,
                specialist_tools.invoke_colorado,
                specialist_tools.invoke_umich,
                specialist_tools.invoke_coder,
                tap,
            ],
            model=bedrock_model,
            session_manager=session_manager,
            trace_attributes={
                "user.id": user_id,
                "session.id": session_id,
                "agent.type": "orchestrator",
            },
        )

        print("[ORCHESTRATOR] Agent created successfully with all tools")
        return agent

    except Exception as e:
        print(f"[ORCHESTRATOR ERROR] Error creating agent: {e}")
        print(f"[ORCHESTRATOR ERROR] Exception type: {type(e).__name__}")
        print("[ORCHESTRATOR ERROR] Traceback:")
        traceback.print_exc()
        print("[ORCHESTRATOR] Raising exception - agent creation failed")
        raise


@app.entrypoint
async def agent_stream(payload: dict, context: RequestContext):
    """
    Main entrypoint for the orchestrator agent using streaming.

    This function is called by AgentCore Runtime when the agent receives a request.
    It extracts the user's query from the payload, securely obtains the user ID from
    the validated JWT token in the request context, creates the orchestrator agent with
    routing capabilities and memory integration, and streams the response back token-by-token.

    The orchestrator analyzes the query and may:
    - Route it to a specialist agent (Colorado, UMich, Coder)
    - Respond directly using its own capabilities
    - Use Gateway tools

    When invoking specialists, the orchestrator:
    - Maintains the same actor_id for shared long-term memory
    - Uses the base session_id (specialists apply their own prefixes)
    - Includes specialist responses in its own response

    The user ID is extracted from the JWT token (via RequestContext) rather than
    trusting the payload body, which could be manipulated by clients.

    Args:
        payload (dict): Input payload containing:
                        - prompt: The user's query/message
                        - runtimeSessionId: The session identifier
        context (RequestContext): RequestContext containing the validated JWT token with user identity

    Yields:
        dict: Streaming response events from the agent, including:
              - status: Event status
              - data: Response text chunks
              - error: Error message if something fails

    Example payload:
        {
            "prompt": "Tell me about coding in Python",
            "runtimeSessionId": "session-123"
        }
    """
    # Extract required fields from payload
    user_query = payload.get("prompt")
    session_id = payload.get("runtimeSessionId")

    # Validate required fields
    if not all([user_query, session_id]):
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

        # Extract the JWT token itself for passing to specialist agents
        # Specialist agents are configured with JWT (Cognito) authorization and need the user's token
        auth_header = context.request_headers.get("Authorization", "")
        user_jwt_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header

        print(
            f"[ORCHESTRATOR STREAM] Starting streaming invocation for user: {user_id}, session: {session_id}"
        )
        print(f"[ORCHESTRATOR STREAM] Query: {user_query}")

        # Create the orchestrator agent with routing capabilities and memory
        agent = create_orchestrator_agent(
            user_id=user_id, 
            session_id=session_id,
            user_jwt_token=user_jwt_token
        )

        # Stream the agent's response token-by-token for better UX
        # The agent will:
        # - Analyze the query
        # - Route to specialists if appropriate
        # - Access memory for context
        # - Generate responses
        async for event in agent.stream_async(user_query):
            # Convert event to JSON-serializable format and yield
            yield json.loads(json.dumps(dict(event), default=str))

    except Exception as e:
        # Log the error with full traceback for debugging
        print(f"[ORCHESTRATOR STREAM ERROR] Error in agent_stream: {e}")
        traceback.print_exc()

        # Return error to client
        # Following the "fail loudly" principle - don't hide errors
        yield {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # Run the AgentCore app when executed directly
    # This is used by AgentCore Runtime to start the agent service
    app.run()
