"""
Colorado Agent - A helpful assistant excited about teaching in Denver.

This agent represents a teacher who recently moved to Denver to start a teaching job
at a local elementary school, is beginning a masters in education program, and is
making new friends in a new city - with a cat named Napoleon.

Built with Strands SDK and integrated with AWS Bedrock AgentCore for memory,
authentication, and runtime deployment.
"""

import json
import os
import traceback

import boto3
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

from utils.auth import extract_user_id_from_context

app = BedrockAgentCoreApp()


def create_colorado_agent(user_id: str, session_id: str) -> Agent:
    """
    Create the Colorado agent with memory integration.

    This agent is a conversational assistant with a specific personality: a teacher
    who recently moved to Denver. The agent maintains both short-term conversation
    history and long-term memory (preferences, facts, summaries) shared across all
    agents for the same user.

    Args:
        user_id: The unique identifier for the user (actor_id in memory).
                 Extracted from the validated JWT token for security.
        session_id: The unique identifier for this conversation session.
                    Prefixed with 'colorado_' to distinguish from other agents.

    Returns:
        Agent: Configured Strands agent with personality and memory integration.

    Raises:
        ValueError: If MEMORY_ID environment variable is not set.
    """
    # System prompt defines the agent's personality and behavior
    system_prompt = """You are a helpful AI assistant who is excited about a recent move to Denver to start a teaching job at the local elementary school, is beginning a masters in education program, and is making new friends in a new city - with a cat named Napoleon.

You have access to:
- Short-term memory: Recent conversation history within this session
- Long-term memory: User preferences, important facts, and session summaries across all conversations

When responding:
- Reference relevant information from past conversations when appropriate
- Learn and remember user preferences
- Build on previous context to provide personalized assistance
- Share your enthusiasm about teaching, Denver, your education program, and your cat Napoleon when relevant"""

    # Configure the Bedrock model
    # Using Claude Sonnet 4.5 for best performance and consistency across agents
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        temperature=0.7  # Higher temperature for more conversational, personality-driven responses
    )

    # Get memory ID from environment (set by CDK deployment)
    memory_id = os.environ.get("MEMORY_ID")
    if not memory_id:
        raise ValueError("MEMORY_ID environment variable is required")

    # Configure AgentCore Memory with long-term memory retrieval
    # This agent shares memory with other agents but has its own conversation history
    # The session_id is prefixed with 'colorado_' to distinguish this agent's sessions
    agentcore_memory_config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=f"colorado_{session_id}",  # Unique session prefix per agent
        actor_id=user_id,  # Same user across all agents
        retrieval_config={
            # Retrieve user preferences with high relevance threshold
            "/preferences/{actorId}": RetrievalConfig(
                top_k=5, relevance_score=0.7
            ),
            # Retrieve facts with lower threshold for broader context
            "/facts/{actorId}": RetrievalConfig(
                top_k=10, relevance_score=0.3
            ),
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

    print("[COLORADO AGENT] Creating agent with memory integration...")

    # Create the agent with personality, model, and memory
    agent = Agent(
        name="ColoradoAgent",
        system_prompt=system_prompt,
        tools=[],  # No tools - pure conversational agent
        model=bedrock_model,
        session_manager=session_manager,
        trace_attributes={
            "user.id": user_id,
            "session.id": session_id,
            "agent.type": "colorado",
        },
    )

    print("[COLORADO AGENT] Agent created successfully")
    return agent


@app.entrypoint
async def agent_stream(payload: dict, context: RequestContext):
    """
    Main entrypoint for the Colorado agent using streaming.

    This function is called by AgentCore Runtime when the agent receives a request.
    It extracts the user's query from the payload, securely obtains the user ID from
    the validated JWT token in the request context, creates the Colorado agent with
    memory integration, and streams the response back token-by-token.

    The user ID is extracted from the JWT token (via RequestContext) rather than
    trusting the payload body, which could be manipulated by clients.

    Args:
        payload: Input payload containing:
                 - prompt: The user's query/message
                 - runtimeSessionId: The session identifier
        context: RequestContext containing the validated JWT token with user identity

    Yields:
        dict: Streaming response events from the agent, including:
              - status: Event status
              - data: Response text chunks
              - error: Error message if something fails

    Example payload:
        {
            "prompt": "Tell me about your cat!",
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

        print(
            f"[COLORADO STREAM] Starting streaming invocation for user: {user_id}, session: {session_id}"
        )
        print(f"[COLORADO STREAM] Query: {user_query}")

        # Create the Colorado agent with memory and personality
        agent = create_colorado_agent(user_id=user_id, session_id=session_id)

        # Stream the agent's response token-by-token for better UX
        # The agent will access memory, apply its personality, and generate responses
        async for event in agent.stream_async(user_query):
            # Convert event to JSON-serializable format and yield
            yield json.loads(json.dumps(dict(event), default=str))

    except Exception as e:
        # Log the error with full traceback for debugging
        print(f"[COLORADO STREAM ERROR] Error in agent_stream: {e}")
        traceback.print_exc()

        # Return error to client
        # Following the "fail loudly" principle - don't hide errors
        yield {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # Run the AgentCore app when executed directly
    # This is used by AgentCore Runtime to start the agent service
    app.run()
