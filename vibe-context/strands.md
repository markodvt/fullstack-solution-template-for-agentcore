---
inclusion: fileMatch
fileMatchPattern: '(strands|patterns|agents)'
---

# Strands Agents Development Guide

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Critical Package Information

### strands-agents vs strands-agents-tools

There are TWO separate packages required for Strands agents:

1. **strands-agents** - Core agent framework
2. **strands-agents-tools** - Community tools package (http_request, current_time, etc.)

**CRITICAL**: `strands_tools` is NOT included in `strands-agents`. It comes from the separate `strands-agents-tools` package.

### Correct Requirements.txt Pattern

```python
# Core Strands agent framework
strands-agents==1.24.0

# Community tools (http_request, current_time, etc.)
strands-agents-tools>=0.2.0

# Other dependencies
mcp==1.26.0
bedrock-agentcore[strands-agents]==1.2.0
boto3>=1.35.0
PyJWT[crypto]>=2.10.1
```

### Correct Import Patterns

```python
# Core framework imports
from strands import Agent, tool
from strands.tools import tool  # Tool decorator
from strands.models import BedrockModel

# Community tools imports
from strands_tools import http_request, current_time

# Usage
agent = Agent(
    system_prompt="Your prompt",
    tools=[http_request, current_time],
    model=BedrockModel(model_id="...")
)
```

## Common Mistakes to Avoid

❌ **DO NOT** assume `strands_tools` is included in `strands-agents`
❌ **DO NOT** forget to add `strands-agents-tools` to requirements.txt
❌ **DO NOT** use `from strands.tools import http_request` (wrong path)

✅ **DO** install both `strands-agents` AND `strands-agents-tools`
✅ **DO** use `from strands_tools import http_request, current_time`
✅ **DO** check that both packages are in requirements.txt

## Tool Registration with @tool Decorator

For Strands to recognize a Python function as a callable tool, it MUST be decorated with `@tool`:

```python
from strands import tool

@tool
def my_custom_tool(query: str) -> str:
    """
    Tool description that the LLM will see.
    
    Args:
        query: The user's question
        
    Returns:
        The tool's response
    """
    return "response"
```

### functools.partial and @tool Decorators

**IMPORTANT**: When using `functools.partial` to bind context parameters, use the wrapper class pattern:

```python
from strands import tool

class MyTools:
    def __init__(self, session_id: str, actor_id: str):
        self.session_id = session_id
        self.actor_id = actor_id
    
    @tool
    def my_tool(self, user_param: str) -> str:
        """Tool that uses both context and user parameters."""
        # Use self.session_id, self.actor_id, and user_param
        return result

# Usage:
tools_instance = MyTools(session_id="123", actor_id="user1")
agent = Agent(tools=[tools_instance.my_tool], ...)
```

**Why**: `functools.partial` creates wrapper objects that don't preserve `@tool` decorator metadata. The class pattern keeps the decorator intact while providing context access.

## Debugging Import Issues

If you see `ModuleNotFoundError: No module named 'strands_tools'`:

1. Check requirements.txt includes `strands-agents-tools`
2. Verify the package is installed: `pip list | grep strands`
3. Check Docker image build includes the package
4. Verify no typos in import statement

## Testing Locally

To test strands agents locally:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install strands-agents strands-agents-tools boto3

# Test imports
python -c "from strands_tools import http_request, current_time; print('Success!')"
```

**ALWAYS FOLLOW THESE RULES WHEN YOU WORK IN THIS PROJECT**
