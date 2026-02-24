# Orchestrator Agent Implementation Plan

## Architecture Overview

**4 Agents, Each with Own Runtime:**
1. **Colorado Agent** - Teacher in Denver with cat Napoleon (no tools)
2. **UMich Agent** - Michigan enthusiast with HTTP & time tools
3. **Coder Agent** - Code validation expert with Code Interpreter
4. **Orchestrator Agent** - Routes to specialists as needed (NEW)

**Key Innovation**: Orchestrator has the other 3 agents as @tool decorated functions that invoke their runtimes.

## Agent Details from Provided Files

### 1. Colorado Agent
- **Model**: Claude 3.5 Sonnet v2 (old version in file, we'll upgrade to 4.5)
- **Temperature**: 0.7
- **Tools**: None
- **Prompt**: Excited teacher in Denver, masters program, cat Napoleon
- **Status**: ✅ Already deployed and working

### 2. UMich Agent
- **Model**: Claude Sonnet 4.5
- **Temperature**: Default
- **Tools**: `http_request`, `current_time` (from strands_tools)
- **Prompt**: "You are a helpful assistant who LOVES the University of Michigan."
- **Status**: 📋 Need to adapt and deploy

### 3. Coder Agent
- **Model**: Default (we'll use Claude Sonnet 4.5)
- **Temperature**: Default
- **Tools**: `execute_python` (Code Interpreter via code_session)
- **Prompt**: Validates answers through code execution
- **Status**: 📋 Need to adapt and deploy

### 4. Orchestrator Agent (NEW)
- **Model**: Claude Sonnet 4.5
- **Temperature**: 0.7
- **Tools**: `ask_colorado`, `ask_umich`, `ask_coder` (invoke other agents)
- **Prompt**: Helpful assistant that routes to specialists
- **Status**: 📋 Need to create

## Implementation Strategy

### Phase 1: Adapt and Deploy Specialist Agents

#### Step 1.1: Adapt UMich Agent
Create `patterns/strands-umich-agent/` with:
- Memory integration (session prefix: `umich_`)
- Authentication via `extract_user_id_from_context`
- Import tools from strands: `from strands_tools import http_request, current_time`
- System prompt from original file
- Model: Claude Sonnet 4.5

#### Step 1.2: Adapt Coder Agent
Create `patterns/strands-coder-agent/` with:
- Memory integration (session prefix: `coder_`)
- Authentication via `extract_user_id_from_context`
- Code Interpreter tool using `code_session`
- System prompt from original file
- Model: Claude Sonnet 4.5
- IAM permissions for Code Interpreter

#### Step 1.3: Deploy All Specialist Agents
Deploy as separate stacks:
- `marodon-fast-colorado` (already done ✅)
- `marodon-fast-umich` (new)
- `marodon-fast-coder` (new)

Each gets its own runtime ARN.

### Phase 2: Create Orchestrator Agent

#### Step 2.1: Design Orchestrator Tools

The orchestrator will have 3 tools that invoke the specialist agents:

```python
@tool
async def ask_colorado(question: str) -> str:
    """
    Ask the Colorado agent about teaching, Denver, education, or personal topics.
    
    Use this when the user wants to chat about:
    - Teaching and education
    - Denver and Colorado
    - Personal life and experiences
    - Casual conversation
    - The agent's cat Napoleon
    
    Args:
        question: The question or message to send to Colorado agent
        
    Returns:
        Colorado agent's response
    """
    # Invoke Colorado runtime via AgentCore API
    return await invoke_agent_runtime(
        runtime_arn=COLORADO_RUNTIME_ARN,
        prompt=question,
        session_id=f"orchestrator_to_colorado_{session_id}"
    )

@tool
async def ask_umich(question: str) -> str:
    """
    Ask the UMich agent for help with web requests or time-related queries.
    
    Use this when the user needs:
    - HTTP requests to fetch web content
    - Current time or date information
    - Information about University of Michigan
    - Web scraping or API calls
    
    Args:
        question: The question or task for UMich agent
        
    Returns:
        UMich agent's response with tool results
    """
    # Invoke UMich runtime via AgentCore API
    return await invoke_agent_runtime(
        runtime_arn=UMICH_RUNTIME_ARN,
        prompt=question,
        session_id=f"orchestrator_to_umich_{session_id}"
    )

@tool
async def ask_coder(question: str) -> str:
    """
    Ask the Coder agent to write, execute, and validate code.
    
    Use this when the user needs:
    - Code execution and validation
    - Mathematical calculations
    - Algorithm implementation and testing
    - Data analysis or visualization
    - Python programming help
    
    Args:
        question: The coding task or question
        
    Returns:
        Coder agent's response with code execution results
    """
    # Invoke Coder runtime via AgentCore API
    return await invoke_agent_runtime(
        runtime_arn=CODER_RUNTIME_ARN,
        prompt=question,
        session_id=f"orchestrator_to_coder_{session_id}"
    )
```

#### Step 2.2: Orchestrator System Prompt

```python
SYSTEM_PROMPT = """You are a helpful AI orchestrator with access to three specialist agents:

1. **Colorado Agent**: A teacher in Denver with a cat named Napoleon. Great for:
   - Casual conversation and personal topics
   - Teaching and education discussions
   - Denver and Colorado information
   - Friendly, warm interactions

2. **UMich Agent**: A University of Michigan enthusiast with web tools. Great for:
   - Making HTTP requests to fetch web content
   - Getting current time and date
   - University of Michigan topics
   - Web scraping and API interactions

3. **Coder Agent**: A code validation expert with Python execution. Great for:
   - Writing and executing Python code
   - Mathematical calculations and algorithms
   - Data analysis and visualization
   - Validating answers through code

**Your Role**:
- Answer simple questions directly when you have the knowledge
- Route to specialist agents when their expertise or tools are needed
- You can consult multiple agents if needed
- Synthesize responses from specialists into coherent answers
- Be transparent about which agent you're consulting

**When to Route**:
- Colorado: Personal chat, teaching topics, casual conversation
- UMich: Need to fetch web content, check time, or Michigan topics
- Coder: Need to execute code, validate calculations, or analyze data

**When to Answer Directly**:
- General knowledge questions
- Simple explanations
- Clarifying questions
- Routing decisions

You have access to the same long-term memory as the specialist agents, so you can reference user preferences and past conversations."""
```

#### Step 2.3: Implement Agent Runtime Invocation

```python
async def invoke_agent_runtime(
    runtime_arn: str,
    prompt: str,
    session_id: str,
    access_token: str
) -> str:
    """
    Invoke another agent's runtime and return its response.
    
    This function makes an HTTP request to the AgentCore Runtime API
    to invoke a specialist agent and collect its streaming response.
    
    Args:
        runtime_arn: ARN of the agent runtime to invoke
        prompt: User's question/message for the agent
        session_id: Session ID for the invocation
        access_token: JWT access token for authentication
        
    Returns:
        Complete response text from the agent
        
    Raises:
        RuntimeError: If the invocation fails
    """
    import aiohttp
    import json
    from urllib.parse import quote
    
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com"
    escaped_arn = quote(runtime_arn, safe="")
    url = f"{endpoint}/runtimes/{escaped_arn}/invocations?qualifier=DEFAULT"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
    }
    
    payload = {
        "prompt": prompt,
        "runtimeSessionId": session_id,
    }
    
    response_text = ""
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Agent invocation failed: HTTP {response.status}"
                )
            
            # Parse SSE stream
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    try:
                        event = json.loads(line[6:])
                        # Extract text from Strands response
                        if isinstance(event.get("data"), str):
                            response_text += event["data"]
                    except json.JSONDecodeError:
                        continue
    
    return response_text
```

#### Step 2.4: Create Orchestrator Pattern

Create `patterns/strands-orchestrator-agent/` with:
- `orchestrator_agent.py` - Main agent with 3 tools
- `requirements.txt` - Include aiohttp for HTTP requests
- `Dockerfile` - Standard pattern dockerfile
- Memory integration (session prefix: `orchestrator_`)
- Authentication via `extract_user_id_from_context`

### Phase 3: Update Infrastructure

#### Step 3.1: Deploy All 4 Agents

Deploy as separate stacks:
```bash
# Already deployed
marodon-fast-colorado

# New deployments
marodon-fast-umich
marodon-fast-coder
marodon-fast-orchestrator
```

#### Step 3.2: Store Runtime ARNs in SSM

Each deployment stores its runtime ARN:
- `/marodon-fast/runtime-arn-colorado`
- `/marodon-fast/runtime-arn-umich`
- `/marodon-fast/runtime-arn-coder`
- `/marodon-fast/runtime-arn-orchestrator`

#### Step 3.3: Orchestrator Environment Variables

The orchestrator needs access to other runtime ARNs:
```python
env_vars = {
    "MEMORY_ID": memory_id,
    "AWS_DEFAULT_REGION": region,
    "STACK_NAME": stack_name,
    "COLORADO_RUNTIME_ARN": colorado_runtime_arn,  # From SSM
    "UMICH_RUNTIME_ARN": umich_runtime_arn,        # From SSM
    "CODER_RUNTIME_ARN": coder_runtime_arn,        # From SSM
}
```

#### Step 3.4: IAM Permissions

Orchestrator needs permission to invoke other runtimes:
```python
orchestrator_role.add_to_policy(
    iam.PolicyStatement(
        sid="InvokeOtherAgentRuntimes",
        effect=iam.Effect.ALLOW,
        actions=[
            "bedrock-agentcore:InvokeRuntime",
        ],
        resources=[
            colorado_runtime_arn,
            umich_runtime_arn,
            coder_runtime_arn,
        ],
    )
)
```

### Phase 4: Update Frontend

#### Step 4.1: Update aws-exports.json

```json
{
  "awsRegion": "us-east-1",
  "cognitoUserPoolId": "us-east-1_xxx",
  "cognitoClientId": "xxx",
  "cognitoDomain": "xxx.auth.us-east-1.amazoncognito.com",
  "agents": [
    {
      "id": "orchestrator",
      "name": "Orchestrator",
      "description": "Smart assistant that routes to specialists",
      "runtimeArn": "arn:aws:bedrock-agentcore:...:orchestrator",
      "pattern": "strands-single-agent",
      "icon": "🎯"
    },
    {
      "id": "colorado",
      "name": "Colorado Teacher",
      "description": "Friendly teacher in Denver with cat Napoleon",
      "runtimeArn": "arn:aws:bedrock-agentcore:...:colorado",
      "pattern": "strands-single-agent",
      "icon": "🏔️"
    },
    {
      "id": "umich",
      "name": "UMich Assistant",
      "description": "Michigan fan with web tools",
      "runtimeArn": "arn:aws:bedrock-agentcore:...:umich",
      "pattern": "strands-single-agent",
      "icon": "〽️"
    },
    {
      "id": "coder",
      "name": "Code Validator",
      "description": "Python expert with code execution",
      "runtimeArn": "arn:aws:bedrock-agentcore:...:coder",
      "pattern": "strands-single-agent",
      "icon": "💻"
    }
  ],
  "defaultAgent": "orchestrator"
}
```

#### Step 4.2: Create Agent Selector Component

`frontend/src/components/chat/AgentSelector.tsx`:
- Dropdown with agent names, descriptions, and icons
- Persists selection to localStorage
- Shows current agent clearly

#### Step 4.3: Update ChatInterface

- Load agents from config
- Show agent selector in header
- Create client with selected agent's runtime ARN
- Handle agent switching (clear messages, new session)

## Deployment Order

### Phase 1: Deploy Specialist Agents
1. ✅ Colorado (already deployed)
2. Deploy UMich
3. Deploy Coder
4. Test each individually

### Phase 2: Deploy Orchestrator
1. Create orchestrator pattern
2. Deploy orchestrator stack
3. Test orchestrator routing

### Phase 3: Update Frontend
1. Update aws-exports.json with all 4 agents
2. Add agent selector component
3. Deploy frontend
4. Test full multi-agent experience

## Testing Strategy

### Test Each Specialist Agent
- **Colorado**: "Tell me about your cat" → Should respond about Napoleon
- **UMich**: "What time is it?" → Should use current_time tool
- **UMich**: "Fetch https://example.com" → Should use http_request tool
- **Coder**: "Calculate 123 * 456" → Should execute Python code

### Test Orchestrator Routing
- "Tell me about Denver" → Should route to Colorado
- "What's the current time?" → Should route to UMich
- "Calculate the factorial of 10" → Should route to Coder
- "What's 2+2?" → Should answer directly (simple math)
- "Tell me about Napoleon and then calculate 5!" → Should route to both

### Test Frontend
- Can select each agent from dropdown
- Each agent responds with correct personality
- Switching agents clears conversation
- Memory persists across agents (preferences)

## File Structure

```
patterns/
├── strands-colorado-agent/     ✅ Done
│   ├── colorado_agent.py
│   ├── requirements.txt
│   └── Dockerfile
├── strands-umich-agent/        📋 To create
│   ├── umich_agent.py
│   ├── requirements.txt
│   └── Dockerfile
├── strands-coder-agent/        📋 To create
│   ├── coder_agent.py
│   ├── requirements.txt
│   └── Dockerfile
└── strands-orchestrator-agent/ 📋 To create
    ├── orchestrator_agent.py
    ├── requirements.txt
    └── Dockerfile
```

## Key Implementation Details

### Memory Sharing
All agents share:
- User preferences: `/preferences/{actorId}`
- Facts: `/facts/{actorId}`
- Same `actor_id` (user ID)

Each agent has unique:
- Session prefix: `colorado_`, `umich_`, `coder_`, `orchestrator_`
- Conversation history

### Authentication Flow
1. User logs in via Cognito (frontend)
2. Frontend gets JWT access token
3. Frontend sends token to selected agent runtime
4. Agent extracts user ID from JWT via `extract_user_id_from_context`
5. Orchestrator passes same token when invoking specialist agents

### Error Handling
- Orchestrator catches errors from specialist invocations
- Returns helpful error messages to user
- Logs errors for debugging
- Fails loudly (no silent fallbacks)

## Next Steps

1. **Get approval** on this architecture
2. **Adapt UMich agent** (Phase 1, Step 1)
3. **Adapt Coder agent** (Phase 1, Step 2)
4. **Deploy specialists** (Phase 1, Step 3)
5. **Create orchestrator** (Phase 2)
6. **Update frontend** (Phase 3)
7. **Test everything** (Phase 4)

## Questions

1. Should orchestrator always be the default agent in UI?
2. Any specific routing logic preferences for orchestrator?
3. Should orchestrator be able to invoke multiple agents in sequence?
4. Any additional tools needed for orchestrator beyond the 3 agent tools?

Ready to proceed?
