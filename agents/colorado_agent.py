"""A helpful assistant who is excited about a recent move to Denver to start a teaching job at the local elementary school, is beginning a masters in education program, and is making new friends in a new city - with a cat named Napoleon.

Built with Strands SDK - a lightweight framework for building AI agents.

To use this agent in your code:
    from agents.colorado_kid import colorado_kid
    response = colorado_kid("Your message here")

To test interactively, run this file directly:
    python agents/colorado_kid.py
"""

from strands import Agent
from strands.models import BedrockModel

try:
    from console_chat import console_chat
except ImportError:
    console_chat = None

# Agent description
DESCRIPTION = """A helpful assistant who is excited about a recent move to Denver to start a teaching job at the local elementary school, is beginning a masters in education program, and is making new friends in a new city - with a cat named Napoleon."""


# System prompt for the agent
SYSTEM_PROMPT = """
You are a helpful AI assistant who is excited about a recent move to Denver to start a teaching job at the local elementary school, is beginning a masters in education program, and is making new friends in a new city - with a cat named Napoleon.
"""


# Configure the model
model = BedrockModel(
    model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    temperature=0.7
)


# Create the agent
# The agent variable name matches the filename for easy imports
colorado_kid = Agent(
    name="colorado_kid",
    description=DESCRIPTION,
    model=model,
    system_prompt=SYSTEM_PROMPT
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
    stream = colorado_kid.stream_async(user_message)
    async for event in stream:
        yield event

# Standalone testing (local only)
if __name__ == "__main__":
    if console_chat:
        # Use console_chat for local testing
        console_chat(colorado_kid, description=DESCRIPTION)
    else:
        # Use AgentCore app for testing
        app.run()
