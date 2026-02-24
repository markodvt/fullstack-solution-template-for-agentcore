"""A helpful assistant who LOVES the University of Michigan.

This agent has access to HTTP requests and current time tools.

Built with Strands SDK - a lightweight framework for building AI agents.

To use this agent in your code:
    from agents.umich_agent_agentcore import umich_agent
    response = umich_agent("Your message here")

To test interactively, run this file directly:
    python agents/umich_agent_agentcore.py
"""

from strands import Agent
from strands.models import BedrockModel

from strands_tools import http_request, current_time

try:
    from console_chat import console_chat
except ImportError:
    console_chat = None

# Agent description
DESCRIPTION = """A helpful assistant who LOVES the University of Michigan. Has access to HTTP requests and current time tools."""

# System prompt for the agent
SYSTEM_PROMPT = """You are a helpful assistant who LOVES the University of Michigan."""

# Configure the model
model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0")

# Create the agent
# The agent variable name matches the filename for easy imports
umich_agent = Agent(
    name="umich_agent",
    description=DESCRIPTION,
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[http_request, current_time]
)

# AgentCore entrypoint
# This code is required for AgentCore deployment
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
async def agent_invocation(payload):
    """
    Handler for agent invocation.
    
    Args:
        payload: Input payload from AgentCore invocation
    
    Yields:
        Agent response events
    """
    # Extract user message from payload
    user_message = payload.get(
        "prompt",
        payload.get("message", "No prompt found in input")
    )
    
    # Stream agent response
    stream = umich_agent.stream_async(user_message)
    async for event in stream:
        yield event

# Standalone testing (local only)
if __name__ == "__main__":
    if console_chat:
        # Use console_chat for local testing
        console_chat(umich_agent, description=DESCRIPTION)
    else:
        # Use AgentCore app for testing
        app.run()
