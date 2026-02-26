# Multi-Agent UI Integration Plan

## Current State

### Backend
- ✅ Colorado agent deployed and working at runtime ARN
- ✅ Shared memory configured (all agents will share preferences/facts)
- ✅ Pattern structure established: `patterns/strands-colorado-agent/`
- 📋 UMich agent ready to adapt (has tools from strands)
- 📋 Coder agent ready to adapt (needs Code Interpreter)

### Frontend
- Single runtime ARN loaded from `aws-exports.json`
- No agent selection UI
- Hardcoded to use one agent pattern
- Configuration loaded in `ChatInterface.tsx`

## Goal

Enable users to select which agent to chat with from the UI, with each agent having its own runtime and personality.

## Architecture Options

### Option 1: Multiple Runtimes (Recommended by MULTI_AGENT_INTEGRATION_PLAN.md)

**Backend**: Deploy each agent as a separate runtime
- `patterns/strands-colorado-agent/` → Runtime 1
- `patterns/strands-umich-agent/` → Runtime 2  
- `patterns/strands-coder-agent/` → Runtime 3

**Frontend**: Agent selector dropdown
- Load all runtime ARNs from config
- User selects agent from dropdown
- ChatInterface uses selected runtime ARN

**Pros**:
- Independent scaling per agent
- Clean separation of concerns
- Easy to add/remove agents
- Follows existing FAST pattern structure
- Each agent can have different dependencies

**Cons**:
- More infrastructure (3 runtimes)
- Requires CDK changes to deploy multiple runtimes
- Frontend needs agent selection UI

### Option 2: Single Runtime with Router

**Backend**: One runtime with router pattern
- `patterns/strands-multi-agent/router.py` routes to appropriate agent
- All agents in same container

**Frontend**: Agent selector or automatic routing
- Send agent preference in payload
- Router selects appropriate agent

**Pros**:
- Single deployment
- Shared dependencies
- Less infrastructure

**Cons**:
- More complex routing logic
- All agents must share dependencies
- Harder to scale individually
- Doesn't follow existing FAST pattern structure

## Recommended Approach: Option 1 (Multiple Runtimes)

Based on:
1. `MULTI_AGENT_INTEGRATION_PLAN.md` recommends separate patterns
2. Follows existing FAST architecture
3. Maximum flexibility and independence
4. Easier to test and debug

## Implementation Plan

### Phase 1: Backend - Deploy Additional Agents

#### Step 1.1: Adapt UMich Agent
- Create `patterns/strands-umich-agent/`
- Copy structure from `patterns/strands-colorado-agent/`
- Adapt agent code with UMich personality and tools
- Configure memory with `umich_` session prefix

#### Step 1.2: Adapt Coder Agent
- Create `patterns/strands-coder-agent/`
- Copy structure from `patterns/strands-colorado-agent/`
- Adapt agent code with Coder personality
- Add Code Interpreter tool access
- Configure memory with `coder_` session prefix

#### Step 1.3: Update CDK for Multiple Runtimes
Current CDK deploys one runtime based on `config.yaml`:
```yaml
backend:
  pattern: strands-colorado-agent
```

**Option A: Deploy Separate Stacks** (Simplest)
- Deploy each agent as separate stack
- `marodon-fast-colorado` (already deployed)
- `marodon-fast-umich` (new)
- `marodon-fast-coder` (new)
- Each has own runtime ARN

**Option B: Single Stack, Multiple Runtimes** (More complex)
- Modify `backend-stack.ts` to create multiple runtimes
- Read agent list from config
- Create runtime for each agent
- Output all runtime ARNs

**Recommendation**: Start with Option A (separate stacks) for simplicity

### Phase 2: Frontend - Add Agent Selection

#### Step 2.1: Update Configuration Schema
Modify `aws-exports.json` to support multiple agents:

```json
{
  "awsRegion": "us-east-1",
  "cognitoUserPoolId": "us-east-1_xxx",
  "cognitoClientId": "xxx",
  "cognitoDomain": "xxx.auth.us-east-1.amazoncognito.com",
  "agents": [
    {
      "id": "colorado",
      "name": "Colorado Teacher",
      "description": "Excited about teaching in Denver with cat Napoleon",
      "runtimeArn": "arn:aws:bedrock-agentcore:...",
      "pattern": "strands-single-agent"
    },
    {
      "id": "umich",
      "name": "UMich Assistant",
      "description": "Specialized assistant with tools",
      "runtimeArn": "arn:aws:bedrock-agentcore:...",
      "pattern": "strands-single-agent"
    },
    {
      "id": "coder",
      "name": "Code Assistant",
      "description": "Coding expert with Code Interpreter",
      "runtimeArn": "arn:aws:bedrock-agentcore:...",
      "pattern": "strands-single-agent"
    }
  ],
  "defaultAgent": "colorado"
}
```

#### Step 2.2: Update AgentCore Client Types
Modify `frontend/src/lib/agentcore-client/types.ts`:

```typescript
export interface AgentInfo {
  id: string;
  name: string;
  description: string;
  runtimeArn: string;
  pattern: AgentPattern;
}

export interface AgentCoreConfig {
  runtimeArn: string;
  region?: string;
  pattern: AgentPattern;
}
```

#### Step 2.3: Create Agent Selector Component
New file: `frontend/src/components/chat/AgentSelector.tsx`

Features:
- Dropdown/select component using shadcn Select
- Shows agent name and description
- Persists selection to localStorage
- Emits event when agent changes

#### Step 2.4: Update ChatInterface
Modify `frontend/src/components/chat/ChatInterface.tsx`:

