---
inclusion: fileMatch
fileMatchPattern: '(strands|patterns|infra-cdk|cdk\.)'
---

# Strands Agents and CDK Development Guide

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Strands Agent Dependencies

### Package Structure

```python
# Core dependencies - requirements.txt
strands-agents==1.24.0              # Core framework
strands-agents-tools>=0.2.0         # Community tools (http_request, current_time)
mcp==1.26.0                         # Model Context Protocol
bedrock-agentcore[strands-agents]==1.2.0
PyJWT[crypto]>=2.10.1
boto3>=1.35.0
```

### Import Patterns

```python
# Core framework
from strands import Agent, tool
from strands.models import BedrockModel

# Community tools (from strands-agents-tools package)
from strands_tools import http_request, current_time

# Usage
agent = Agent(
    system_prompt="Your prompt",
    tools=[http_request, current_time],
    model=BedrockModel(model_id="...")
)
```

### Common Mistakes

❌ **DO NOT** assume `strands_tools` is in `strands-agents` - it's a separate package
❌ **DO NOT** forget `strands-agents-tools` in requirements.txt
❌ **DO NOT** use `from strands.tools import http_request` (wrong path)

✅ **DO** install both `strands-agents` AND `strands-agents-tools`
✅ **DO** use `from strands_tools import http_request`

---

## Tool Registration with @tool Decorator

Functions MUST be decorated with `@tool` for Strands to recognize them:

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

### Binding Context Parameters

When tools need context (session_id, actor_id) that the LLM shouldn't provide, use a class wrapper:

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

**Why not functools.partial?** It creates wrapper objects that don't preserve `@tool` decorator metadata.

---

## CDK CLI Version Management

### Understanding CDK Versions

CDK has two components:
1. **CDK CLI** (`aws-cdk` package) - Command-line tool
2. **CDK Library** (`aws-cdk-lib` package) - Construct library

### Global vs Local CDK

When you run `npx cdk synth`, it uses the **local** CDK CLI from `node_modules`, NOT global.

**Version Mismatch Error:**
```
Cloud assembly schema version mismatch: Maximum schema version supported is 48.x.x, 
but found 50.0.0. You need at least CLI version 2.1105.0
```

**Solution:** Update local CDK CLI in `infra-cdk/package.json`:

```json
{
  "devDependencies": {
    "aws-cdk": "2.1107.0"  // Must match aws-cdk-lib compatibility
  },
  "dependencies": {
    "aws-cdk-lib": "^2.233.0"
  }
}
```

Then:
```bash
cd infra-cdk
npm install
npx cdk synth  # Uses updated local CLI
```

**Best Practice:** Keep `aws-cdk` (CLI) and `aws-cdk-lib` (library) versions in sync.

---

## Docker Build Context

### Pattern Directory Structure

```
patterns/strands-multi-agent-orchestrator/
├── agents.json                    # Manifest
├── requirements.txt               # Shared dependencies
├── agents/
│   ├── orchestrator/
│   │   ├── Dockerfile
│   │   └── orchestrator_agent.py
│   └── colorado/
│       ├── Dockerfile
│       └── colorado_agent.py
└── tools/                         # Shared tools
```

### Dockerfile Best Practices

```dockerfile
# Copy shared requirements from pattern root
COPY patterns/strands-multi-agent-orchestrator/requirements.txt requirements.txt
RUN uv pip install --no-cache -r requirements.txt

# Copy shared tools
COPY patterns/strands-multi-agent-orchestrator/tools/ tools/

# Copy agent-specific code
COPY patterns/strands-multi-agent-orchestrator/agents/orchestrator/orchestrator_agent.py .
```

**ALWAYS FOLLOW THESE RULES WHEN YOU WORK IN THIS PROJECT**
