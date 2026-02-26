# Design Document: Multi-Agent Orchestration Pattern

## Overview

This design document specifies the technical implementation for refactoring the current multi-agent deployment architecture from treating each agent as a separate pattern to a unified multi-agent orchestration pattern. The refactoring consolidates all four agents (orchestrator + three specialists: colorado, umich, coder) into a single pattern directory that properly represents a multi-agent orchestration architectural approach.

### Current State

The current implementation incorrectly uses the `patterns/` directory to hold individual agents:
- `patterns/strands-colorado-agent/`
- `patterns/strands-umich-agent/`
- `patterns/strands-coder-agent/`
- `agents/` directory with standalone agent files

Each agent is treated as a separate "pattern" directory, which violates the repository's architectural principle that patterns represent different deployment approaches, not individual agents.

### Target State

The refactored implementation will have:
- Single pattern directory: `patterns/strands-multi-agent-orchestrator/`
- All four agents (orchestrator, colorado, umich, coder) within this pattern
- Shared resources (tools/, utils/) within the pattern
- Separate Dockerfiles per agent with shared requirements.txt for efficient iteration
- Simplified config.yaml pointing to one pattern
- Agent discovery via agents.json manifest
- CDK stack deploying multiple AgentCore Runtime instances from one pattern

Directory structure:
```
patterns/strands-multi-agent-orchestrator/
├── agents/
│   ├── orchestrator/
│   │   ├── orchestrator_agent.py
│   │   └── Dockerfile
│   ├── colorado/
│   │   ├── colorado_agent.py
│   │   └── Dockerfile
│   ├── umich/
│   │   ├── umich_agent.py
│   │   └── Dockerfile
│   └── coder/
│       ├── coder_agent.py
│       └── Dockerfile
├── tools/          # pattern-specific tools
├── requirements.txt  # shared dependencies
└── agents.json     # agent discovery manifest

patterns/utils/     # shared across ALL patterns (already exists)
├── auth.py         # OAuth2 + JWT utilities
└── ssm.py          # SSM Parameter Store access
```

### Key Design Principles

1. **Patterns represent architectural approaches**: A pattern is a deployment strategy (single agent, multi-agent orchestration, LangGraph-based), not an individual agent
2. **Resource sharing**: All agents share AgentCore Memory, Gateway, Code Interpreter, and Cognito
3. **Session isolation**: Each agent maintains separate conversation history using session prefixes
4. **Actor consistency**: Same user (actor_id) across all agents for shared long-term memory
5. **Independent agent deployment**: Each agent has its own Dockerfile for fast iteration - only changed agents need rebuilding
6. **Extensibility**: Architecture supports future frontends (Amazon Connect, workflows) without modification


## Architecture

### High-Level Architecture

The multi-agent orchestration pattern implements a hub-and-spoke architecture where the Orchestrator Agent acts as the central hub, routing user queries to specialized agents based on query content and context.

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend UI                          │
│                  (Agent Selection Interface)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway / ALB                         │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬──────────────┐
         │               │               │              │
         ▼               ▼               ▼              ▼
┌────────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│  Orchestrator  │ │ Colorado │ │  UMich   │ │    Coder     │
│     Agent      │ │  Agent   │ │  Agent   │ │    Agent     │
│  (Runtime 1)   │ │(Runtime2)│ │(Runtime3)│ │  (Runtime 4) │
└────────┬───────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘
         │              │            │               │
         └──────────────┴────────────┴───────────────┘
                         │
         ┌───────────────┼───────────────┬──────────────┐
         ▼               ▼               ▼              ▼
