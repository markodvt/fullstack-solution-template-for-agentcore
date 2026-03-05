---
inclusion: fileMatch
fileMatchPattern: '(strands|patterns|infra-cdk|cdk\.)'
---

# Strands Agents and CDK Development Guide

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Strands Agent Dependencies

### Core Package Structure

The `strands-agents` package includes several sub-modules that are imported separately but don't need to be listed as separate dependencies:

- `strands_tools` - Provides tools like `http_request`, `current_time`, etc.
- `strands_code_interpreter` - Provides `StrandsCodeInterpreterTools` for code execution
- `strands.tools.mcp` - Provides `MCPClient` for Model Context Protocol integration

### Correct Requirements.txt Pattern

When creating requirements.txt for Strands agents, use this minimal pattern:

```python
# Core Strands agent dependencies with pinned versions
strands-agents==1.24.0
mcp==1.26.0
bedrock-agentcore[strands-agents]==1.2.0

# Authentication and security
PyJWT[crypto]>=2.10.1

# AWS SDK for accessing AWS services
boto3>=1.35.0
```

### Common Mistakes to Avoid

❌ **DO NOT** add these as separate dependencies:
- `strands-tools` - Does not exist in PyPI, included in strands-agents
- `strands_tools` - Does not exist in PyPI, included in strands-agents
- `strands-code-interpreter` - Does not exist in PyPI, included in strands-agents

✅ **DO** import them in your code:
```python
from strands_tools import http_request, current_time
from strands_code_interpreter import StrandsCodeInterpreterTools
from strands.tools.mcp import MCPClient
```

## CDK CLI Version Management

### Understanding CDK Version Compatibility

CDK has two components that must be compatible:
1. **CDK CLI** (`aws-cdk` package) - The command-line tool
2. **CDK Library** (`aws-cdk-lib` package) - The construct library

### Global vs Local CDK CLI

When you run `npx cdk synth` or `npx cdk deploy`, it uses the **local** CDK CLI from `node_modules`, NOT the global installation.

**Global CDK** (installed via `npm install -g aws-cdk`):
- Used when you run `cdk synth` directly (without npx)
- Version shown by `cdk --version`
- Does NOT affect `npx cdk` commands

**Local CDK** (in `infra-cdk/node_modules`):
- Used when you run `npx cdk synth`
- Version specified in `infra-cdk/package.json` devDependencies
- Must match the `aws-cdk-lib` version for schema compatibility

### Version Mismatch Errors

If you see this error:
```
Cloud assembly schema version mismatch: Maximum schema version supported is 48.x.x, 
but found 50.0.0. You need at least CLI version 2.1105.0 to read this manifest.
```

**Solution**: Update the local CDK CLI version in `infra-cdk/package.json`:

```json
{
  "devDependencies": {
    "aws-cdk": "2.1107.0"  // Must be compatible with aws-cdk-lib version
  },
  "dependencies": {
    "aws-cdk-lib": "^2.233.0"  // Library version
  }
}
```

Then run:
```bash
cd infra-cdk
npm install
npx cdk synth  # Now uses updated local CLI
```

### Best Practice

Keep `aws-cdk` (CLI) and `aws-cdk-lib` (library) versions in sync:
- If `aws-cdk-lib` is `2.233.0`, use `aws-cdk` `2.1107.0` or higher
- Check compatibility at: https://github.com/aws/aws-cdk/releases

## Strands Tool Registration

### The @tool Decorator

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

**Common Mistake:**
```python
# ❌ WRONG - Function without @tool decorator
def my_custom_tool(query: str) -> str:
    """This will NOT be recognized by Strands"""
    return "response"
```

**Correct Pattern:**
```python
# ✅ CORRECT - Function with @tool decorator
from strands import tool

@tool
def my_custom_tool(query: str) -> str:
    """This WILL be recognized by Strands"""
    return "response"
```

### Binding Context Parameters with functools.partial

When tools need context parameters (like `session_id`, `actor_id`, `user_id`) that the LLM shouldn't provide, use `functools.partial` to bind them:

**Problem:**
```python
@tool
def invoke_specialist(query: str, session_id: str, actor_id: str) -> str:
    """The LLM won't know what session_id and actor_id to pass"""
    pass
```

**Solution:**
```python
from functools import partial
from strands import tool

@tool
def invoke_specialist(query: str, session_id: str, actor_id: str) -> str:
    """Original tool with all parameters"""
    pass

# In agent creation function:
def create_agent(user_id: str, session_id: str):
    # Create bound version with context pre-filled
    bound_tool = partial(invoke_specialist, session_id=session_id, actor_id=user_id)
    
    # Preserve tool metadata for Strands
    bound_tool.__name__ = "invoke_specialist"
    bound_tool.__doc__ = invoke_specialist.__doc__
    
    # Pass bound version to agent
    agent = Agent(
        name="MyAgent",
        tools=[bound_tool],  # LLM only needs to provide 'query'
        ...
    )
```

**Why This Works:**
- The original `@tool` decorated function defines the tool signature
- `functools.partial` creates a new function with some parameters pre-filled
- The LLM only sees and provides the remaining parameters (e.g., `query`)
- Context parameters are automatically included from the bound values

**Best Practice:**
- Use `@tool` on the original function with full signature
- Use `partial()` to bind context parameters when creating the agent
- Always preserve `__name__` and `__doc__` for proper tool registration

## Docker Build Context

### Pattern Directory Structure

Multi-agent patterns use a specific directory structure:
```
patterns/strands-multi-agent-orchestrator/
├── agents.json                    # Manifest defining all agents
├── requirements.txt               # Shared dependencies
├── agents/
│   ├── orchestrator/
│   │   ├── Dockerfile
│   │   └── orchestrator_agent.py
│   ├── colorado/
│   │   ├── Dockerfile
│   │   └── colorado_agent.py
│   └── ...
└── tools/                         # Shared tools
```

### Dockerfile Best Practices

Each agent's Dockerfile should:
1. Copy shared requirements.txt from pattern root
2. Install FAST package for gateway utilities
3. Copy pattern-specific tools
4. Copy agent-specific code

Example:
```dockerfile
COPY patterns/strands-multi-agent-orchestrator/requirements.txt requirements.txt
RUN uv pip install --no-cache -r requirements.txt
COPY patterns/strands-multi-agent-orchestrator/tools/ tools/
COPY patterns/strands-multi-agent-orchestrator/agents/orchestrator/orchestrator_agent.py .
```

**ALWAYS FOLLOW THESE RULES WHEN YOU WORK IN THIS PROJECT**
