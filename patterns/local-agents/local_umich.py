"""A helpful assistant who LOVES the University of Michigan.

This agent has access to HTTP requests and current time tools.
"""

from strands import Agent
from strands.models import BedrockModel

from strands_tools import http_request, current_time
from local_tools import simple_greeting
from console_chat import console_chat

agent = Agent(
    system_prompt = "You are a helpful assistant who LOVES the University of Michigan.",
    model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0"),
    tools = [http_request, current_time, simple_greeting]
)

if __name__ == "__main__":
    console_chat(agent, description="A helpful assistant who LOVES the University of Michigan.")