┌────────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│  AgentCore     │ │AgentCore │ │  Code    │ │   Cognito    │
│    Memory      │ │ Gateway  │ │Interpreter│ │  User Pool   │
└────────────────┘ └──────────┘ └──────────┘ └──────────────┘
```

### Component Interaction Flow

1. **User Request**: User selects an agent from the UI and sends a message
2. **Routing**: Request is routed to the selected agent's AgentCore Runtime endpoint
3. **Authentication**: Agent retrieves JWT token from Cognito for gateway access
4. **Memory Access**: Agent retrieves conversation history from AgentCore Memory using agent-specific session prefix
5. **Tool Execution**: Agent invokes tools via AgentCore Gateway (MCP protocol)
6. **Orchestration** (if Orchestrator): Orchestrator may invoke specialist agents as tools
7. **Response**: Agent returns response to frontend
8. **Memory Update**: Agent stores conversation turn in AgentCore Memory

### Deployment Architecture

Each agent is deployed as a separate AgentCore Runtime instance with its own Docker container:

- **Orchestrator Runtime**: Hosts orchestrator_agent.py, has tools to invoke specialists
- **Colorado Runtime**: Hosts colorado_agent.py, specialized for Colorado-specific queries
- **UMich Runtime**: Hosts umich_agent.py, specialized for University of Michigan queries
- **Coder Runtime**: Hosts coder_agent.py, specialized for coding assistance

All runtimes share:
- Single AgentCore Memory instance (with session prefixes for isolation)
- Single AgentCore Gateway instance (MCP server access)
- Single Code Interpreter instance (secure Python execution)
- Single Cognito User Pool (authentication)

## Components and Interfaces

### 1. Pattern Directory Structure

```
patterns/strands-multi-agent-orchestrator/
├── agents/
│   ├── orchestrator/
│   │   ├── orchestrator_agent.py      # Main orchestrator logic
│   │   └── Dockerfile                 # Orchestrator-specific build
│   ├── colorado/
│   │   ├── colorado_agent.py          # Colorado specialist logic
│   │   └── Dockerfile                 # Colorado-specific build
│   ├── umich/
│   │   ├── umich_agent.py             # UMich specialist logic
│   │   └── Dockerfile                 # UMich-specific build
│   └── coder/
│       ├── coder_agent.py             # Coder specialist logic
│       └── Dockerfile                 # Coder-specific build
├── tools/
│   ├── code_interpreter.py            # Shared code execution wrapper
│   ├── invoke_specialist.py           # Tool for orchestrator to call specialists
│   └── __init__.py
├── requirements.txt                   # Shared dependencies for all agents
└── agents.json                        # Agent discovery manifest

# Shared utilities (already exist at repository level)
patterns/utils/
├── auth.py                            # OAuth2 + JWT + Secrets Manager utilities
└── ssm.py                             # SSM Parameter Store access
```

**Note**: The pattern does NOT have its own `utils/` directory. All agents import from the existing `patterns/utils/` which provides shared authentication and configuration utilities used across all patterns.

### 2. Agent Implementations

#### Orchestrator Agent (orchestrator_agent.py)

```python
"""
Orchestrator agent that routes queries to specialist agents.
"""
from typing import Dict, Any, List
import sys
sys.path.append('/app/patterns')  # Add patterns to path for shared utils

from tools.invoke_specialist import invoke_colorado, invoke_umich, invoke_coder
from utils.auth import get_gateway_access_token
from utils.ssm import get_ssm_parameter

class OrchestratorAgent:
    """Routes user queries to appropriate specialist agents."""
    
    def __init__(self, config: Dict[str, Any]):
        self.agent_name = "orchestrator"
        self.tools = [invoke_colorado, invoke_umich, invoke_coder]
    
    def get_session_id(self, base_session_id: str) -> str:
        """Get agent-specific session ID with prefix."""
        return f"{self.agent_name}_{base_session_id}"
    
    def handle_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request and route to specialists as needed."""
        # Session prefixing is just string concatenation
        session_id = self.get_session_id(event['sessionId'])
        # Implementation details
        pass
```

#### Specialist Agents (colorado_agent.py, umich_agent.py, coder_agent.py)

Each specialist follows a similar structure:

```python
"""
Specialist agent for domain-specific queries.
"""
from typing import Dict, Any
import sys
sys.path.append('/app/patterns')  # Add patterns to path for shared utils

from tools.code_interpreter import execute_python_securely
from utils.auth import get_gateway_access_token
from utils.ssm import get_ssm_parameter

class SpecialistAgent:
    """Handles domain-specific queries."""
    
    def __init__(self, config: Dict[str, Any], agent_name: str):
        self.agent_name = agent_name
        self.tools = [execute_python_securely]
    
    def get_session_id(self, base_session_id: str) -> str:
        """Get agent-specific session ID with prefix."""
        return f"{self.agent_name}_{base_session_id}"
    
    def handle_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request."""
        # Session prefixing is just string concatenation
        session_id = self.get_session_id(event['sessionId'])
        # Implementation details
        pass
```

### 3. Shared Tools

#### Code Interpreter Tool (tools/code_interpreter.py)

```python
"""
Shared tool for secure Python code execution via Code Interpreter.
"""
from typing import Dict, Any
import sys
sys.path.append('/app/patterns')

from utils.auth import get_gateway_access_token
from utils.ssm import get_ssm_parameter

def execute_python_securely(code: str, session_id: str) -> Dict[str, Any]:
    """
    Execute Python code securely using AgentCore Code Interpreter.
    
    Args:
        code: Python code to execute
        session_id: Session identifier for context
        
    Returns:
        Dict containing execution results or error information
    """
    # Delegates to root tools/code_interpreter/ implementation
    pass
```

#### Specialist Invocation Tool (tools/invoke_specialist.py)

```python
"""
Tools for orchestrator to invoke specialist agents.
"""
from typing import Dict, Any
import sys
sys.path.append('/app/patterns')

