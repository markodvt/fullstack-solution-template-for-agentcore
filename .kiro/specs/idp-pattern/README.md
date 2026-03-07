# Intelligent Document Processing (IDP) Pattern

## Status
Planned - spec not yet written

## Source Repository
[GenAI IDP Accelerator](https://github.com/cdklabs/genai-idp)

## Purpose

Integrate the GenAI Intelligent Document Processing accelerator with FAST Agent Gallery to add enterprise governance, observability, and experimentation capabilities while preserving the original document processing workflows and operational UIs.

## Strategic Approach: Governance-Enhanced IDP

This pattern demonstrates how FAST Agent Gallery can enhance existing document processing solutions by adding visibility and governance without disrupting operational workflows.

### Current IDP Architecture
- Document processing agents (classification, extraction, validation)
- Workflow orchestration for multi-step processing
- Integration with document storage (S3)
- Custom UIs for document management
- Operational focus: process documents, extract data, validate results

### Enhanced IDP with FAST Gallery
- **Same agents**, now hosted on AgentCore Runtime
- **Same workflows**, preserved document processing pipelines
- **Same UIs**, original IDP interfaces continue to work
- **Added capabilities**:
  - Agents visible in FAST Agent Gallery
  - Full observability: trace document processing steps
  - Memory inspection: see what agents learned from documents
  - Governance: audit document access, track processing decisions
  - Experimentation: test extraction improvements, compare accuracy
  - Multi-channel access: process via IDP workflows or Gallery chat

## Business Value

### For Document Processing Teams
- Deploy proven IDP solution with added governance
- Experiment with extraction improvements safely
- Maintain operational workflows teams already know
- Add compliance tracking without rebuilding

### For Compliance Teams
- Visibility into all document processing activities
- Audit trails for sensitive document access
- Track agent decisions and confidence scores
- Ensure PII handling meets requirements

### For Platform Teams
- Centralized observability across document agents
- Reusable pattern for other document use cases
- Governance framework for AI-powered processing
- Experimentation platform for accuracy improvements

## Technical Approach

### Phase 1: Agent Wrapping and Deployment

**Goal**: Host IDP agents on AgentCore Runtime while preserving functionality

**Steps**:
1. Extract agent code from IDP repo
2. Wrap with AgentCore imports and entrypoint decorators
3. Create FAST pattern directory: `patterns/idp-multi-agent/`
4. Configure agents for AgentCore Runtime deployment
5. Update CDK to deploy agents to Runtime
6. Verify agents work via FAST Gallery chat interface

**Outcome**: IDP agents visible and usable in FAST Gallery

### Phase 2: Document Pipeline Integration

**Goal**: Connect AgentCore-hosted agents to existing IDP workflows

**Steps**:
1. Configure S3 buckets for document ingestion
2. Set up event triggers for document processing
3. Update agent code to access document storage
4. Preserve workflow orchestration patterns
5. Test end-to-end document processing
6. Validate extraction accuracy matches original

**Outcome**: Agents process documents through original IDP pipeline

### Phase 3: Unified UI and Governance

**Goal**: Combine FAST Gallery observability with IDP operational UIs

**Steps**:
1. Deploy IDP UIs alongside FAST Gallery
2. Configure shared authentication (Cognito)
3. Add navigation between Gallery and IDP interfaces
4. Enable compliance reporting via Gallery observability
5. Document dual-mode usage patterns

**Outcome**: Users can govern via Gallery, operate via IDP UIs

## Key Components

### Agents (from IDP repo)
- **Classification Agent**: Categorizes document types
- **Extraction Agent**: Extracts structured data from documents
- **Validation Agent**: Validates extracted data quality
- **Enrichment Agent**: Enhances data with additional context
- **Orchestrator Agent**: Coordinates multi-step processing

### Infrastructure (merged from both repos)
- **AgentCore Runtime**: Host agents
- **AgentCore Memory**: Store processing history and learnings
- **AgentCore Gateway**: Tool access for document operations
- **S3**: Document storage and staging
- **EventBridge**: Document processing triggers
- **Lambda**: Pipeline orchestration
- **FAST Gallery UI**: Governance and observability
- **IDP UIs**: Document management and workflow control

### Document Processing Pipeline
```
Documents → S3 Bucket → EventBridge Trigger
    ↓
Orchestrator Agent (on Runtime)
    ↓
Classification → Extraction → Validation → Enrichment
    ↓
Structured Data Output
    ↓
Observable in Gallery + Accessible via IDP UI
```

## Integration Patterns

### Pattern 1: Document Processing with Observability
```
Document Upload (via IDP UI or S3)
    ↓
EventBridge → Lambda → AgentCore Runtime
    ↓
Orchestrator Agent coordinates specialists
    ↓
Each step generates OTEL traces
    ↓
Results stored + traces in CloudWatch
    ↓
View processing details in Gallery Observability
```

### Pattern 2: Compliance Tracking
```
Sensitive Document Processing
    ↓
Agent interactions captured in Memory
    ↓
Audit trail: who accessed, what was extracted, when
    ↓
Compliance dashboard in Gallery
    ↓
Export audit logs for regulatory reporting
```

### Pattern 3: Accuracy Experimentation
```
Test Extraction Improvement
    ↓
Deploy agent variation as new pattern
    ↓
Process same documents through both versions
    ↓
Compare results in Gallery Observability
    ↓
Measure accuracy, latency, cost differences
    ↓
Promote winning version to production
```

## Benefits of This Approach

### Preserves Investment
- Existing IDP code and workflows continue to work
- No need to rebuild proven document processing logic
- Teams keep familiar interfaces and processes

### Adds Governance
- All document processing visible in Gallery
- Audit trails for compliance and security
- Track PII handling and sensitive data access
- User feedback on extraction quality

### Enables Experimentation
- Test extraction improvements without disrupting operations
- Compare accuracy across different approaches
- Iterate on prompts and validation rules safely
- Learn what works before scaling

### Scales Across Document Types
- Same pattern works for invoices, contracts, forms, etc.
- Reusable approach for any document processing need
- Accelerates adoption of proven patterns
- Reduces risk through incremental enhancement

## Use Cases

### Invoice Processing
- Extract line items, totals, vendor information
- Validate against purchase orders
- Route for approval based on extracted data
- Track processing accuracy and exceptions

### Contract Analysis
- Extract key terms, dates, obligations
- Identify risks and non-standard clauses
- Compare against standard templates
- Maintain audit trail of contract reviews

### Form Processing
- Extract structured data from PDFs
- Validate completeness and accuracy
- Enrich with external data sources
- Track processing metrics and errors

### Medical Records
- Extract patient information, diagnoses, treatments
- Validate against medical coding standards
- Ensure HIPAA compliance through audit trails
- Track extraction accuracy for quality assurance

## Questions to Resolve

1. **Document Storage**: How do agents access documents from Runtime? Direct S3 or via Gateway?
2. **Processing Scale**: Can Runtime handle high-volume document processing?
3. **Accuracy Tracking**: How do we measure and compare extraction accuracy?
4. **PII Handling**: How do we ensure PII is properly handled in Memory and traces?
5. **Tool Compatibility**: Do all IDP tools work with AgentCore Gateway?
6. **UI Integration**: Should we merge UIs or keep them separate?
7. **Cost**: What's the cost comparison for document processing workloads?
8. **Migration Path**: Can we run both versions during transition?

## Success Criteria

### Technical Success
- [ ] IDP agents deployed to AgentCore Runtime
- [ ] All document processing functionality preserved
- [ ] Pipeline processes documents end-to-end
- [ ] Agents visible in FAST Gallery
- [ ] Observability data captured for all processing
- [ ] Extraction accuracy matches or exceeds original

### User Success
- [ ] Document teams can use IDP workflows as before
- [ ] Compliance teams can audit document access
- [ ] Platform teams can observe all agent activity
- [ ] Developers can experiment with improvements
- [ ] Documentation enables self-service deployment

### Business Success
- [ ] Deployment time < 2 hours
- [ ] Zero disruption to existing IDP users
- [ ] Governance capabilities meet compliance requirements
- [ ] Pattern reusable for other document types
- [ ] Measurable accuracy improvements through experimentation

## Related Specs

- [Use Case Patterns Framework](../use-case-patterns/) - General approach for domain patterns
- [ADE Pattern](../ade-pattern/) - Similar wrapping approach for data exploration
- [Multi-Agent Orchestration Pattern](../multi-agent-orchestration-pattern/) - Foundation for orchestrator + specialists
- [Enhanced Agent UI](../enhanced-agent-ui/) - Gallery interface for agent visibility

## Next Steps

1. Clone IDP repo and analyze agent code structure
2. Identify all agents, tools, and dependencies
3. Create detailed requirements document
4. Design agent wrapping approach
5. Plan phased implementation
6. Document migration guide for IDP users
7. Define accuracy measurement framework
