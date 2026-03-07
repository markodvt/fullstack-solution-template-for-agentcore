# Agentic Data Exploration (ADE) Pattern

## Status
Planned - spec not yet written

## Source Repository
[AWS Guidance for Agentic Data Exploration on AWS](https://github.com/aws-solutions-library-samples/guidance-for-agentic-data-exploration-on-aws)

## Purpose

Integrate the proven Agentic Data Exploration solution with FAST Agent Gallery to provide enterprise governance, observability, and experimentation capabilities while preserving the original data exploration workflows and operational UIs.

## Strategic Approach: Dual-Mode Deployment

This pattern demonstrates a key FAST Agent Gallery capability: **wrapping existing agent solutions to add governance without disrupting operations**.

### Current ADE Architecture
- Strands agents (orchestrator + specialists) hosted on Fargate and Bedrock
- Data pipeline: S3 → SQS → Lambda → Bedrock Flow
- Neptune knowledge graph for data relationships
- Custom UIs for data exploration workflows
- Operational focus: process data, build knowledge graphs, answer queries

### Enhanced ADE with FAST Gallery
- **Same agents**, now hosted on AgentCore Runtime (instead of Fargate/Bedrock direct)
- **Same workflows**, preserved data pipeline and processing logic
- **Same UIs**, original ADE interfaces continue to work
- **Added capabilities**:
  - Agents visible in FAST Agent Gallery
  - Full observability: traces, spans, metrics, session history
  - Memory inspection across all agent interactions
  - Governance: audit trails, user feedback, compliance tracking
  - Experimentation: test agent variations, compare performance
  - Multi-channel access: use agents via Gallery UI, ADE workflows, or Connect

## Business Value

### For Data Teams
- Deploy proven data exploration solution faster
- Add enterprise governance without rebuilding
- Experiment with agent improvements safely
- Maintain operational workflows teams already know

### For Platform Teams
- Visibility into data exploration agents
- Centralized observability across all agents
- Governance and compliance for data access
- Reusable pattern for other domain solutions

### For the Enterprise
- Accelerate AI adoption with proven patterns
- Reduce risk through built-in governance
- Enable learning through experimentation
- Scale successful patterns across teams

## Technical Approach

### Phase 1: Agent Wrapping and Deployment

**Goal**: Host ADE agents on AgentCore Runtime while preserving functionality

**Steps**:
1. Extract Strands agent code from ADE repo
2. Wrap with AgentCore imports and `@app.entrypoint` decorators
3. Create FAST pattern directory: `patterns/ade-multi-agent/`
4. Configure agents for AgentCore Runtime deployment
5. Update CDK to deploy agents to Runtime (not Fargate)
6. Verify agents work via FAST Gallery chat interface

**Outcome**: ADE agents visible and usable in FAST Gallery

### Phase 2: Data Pipeline Integration

**Goal**: Connect AgentCore-hosted agents to existing ADE data pipeline

**Steps**:
1. Deploy Neptune knowledge graph via FAST CDK
2. Deploy S3 staging buckets for data ingestion
3. Configure SQS queues and Lambda triggers
4. Update agent code to interact with Neptune
5. Preserve Bedrock Flow orchestration patterns
6. Test end-to-end data processing workflow

**Outcome**: Agents process data through original ADE pipeline

### Phase 3: Unified UI and Workflows

**Goal**: Combine FAST Gallery observability with ADE operational UIs

**Steps**:
1. Deploy ADE UIs alongside FAST Gallery
2. Configure shared authentication (Cognito)
3. Add navigation between Gallery and ADE interfaces
4. Enable observability data in ADE UIs (optional)
5. Document dual-mode usage patterns

**Outcome**: Users can govern via Gallery, operate via ADE UIs

## Key Components

### Agents (from ADE repo)
- **Orchestrator Agent**: Routes queries to specialist agents
- **SQL Agent**: Generates and executes SQL queries
- **Graph Agent**: Queries Neptune knowledge graph
- **Analysis Agent**: Performs data analysis and visualization
- **Synthesis Agent**: Combines results and generates insights

### Infrastructure (merged from both repos)
- **AgentCore Runtime**: Host agents (replaces Fargate)
- **AgentCore Memory**: Store conversation history and insights
- **AgentCore Gateway**: Tool access via MCP
- **Neptune**: Knowledge graph database
- **S3**: Data staging and storage
- **SQS**: Job queue for data processing
- **Lambda**: Pipeline orchestration
- **FAST Gallery UI**: Governance and observability
- **ADE UIs**: Data exploration and workflow management

### Data Pipeline
```
CSV Files → S3 Bucket → SQS Queue → Lambda Trigger
    ↓
Bedrock Flow (orchestrator agent)
    ↓
Specialist Agents (SQL, Graph, Analysis)
    ↓
Neptune Knowledge Graph
    ↓
Query Interface (ADE UI + Gallery Chat)
```

## Integration Patterns

### Pattern 1: Agent Wrapping
```python
# Original ADE agent (Strands on Fargate)
from strands import Agent

agent = Agent(
    name="sql-agent",
    instructions="Generate SQL queries...",
    tools=[sql_tool]
)

# Wrapped for AgentCore
from strands import Agent
from agentcore import app

@app.entrypoint()
def handler(event, context):
    agent = Agent(
        name="sql-agent",
        instructions="Generate SQL queries...",
        tools=[sql_tool]
    )
    return agent.run(event['input'])
```

### Pattern 2: Dual-Channel Access
```
User Query via Gallery UI
    ↓
AgentCore Runtime → Orchestrator Agent
    ↓
Specialist Agents (hosted on Runtime)
    ↓
Response in Gallery + stored in Memory

Data Processing Job via ADE Workflow
    ↓
SQS → Lambda → Bedrock Flow
    ↓
Same Orchestrator Agent (hosted on Runtime)
    ↓
Same Specialist Agents
    ↓
Results in Neptune + observable in Gallery
```

### Pattern 3: Observability Integration
```
Agent Execution (any channel)
    ↓
AgentCore Runtime generates OTEL traces
    ↓
CloudWatch Logs (system of record)
    ↓
FAST Gallery Observability Dashboard
    ↓
View traces, spans, metrics for all interactions
```

## Benefits of This Approach

### Preserves Investment
- Existing ADE code and workflows continue to work
- No need to rebuild proven data exploration logic
- Teams keep familiar interfaces and processes

### Adds Governance
- All agent interactions visible in Gallery
- Audit trails for compliance
- User feedback and quality tracking
- Memory inspection for data access patterns

### Enables Experimentation
- Test agent variations without disrupting operations
- Compare performance across different approaches
- Iterate on prompts and tools safely
- Learn what works before scaling

### Scales Across Use Cases
- Same pattern works for IDP, customer support, etc.
- Reusable approach for any existing agent solution
- Accelerates adoption of proven patterns
- Reduces risk through incremental enhancement

## Questions to Resolve

1. **Agent State Management**: How do we handle agent state that was previously managed by Fargate?
2. **Performance**: Does AgentCore Runtime match Fargate performance for data processing workloads?
3. **Cost**: What's the cost comparison between Fargate and Runtime hosting?
4. **Migration Path**: Can we run both versions (Fargate + Runtime) during transition?
5. **Tool Compatibility**: Do all ADE tools work with AgentCore Gateway?
6. **Neptune Access**: How do agents authenticate to Neptune from Runtime?
7. **UI Integration**: Should we merge UIs or keep them separate with navigation?
8. **Data Pipeline**: Can we trigger Runtime agents from SQS/Lambda as easily as Fargate?

## Success Criteria

### Technical Success
- [ ] ADE agents deployed to AgentCore Runtime
- [ ] All agent functionality preserved
- [ ] Data pipeline processes data end-to-end
- [ ] Neptune integration working
- [ ] Agents visible in FAST Gallery
- [ ] Observability data captured for all interactions

### User Success
- [ ] Data teams can use ADE workflows as before
- [ ] Platform teams can observe all agent activity
- [ ] Governance teams can audit data access
- [ ] Developers can experiment with agent improvements
- [ ] Documentation enables self-service deployment

### Business Success
- [ ] Deployment time < 2 hours (vs. weeks to build from scratch)
- [ ] Zero disruption to existing ADE users
- [ ] Governance capabilities meet compliance requirements
- [ ] Pattern reusable for other domain solutions

## Related Specs

- [Use Case Patterns Framework](../use-case-patterns/) - General approach for domain patterns
- [Multi-Agent Orchestration Pattern](../multi-agent-orchestration-pattern/) - Foundation for orchestrator + specialists
- [IDP Pattern](../idp-pattern/) - Similar wrapping approach for document processing
- [Enhanced Agent UI](../enhanced-agent-ui/) - Gallery interface for agent visibility

## Next Steps

1. Clone ADE repo and analyze agent code structure
2. Identify all agents, tools, and dependencies
3. Create detailed requirements document
4. Design agent wrapping approach
5. Plan phased implementation
6. Document migration guide for ADE users