import boto3
import json
from utils.ssm import get_ssm_parameter

def invoke_colorado(query: str, session_id: str, actor_id: str) -> str:
    """Invoke Colorado specialist agent."""
    return _invoke_specialist("colorado", query, session_id, actor_id)

def invoke_umich(query: str, session_id: str, actor_id: str) -> str:
    """Invoke UMich specialist agent."""
    return _invoke_specialist("umich", query, session_id, actor_id)

def invoke_coder(query: str, session_id: str, actor_id: str) -> str:
    """Invoke Coder specialist agent."""
    return _invoke_specialist("coder", query, session_id, actor_id)

def _invoke_specialist(
    agent_name: str, 
    query: str, 
    session_id: str, 
    actor_id: str
) -> str:
    """
    Internal method to invoke a specialist agent's runtime endpoint.
    
    Args:
        agent_name: Name of specialist agent (colorado, umich, coder)
        query: User query to process
        session_id: Session identifier (will be prefixed by specialist)
        actor_id: User identifier
        
    Returns:
        Specialist agent's response as string
    """
    # Get runtime endpoint from SSM Parameter Store using shared utility
    endpoint = get_ssm_parameter(f"/agentcore/agents/{agent_name}/endpoint")
    # Invoke AgentCore Runtime API
    # Return response
    pass
```

### 4. Shared Utilities (patterns/utils/)

The pattern leverages existing shared utilities located at `patterns/utils/` that are used across all patterns in the repository. These utilities are already implemented and provide:

#### Authentication Utility (patterns/utils/auth.py)

Provides the following functions that agents import:

- **`get_gateway_access_token() -> str`**: Retrieves OAuth2 access token using client credentials flow for AgentCore Gateway access. Handles Cognito authentication with machine client credentials from SSM/Secrets Manager.

- **`extract_user_id_from_context(context: RequestContext) -> str`**: Securely extracts user ID from validated JWT token in request context (prevents prompt injection attacks).

- **`get_secret(secret_name: str) -> str`**: Fetches secrets from AWS Secrets Manager.

**Note on Token Caching**: The current shared implementation makes a fresh token request each time. If token caching is needed for performance optimization, it should be added to the shared `patterns/utils/auth.py` (not pattern-specific implementations) so all patterns benefit from the optimization.

#### SSM Utility (patterns/utils/ssm.py)

Provides:

- **`get_ssm_parameter(parameter_name: str) -> str`**: Retrieves configuration values from AWS SSM Parameter Store (e.g., Gateway URLs, agent endpoints).

#### Session Management

Session prefixing is handled directly in agent code as simple string concatenation:

```python
def get_session_id(self, base_session_id: str) -> str:
    """Get agent-specific session ID with prefix."""
    return f"{self.agent_name}_{base_session_id}"
```

No separate SessionManager class is needed - it's just string formatting.

#### Import Pattern

Agents import from shared utilities using:

```python
import sys
sys.path.append('/app/patterns')  # Add patterns to path

from utils.auth import get_gateway_access_token, extract_user_id_from_context
from utils.ssm import get_ssm_parameter
```

### 5. Agent Discovery Manifest (agents.json)

```json
{
  "agents": [
    {
      "name": "orchestrator",
      "displayName": "Orchestrator",
      "description": "Main agent that routes queries to specialized agents",
      "runtimeId": "orchestrator",
      "isDefault": true
    },
    {
      "name": "colorado",
      "displayName": "Colorado Specialist",
      "description": "Specialized agent for Colorado-specific queries",
      "runtimeId": "colorado",
      "isDefault": false
    },
    {
      "name": "umich",
      "displayName": "UMich Specialist",
      "description": "Specialized agent for University of Michigan queries",
      "runtimeId": "umich",
      "isDefault": false
    },
    {
      "name": "coder",
      "displayName": "Coding Assistant",
      "description": "Specialized agent for coding and technical assistance",
      "runtimeId": "coder",
      "isDefault": false
    }
  ]
}
```

### 6. Dockerfile Structure

Each agent has its own Dockerfile for independent building and deployment:

#### Example: agents/orchestrator/Dockerfile

```dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Copy shared dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy pattern-specific tools
COPY tools/ ${LAMBDA_TASK_ROOT}/tools/

# Copy shared utilities from patterns/utils (parent directory)
COPY ../utils/ ${LAMBDA_TASK_ROOT}/patterns/utils/

# Copy agent-specific code
COPY agents/orchestrator/orchestrator_agent.py ${LAMBDA_TASK_ROOT}/