1. Load all agents from config
2. Show AgentSelector component
3. Create AgentCoreClient with selected agent's runtime ARN
4. Handle agent switching (clear messages, new session)

#### Step 2.5: Update CDK Frontend Stack
Modify `frontend-stack.ts` to generate `aws-exports.json` with all agents:
- Read all deployed runtime ARNs from SSM parameters
- Generate agents array
- Deploy to S3/Amplify

### Phase 3: Testing

#### Test Checklist
- [ ] Each agent deploys successfully
- [ ] Frontend loads all agents from config
- [ ] Agent selector shows all agents
- [ ] Can switch between agents
- [ ] Each agent has correct personality
- [ ] Memory sharing works (preferences persist across agents)
- [ ] Session history is separate per agent
- [ ] Authentication works for all agents

## Detailed Implementation Steps

### Backend Changes

#### File: `infra-cdk/config.yaml`
```yaml
stack_name_base: marodon-fast

backend:
  agents:
    - pattern: strands-colorado-agent
      name: colorado
    - pattern: strands-umich-agent
      name: umich
    - pattern: strands-coder-agent
      name: coder
  deployment_type: docker
```

#### File: `infra-cdk/lib/backend-stack.ts`
- Loop through agents array
- Create runtime for each agent
- Store each runtime ARN in SSM with agent name
- Example: `/marodon-fast/runtime-arn-colorado`

### Frontend Changes

#### File: `frontend/src/components/chat/AgentSelector.tsx`
```tsx
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AgentInfo } from "@/lib/agentcore-client/types"

interface AgentSelectorProps {
  agents: AgentInfo[];
  selectedAgent: string;
  onAgentChange: (agentId: string) => void;
}

export function AgentSelector({ agents, selectedAgent, onAgentChange }: AgentSelectorProps) {
  return (
    <Select value={selectedAgent} onValueChange={onAgentChange}>
      <SelectTrigger className="w-[250px]">
        <SelectValue placeholder="Select an agent" />
      </SelectTrigger>
      <SelectContent>
        {agents.map((agent) => (
          <SelectItem key={agent.id} value={agent.id}>
            <div>
              <div className="font-medium">{agent.name}</div>
              <div className="text-xs text-muted-foreground">{agent.description}</div>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
```

#### File: `frontend/src/components/chat/ChatInterface.tsx`
```tsx
// Add state for agents and selected agent
const [agents, setAgents] = useState<AgentInfo[]>([]);
const [selectedAgentId, setSelectedAgentId] = useState<string>("");

// Load agents from config
useEffect(() => {
  async function loadConfig() {
    const response = await fetch("/aws-exports.json");
    const config = await response.json();
    
    setAgents(config.agents || []);
    setSelectedAgentId(config.defaultAgent || config.agents[0]?.id);
  }
  loadConfig();
}, []);

// Create client with selected agent
const selectedAgent = agents.find(a => a.id === selectedAgentId);
const agentClient = new AgentCoreClient({
  runtimeArn: selectedAgent?.runtimeArn,
  region: config.awsRegion,
  pattern: selectedAgent?.pattern
});

// Handle agent change
const handleAgentChange = (agentId: string) => {
  setSelectedAgentId(agentId);
  setMessages([]); // Clear conversation
  setSessionId(crypto.randomUUID()); // New session
  localStorage.setItem("selectedAgent", agentId);
};

// Render agent selector
<AgentSelector 
  agents={agents}
  selectedAgent={selectedAgentId}
  onAgentChange={handleAgentChange}
/>
```

## Deployment Strategy

### Recommended: Separate Stacks (Phased Approach)

#### Phase 1: Deploy UMich Agent
```bash
# Update config
cd infra-cdk
cp config.yaml config-colorado.yaml.backup
vim config.yaml  # Change to strands-umich-agent

# Deploy
cdk deploy --stack-name marodon-fast-umich

# Note runtime ARN
```

#### Phase 2: Deploy Coder Agent
```bash
# Update config
vim config.yaml  # Change to strands-coder-agent

# Deploy
cdk deploy --stack-name marodon-fast-coder

# Note runtime ARN
```

#### Phase 3: Update Frontend
```bash
# Manually update aws-exports.json with all runtime ARNs
# Or modify frontend-stack.ts to read from SSM

# Deploy frontend
cdk deploy --stack-name marodon-fast-frontend
```

## Questions for User

1. **Deployment Strategy**: 
   - Separate stacks (simpler, recommended)? 
   - Or single stack with multiple runtimes (more complex)?

2. **Agent Priority**: 
   - Which agent to deploy next: UMich or Coder?
   - Or deploy both?

3. **Frontend Changes**:
   - Should agent selector be in header or sidebar?
   - Auto-switch agents based on query, or manual selection only?

4. **Memory Behavior**:
   - Confirm: All agents share preferences/facts but separate conversation history?

5. **Testing**:
   - Test each agent individually before frontend changes?
   - Or deploy all agents then update frontend?

## Next Steps

1. **Get User Approval** on this plan
2. **Read agent files** in `agents/` directory to understand requirements
3. **Adapt next agent** (UMich or Coder based on priority)
4. **Deploy agent** as separate stack
5. **Test agent** individually
6. **Repeat** for remaining agent
7. **Update frontend** with agent selector
8. **Test** multi-agent experience

## References

- `MULTI_AGENT_INTEGRATION_PLAN.md` - Backend architecture
- `frontend/README.md` - Frontend development guide
- `docs/AGENT_CONFIGURATION.md` - Agent configuration patterns
- `COLORADO_AGENT_DEPLOYMENT.md` - Deployment reference