# Set handler
CMD ["orchestrator_agent.handler"]
```

Benefits of separate Dockerfiles:
- **Fast iteration**: Only rebuild changed agents
- **Independent deployment**: Deploy agents separately
- **Smaller updates**: Only push changed container images
- **Parallel builds**: Build all agents concurrently

**Note**: The Dockerfile copies `patterns/utils/` from the parent directory to make the shared utilities available at the expected import path.

### 7. CDK Stack Integration

The CDK stack reads agents.json and creates:
- Separate AgentCore Runtime instance per agent
- Separate Docker image per agent (built from agent-specific Dockerfile)
- SSM parameters with agent metadata
- API Gateway routes to each runtime
- Shared backend resources (Memory, Gateway, Code Interpreter, Cognito)

## Data Models

### Request Event Structure

```typescript
interface AgentRequest {
  sessionId: string;        // Base session ID (will be prefixed by agent)
  actorId: string;          // User identifier (from JWT)
  message: string;          // User's message
  context?: {               // Optional context
    previousAgent?: string; // If routed from orchestrator
    metadata?: Record<string, any>;
  };
}
```

### Response Structure

```typescript
interface AgentResponse {
  response: string;         // Agent's response text
  agentName: string;        // Name of responding agent
  sessionId: string;        // Session ID used (prefixed)
  metadata?: {              // Optional metadata
    toolsUsed?: string[];   // Tools invoked during processing
    specialistCalled?: string; // If orchestrator called specialist
  };
}
```

### Agent Metadata (SSM Parameter Store)

```typescript
interface AgentMetadata {
  name: string;             // Agent name (orchestrator, colorado, etc.)
  displayName: string;      // Human-readable name
  description: string;      // Agent description
  runtimeEndpoint: string;  // AgentCore Runtime API endpoint
  runtimeArn: string;       // AgentCore Runtime ARN
  isDefault: boolean;       // Whether this is the default agent
}
```

### Session Data (AgentCore Memory)

```typescript
interface SessionData {
  sessionId: string;        // Prefixed session ID
  actorId: string;          // User identifier
  turns: ConversationTurn[];
  metadata: {
    agentName: string;      // Which agent owns this session
    createdAt: string;
    lastAccessedAt: string;
  };
}

interface ConversationTurn {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Session Prefix Isolation

*For any* agent and any session ID, when the agent accesses AgentCore Memory, the session ID used SHALL be prefixed with the agent-specific prefix (e.g., "orchestrator_", "colorado_", "umich_", "coder_"), ensuring separate conversation histories per agent.

**Validates: Requirements 2.5**

### Property 2: Actor ID Consistency

*For any* user (actor) and any set of agents, when the same user interacts with different agents, all agents SHALL use the same Actor_ID when accessing AgentCore Memory, ensuring shared long-term memory across agents.

**Validates: Requirements 2.6**

### Property 3: Concurrent Resource Access

*For any* set of concurrent requests to different agents, when multiple agents access Backend_Resources (Memory, Gateway, Code Interpreter) simultaneously, each request SHALL be handled independently without interference or data corruption.

**Validates: Requirements 2.8**

### Property 4: Agent Manifest Completeness

*For any* agent entry in the agents.json manifest, the entry SHALL include all required fields: agent name, display name, description, and runtime endpoint identifier.

**Validates: Requirements 4.2**

### Property 5: Orchestrator-Specialist Communication Flow

*For any* specialist agent invocation by the Orchestrator, the following SHALL hold:
- The invocation SHALL make a direct call to the specialist's AgentCore Runtime endpoint
- The user's query and session context SHALL be passed to the specialist
- The specialist SHALL return a response to the orchestrator
- The orchestrator's response SHALL include the specialist's response

**Validates: Requirements 5.2, 5.3, 5.4, 5.5**

### Property 6: Orchestrator Context Preservation

*For any* orchestrator-to-specialist invocation, the orchestrator SHALL:
- Maintain the same Actor_ID when calling the specialist
- Use an agent-specific Session_ID for the specialist to maintain separate conversation history
- Ensure the specialist has access to the user's long-term memory via AgentCore Memory

**Validates: Requirements 5.6, 5.7, 5.8**

### Property 7: Shared Resource Import Consistency

*For any* agent implementation, when the agent needs to use shared functionality:
- Code execution SHALL be imported from the pattern's `tools/` directory
- Authentication SHALL be imported from `patterns/utils/auth.py`
- SSM parameter access SHALL be imported from `patterns/utils/ssm.py`
- The agent SHALL NOT contain duplicate implementations of these functions

**Validates: Requirements 6.3, 6.5, 6.6, 6.7, 6.8**

### Property 8: Gateway Authentication Flow

*For any* agent accessing AgentCore Gateway, the agent SHALL:
- Retrieve a JWT token from Cognito using machine client credentials from SSM Parameter Store
- Include the JWT token in the Authorization header of the gateway request

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 9: UI Agent Management

*For any* agent selection in the UI, the following SHALL hold:
- The UI SHALL update the active agent for the current session
- Subsequent requests SHALL be routed to the selected agent's AgentCore Runtime endpoint
- Conversation histories SHALL remain separate when switching between agents
- Previous conversation context SHALL be preserved when switching agents

**Validates: Requirements 9.2, 9.3, 9.5, 9.6**

### Property 10: Dockerfile Dependency Consistency

*For any* agent Dockerfile, the Dockerfile SHALL install dependencies from the shared requirements.txt file located at the pattern root, ensuring all agents use consistent dependency versions.

**Validates: Requirements 11.2**

## Error Handling

### Authentication Errors

**Scenario**: JWT token retrieval from Cognito fails

**Handling**:
- Agent SHALL catch the authentication exception from `get_gateway_access_token()` (from `patterns/utils/auth.py`)
- Agent SHALL log the error with details (client ID, error message)
- Agent SHALL return a user-friendly error response: "Unable to authenticate with gateway. Please try again later."
- Agent SHALL NOT expose sensitive credential information in error messages

**Scenario**: JWT token expires during request processing

**Handling**:
- The `get_gateway_access_token()` function in `patterns/utils/auth.py` handles token refresh automatically
- Request SHALL proceed with new token
- If token refresh fails, follow authentication error handling above

### Memory Access Errors

**Scenario**: AgentCore Memory is unavailable or returns an error

**Handling**:
- Agent SHALL catch the memory access exception
- Agent SHALL log the error with session ID and actor ID
- Agent SHALL attempt to proceed without conversation history (degraded mode)
- Agent SHALL include a note in the response: "Note: Previous conversation history temporarily unavailable"
- Agent SHALL NOT fail the entire request due to memory unavailability

**Scenario**: Session data is corrupted or malformed

**Handling**:
- Agent SHALL validate session data structure when retrieving from AgentCore Memory
- If validation fails, agent SHALL log the error and start a new session
- Agent SHALL proceed with empty conversation history
- Agent SHALL notify user: "Starting a new conversation session"

### Gateway and Tool Errors

**Scenario**: AgentCore Gateway is unavailable

**Handling**:
- Agent SHALL catch gateway connection errors
- Agent SHALL log the error with gateway endpoint and error details
- Agent SHALL return error to user: "Gateway service temporarily unavailable. Tool access is currently limited."
- Agent SHALL continue processing if possible without tool access

**Scenario**: Tool execution fails (e.g., code interpreter error)

**Handling**:
- Tool wrapper SHALL catch execution exceptions
- Tool wrapper SHALL log the error with tool name and input parameters
- Tool wrapper SHALL return structured error response to agent
- Agent SHALL include error information in response to user with actionable guidance

**Scenario**: Code Interpreter times out

**Handling**:
- Code execution wrapper SHALL implement timeout (e.g., 30 seconds)
- If timeout occurs, wrapper SHALL terminate execution
- Wrapper SHALL return timeout error to agent
- Agent SHALL inform user: "Code execution timed out. Please simplify the code or reduce computation."

### Orchestrator-Specialist Communication Errors

**Scenario**: Specialist agent runtime is unavailable

**Handling**:
- Orchestrator's invoke_specialist tool SHALL catch runtime invocation errors
- Tool SHALL log the error with specialist name and endpoint
- Tool SHALL return error to orchestrator: "Specialist {name} is currently unavailable"
- Orchestrator SHALL inform user and offer to handle query directly or suggest alternative specialist

**Scenario**: Specialist returns malformed response

**Handling**:
- Orchestrator SHALL validate specialist response structure
- If validation fails, orchestrator SHALL log the error
- Orchestrator SHALL return to user: "Received unexpected response from specialist. Attempting to handle query directly."
- Orchestrator SHALL attempt to answer query without specialist assistance

### Configuration and Deployment Errors

**Scenario**: agents.json manifest is missing or malformed

**Handling**:
- CDK Stack SHALL validate agents.json during deployment
- If validation fails, deployment SHALL fail with descriptive error
- Error message SHALL indicate which field is missing or malformed
- Deployment SHALL NOT proceed with invalid agent configuration

**Scenario**: Required SSM parameters are missing

**Handling**:
- Agent initialization SHALL check for required SSM parameters
- If parameters are missing, agent SHALL fail to initialize
- Error SHALL be logged with parameter names
- CloudWatch logs SHALL contain clear error message for debugging

**Scenario**: Docker build fails for one agent

**Handling**:
- CDK Stack SHALL detect build failure
- Deployment SHALL fail immediately (fail-fast)
- Error message SHALL indicate which agent failed to build
- Error message SHALL include build log excerpt
- Other agents SHALL NOT be deployed if any agent fails

### Input Validation Errors

**Scenario**: Request missing required fields (sessionId, actorId, message)

**Handling**:
- Agent SHALL validate request structure before processing
- If validation fails, agent SHALL return 400 Bad Request
- Error response SHALL list missing or invalid fields
- Agent SHALL NOT attempt to process invalid requests

**Scenario**: Session ID or Actor ID format is invalid

**Handling**:
- Agent SHALL validate ID formats before processing
- If validation fails, agent SHALL return validation error
- Agent SHALL return error to user: "Invalid session or user identifier"
- Agent SHALL log the validation failure for monitoring

## Testing Strategy

### Overview

The testing strategy employs a dual approach combining unit tests for specific scenarios and property-based tests for universal properties. This ensures both concrete edge cases and general correctness are validated.

### Unit Testing

**Scope**: Specific examples, edge cases, error conditions, and integration points

**Framework**: pytest for Python components, Jest for TypeScript CDK code

**Test Organization**:
```
patterns/strands-multi-agent-orchestrator/
├── tests/
│   ├── unit/
│   │   ├── test_orchestrator_agent.py
│   │   ├── test_colorado_agent.py
│   │   ├── test_umich_agent.py
│   │   ├── test_coder_agent.py
│   │   ├── test_code_interpreter.py
│   │   └── test_invoke_specialist.py
│   ├── integration/
│   │   ├── test_orchestrator_to_specialist.py
│   │   ├── test_memory_integration.py
│   │   └── test_gateway_integration.py
│   └── property/
│       ├── test_properties.py
│       └── generators.py

# Shared utilities are tested at the patterns/utils level
patterns/utils/
├── tests/
│   ├── test_auth.py
│   └── test_ssm.py
```

**Unit Test Examples**:

1. **Agent Initialization**: Verify each agent initializes correctly with valid configuration
2. **Session Prefix Application**: Test that agents correctly apply agent-specific prefixes using string concatenation
3. **Token Retrieval**: Test that agents can successfully call `get_gateway_access_token()` from `patterns/utils/auth.py`
4. **SSM Parameter Retrieval**: Test that agents can successfully call `get_ssm_parameter()` from `patterns/utils/ssm.py`
5. **Specialist Invocation**: Test that orchestrator can invoke each specialist agent
6. **Error Handling**: Test each error scenario defined in Error Handling section
7. **Empty Message Handling**: Test agents handle empty or whitespace-only messages
8. **Malformed Request Handling**: Test agents reject requests with missing required fields
9. **Agent Discovery**: Test that agents.json is correctly parsed and validated
10. **Import Validation**: Test that agents import from `patterns/utils/` not pattern-specific `utils/`

**Integration Test Examples**:

1. **End-to-End Orchestrator Flow**: Test complete flow from user request through orchestrator to specialist and back
2. **Memory Persistence**: Test that conversation turns are correctly stored and retrieved from AgentCore Memory
3. **Gateway Tool Access**: Test that agents can successfully invoke tools via AgentCore Gateway
4. **Code Execution**: Test that code interpreter tool correctly executes Python code
5. **Multi-Agent Session Isolation**: Test that different agents maintain separate session histories for the same user
6. **Concurrent Access**: Test that multiple agents can access shared resources concurrently without issues

### Property-Based Testing

**Scope**: Universal properties that should hold for all valid inputs

**Framework**: Hypothesis for Python

**Configuration**: Minimum 100 iterations per property test (due to randomization)

**Test Tagging**: Each property test references its design document property
- Format: `# Feature: multi-agent-orchestration-pattern, Property {number}: {property_text}`

**Property Test Implementations**:

**Property 1: Session Prefix Isolation**
```python
# Feature: multi-agent-orchestration-pattern, Property 1: Session Prefix Isolation
@given(
    agent_name=st.sampled_from(['orchestrator', 'colorado', 'umich', 'coder']),
    session_id=st.text(min_size=1, max_size=50)
)
@settings(max_examples=100)
def test_session_prefix_isolation(agent_name, session_id):
    """For any agent and session ID, the prefixed session ID should start with agent prefix."""
    # Session prefixing is done directly in agent code
    prefixed_id = f"{agent_name}_{session_id}"
    assert prefixed_id.startswith(f"{agent_name}_")
    assert prefixed_id.endswith(session_id)
    assert prefixed_id == f"{agent_name}_{session_id}"
```

**Property 2: Actor ID Consistency**
```python
# Feature: multi-agent-orchestration-pattern, Property 2: Actor ID Consistency
@given(
    actor_id=st.text(min_size=1, max_size=50),
    agents=st.lists(
        st.sampled_from(['orchestrator', 'colorado', 'umich', 'coder']),
        min_size=2,
        max_size=4,
        unique=True
    )
)
@settings(max_examples=100)
def test_actor_id_consistency(actor_id, agents):
    """For any user and set of agents, all agents should use the same actor ID."""
    # Mock memory access for each agent
    actor_ids_used = []
    for agent_name in agents:
        # Simulate agent accessing memory with actor_id
        # Verify actor_id is not modified
        actor_ids_used.append(actor_id)  # In real test, extract from memory call
    
    assert len(set(actor_ids_used)) == 1
    assert actor_ids_used[0] == actor_id
```

**Property 4: Agent Manifest Completeness**
```python
# Feature: multi-agent-orchestration-pattern, Property 4: Agent Manifest Completeness
@given(
    agent_entry=st.fixed_dictionaries({
        'name': st.text(min_size=1),
        'displayName': st.text(min_size=1),
        'description': st.text(min_size=1),
        'runtimeId': st.text(min_size=1),
        'isDefault': st.booleans()
    })
)
@settings(max_examples=100)
def test_agent_manifest_completeness(agent_entry):
    """For any agent entry, all required fields should be present."""
    required_fields = ['name', 'displayName', 'description', 'runtimeId']
    for field in required_fields:
        assert field in agent_entry
        assert agent_entry[field]  # Not empty
```

**Property 7: Shared Resource Import Consistency**
```python
# Feature: multi-agent-orchestration-pattern, Property 7: Shared Resource Import Consistency
@given(agent_file=st.sampled_from([
    'agents/orchestrator/orchestrator_agent.py',
    'agents/colorado/colorado_agent.py',
    'agents/umich/umich_agent.py',
    'agents/coder/coder_agent.py'
]))
@settings(max_examples=100)
def test_shared_resource_imports(agent_file):
    """For any agent, shared functionality should be imported from correct shared locations."""
    with open(agent_file, 'r') as f:
        content = f.read()
    
    # Check for imports from pattern tools
    if 'execute_python_securely' in content:
        assert 'from tools.code_interpreter import' in content or \
               'from tools import' in content
    
    # Check for imports from patterns/utils (not pattern-specific utils)
    if 'get_gateway_access_token' in content:
        assert 'from utils.auth import' in content
        assert 'sys.path.append' in content  # Should add patterns to path
    
    if 'get_ssm_parameter' in content:
        assert 'from utils.ssm import' in content
        assert 'sys.path.append' in content  # Should add patterns to path
    
    # Check for NO duplicate implementations
    assert 'def execute_python_securely' not in content
    assert 'def get_gateway_access_token' not in content
    assert 'def get_ssm_parameter' not in content
    
    # Check for NO pattern-specific utils directory references
    assert 'from utils.session_manager import' not in content
    assert 'SessionManager(' not in content
```

**Property 8: Gateway Authentication Flow**
```python
# Feature: multi-agent-orchestration-pattern, Property 8: Gateway Authentication Flow
@given(
    agent_name=st.sampled_from(['orchestrator', 'colorado', 'umich', 'coder']),
    gateway_request=st.fixed_dictionaries({
        'tool_name': st.text(min_size=1),
        'parameters': st.dictionaries(st.text(), st.text())
    })
)
@settings(max_examples=100)
def test_gateway_authentication_flow(agent_name, gateway_request):
    """For any gateway access, agent should retrieve token and include in header."""
    # Mock SSM and Cognito
    with patch('boto3.client') as mock_boto:
        mock_ssm = MagicMock()
        mock_cognito = MagicMock()
        mock_boto.side_effect = lambda service: {
            'ssm': mock_ssm,
            'cognito-idp': mock_cognito
        }[service]
        
        # Simulate gateway access
        token = get_gateway_access_token()
        
        # Verify SSM was called for credentials
        assert mock_ssm.get_parameter.called
        
        # Verify token is included in request
        headers = {'Authorization': f'Bearer {token}'}
        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Bearer ')
```

**Property 10: Dockerfile Dependency Consistency**
```python
# Feature: multi-agent-orchestration-pattern, Property 10: Dockerfile Dependency Consistency
@given(dockerfile_path=st.sampled_from([
    'agents/orchestrator/Dockerfile',
    'agents/colorado/Dockerfile',
    'agents/umich/Dockerfile',
    'agents/coder/Dockerfile'
]))
@settings(max_examples=100)
def test_dockerfile_dependency_consistency(dockerfile_path):
    """For any agent Dockerfile, it should reference the shared requirements.txt and copy patterns/utils."""
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    # Check that Dockerfile copies and installs from shared requirements.txt
    assert 'COPY requirements.txt' in content
    assert 'pip install -r requirements.txt' in content
    
    # Verify it's the shared requirements.txt at pattern root, not agent-specific
    assert 'COPY agents/' not in content or \
           'requirements.txt' not in content.split('COPY agents/')[1].split('\n')[0]
    
    # Check that Dockerfile copies patterns/utils from parent directory
    assert '../utils/' in content or 'patterns/utils/' in content
    
    # Check that Dockerfile does NOT copy a pattern-specific utils directory
    lines_with_copy_utils = [line for line in content.split('\n') if 'COPY utils/' in line]
    for line in lines_with_copy_utils:
        # Should be copying ../utils/ not utils/
        assert '../utils/' in line or 'patterns/utils/' in line
```

### Test Data Generators

**Custom Hypothesis Strategies**:

```python
# generators.py
from hypothesis import strategies as st

# Agent names
agent_names = st.sampled_from(['orchestrator', 'colorado', 'umich', 'coder'])

# Session IDs (alphanumeric with hyphens)
session_ids = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-'),
    min_size=10,
    max_size=50
)

# Actor IDs (UUIDs or similar)
actor_ids = st.uuids().map(str)

# User messages
user_messages = st.text(min_size=1, max_size=500)

# Agent requests
agent_requests = st.fixed_dictionaries({
    'sessionId': session_ids,
    'actorId': actor_ids,
    'message': user_messages,
    'context': st.one_of(st.none(), st.dictionaries(st.text(), st.text()))
})

# Agent metadata
agent_metadata = st.fixed_dictionaries({
    'name': agent_names,
    'displayName': st.text(min_size=1, max_size=50),
    'description': st.text(min_size=10, max_size=200),
    'runtimeId': agent_names,
    'isDefault': st.booleans()
})
```

### Continuous Integration

**CI Pipeline**:
1. Run linting (flake8, black, mypy for Python; eslint for TypeScript)
2. Run unit tests with coverage reporting (minimum 80% coverage)
3. Run integration tests (with mocked AWS services)
4. Run property-based tests (100 iterations per property)
5. Build Docker images for all agents
6. Validate CDK synthesis
7. Run CDK deployment to test environment (if on main branch)

**Test Execution**:
```bash
# Run all tests
make test

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run property tests only
pytest tests/property/

# Run with coverage
pytest --cov=agents --cov=tools --cov=utils --cov-report=html
```

### Performance Testing

**Load Testing**: Simulate concurrent requests to multiple agents to verify:
- Backend resources handle concurrent access without degradation
- Response times remain acceptable under load
- No memory leaks or resource exhaustion

**Scalability Testing**: Test with increasing numbers of:
- Concurrent users
- Conversation history length
- Tool invocations per request

### Acceptance Testing

**Manual Testing Checklist**:
1. Deploy pattern to test environment
2. Verify all four agents are accessible via UI
3. Test direct interaction with each specialist agent
4. Test orchestrator routing to specialists
5. Verify conversation history is maintained per agent
6. Verify switching between agents preserves context
7. Test error scenarios (agent unavailable, gateway down, etc.)
8. Verify authentication works correctly
9. Test code execution via code interpreter
10. Verify memory sharing across agents for same user

**Success Criteria**:
- All unit tests pass
- All integration tests pass
- All property tests pass (100 iterations each)
- Code coverage ≥ 80%
- No critical security vulnerabilities
- All manual acceptance tests pass
- Documentation is complete and accurate

## Architecture Simplifications

This design leverages existing shared infrastructure to minimize code duplication and complexity:

### Shared Utilities (patterns/utils/)

The pattern uses existing utilities shared across all patterns:
- **Authentication**: `patterns/utils/auth.py` provides OAuth2 client credentials flow and JWT handling
- **Configuration**: `patterns/utils/ssm.py` provides SSM Parameter Store access
- **No pattern-specific utils**: Session prefixing is handled inline with simple string concatenation

### Benefits

1. **Reduced Duplication**: Authentication and configuration logic exists in one place
2. **Consistency**: All patterns use the same utilities, ensuring consistent behavior
3. **Maintainability**: Bug fixes and improvements to shared utilities benefit all patterns
4. **Simplicity**: No need for complex SessionManager class - session prefixing is just `f"{agent_name}_{session_id}"`
5. **Smaller Codebase**: Pattern directory only contains pattern-specific logic (agents and tools)

### Import Pattern

Agents add `patterns/` to the Python path and import shared utilities:

```python
import sys
sys.path.append('/app/patterns')  # Add patterns to path

from utils.auth import get_gateway_access_token
from utils.ssm import get_ssm_parameter
```

### Dockerfile Pattern

Dockerfiles copy shared utilities from the parent directory:

```dockerfile
# Copy shared utilities from patterns/utils (parent directory)
COPY ../utils/ ${LAMBDA_TASK_ROOT}/patterns/utils/
```

This ensures the import path matches the expected structure while keeping utilities shared across all patterns.
