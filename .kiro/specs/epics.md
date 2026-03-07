# FAST Agent Gallery - Epic Roadmap

This document tracks the feature roadmap for FAST Agent Gallery, organizing specs into thematic epics and maintaining a backlog of future capabilities.

For the overall vision and product tenets, see [../.kiro/README.md](../.kiro/README.md).

---

## Epic Overview

| # | Epic | Description | Status |
|---|------|-------------|--------|
| 1 | **Multi-Agent Foundation** | Deploy and manage multiple specialized agents with orchestration patterns | 🚧 In Progress |
| 2 | **Observability & Debugging** | Comprehensive visibility into agent behavior, traces, metrics, and infrastructure | 🚧 In Progress |
| 3 | **Memory & Context Management** | Long-term memory, knowledge graphs, and context across sessions | 🚧 In Progress |
| 4 | **Tool Ecosystem** | Extensible tool marketplace with MCP servers, API wrappers, and custom tools | 📋 Planned |
| 5 | **Governance & Compliance** | Evals, policies, guardrails, RBAC, and audit trails for safe AI adoption | 💡 Backlog |
| 6 | **Multi-Channel Access** | Expose agents via Connect, APIs, CLI, workflows, Slack/Teams | 📋 Planned |
| 7 | **Use Case Acceleration** | Domain-specific templates for lending, data exploration, customer support | 📋 Planned |
| 8 | **Developer Experience** | Kiro Powers, meta-steering, IDE integration, and deployment enhancements | 💡 Backlog |
| 9 | **Performance & Scale** | Caching, cost controls, optimization tools for production workloads | 💡 Backlog |

**Status Legend:**
- ✅ Completed - Deployed and available
- 🚧 In Progress - Active development with specs
- 📋 Planned - Specs exist, implementation not started
- 💡 Backlog - Concepts captured, specs not written

---

## Epic Structure

Each epic represents a major capability theme. Features within an epic may be:
- **Completed**: Deployed and available
- **In Progress**: Active development with spec in `specs/`
- **Planned**: Spec exists but implementation not started
- **Backlog**: Concept captured, spec not yet written

---

## Epic 1: Multi-Agent Foundation

**Theme**: Enable teams to deploy and manage multiple specialized agents with proper orchestration patterns.

**Business Value**: Reduces time-to-production from months to hours by providing production-ready multi-agent infrastructure.

### Features

#### ✅ Completed
- Basic agent deployment (single Strands agent pattern)
- AgentCore Runtime integration
- Cognito authentication
- Basic chat interface

#### 🚧 In Progress
- **Multi-Agent Orchestration Pattern** → [specs/multi-agent-orchestration-pattern/](multi-agent-orchestration-pattern/)
  - Unified pattern directory structure (orchestrator + specialists)
  - Shared backend resources (Memory, Gateway, Code Interpreter)
  - Agent discovery mechanism
  - Orchestrator-to-specialist communication

#### 📋 Planned
- **Use Case Patterns** → [specs/use-case-patterns/](use-case-patterns/)
  - Template patterns for common use cases
  - Domain-specific agent configurations
  - Reusable tool bundles per use case

#### 💡 Backlog
- LangGraph multi-agent pattern
- Agent versioning and A/B testing
- Agent performance benchmarking
- Cross-agent conversation handoffs

---

## Epic 2: Observability & Debugging

**Theme**: Provide comprehensive visibility into agent behavior for debugging, optimization, and governance.

**Business Value**: Enables teams to understand what agents are doing, identify issues quickly, and continuously improve performance.

### Features

#### ✅ Completed
- Basic session logging
- CloudWatch Logs integration
- OTEL span collection

#### 🚧 In Progress
- **Enhanced Agent UI** → [specs/enhanced-agent-ui/](enhanced-agent-ui/)
  - Agent gallery with tiles and metadata
  - Agent details page with code viewer
  - Memory visualization page
  - Standalone observability dashboard
  - Inline chat observability
  - Session/trace/span visualization

- **Observability Data Strategy** → [specs/observability-data-strategy/](observability-data-strategy/)
  - Multi-pattern support for different team needs
  - Query performance optimization
  - CloudWatch deep linking
  - Configurable data persistence strategies

#### 📋 Planned
- Real-time agent monitoring dashboard
- Alert configuration for agent failures
- Cost tracking per agent/session
- Comparative analysis across agents

#### 💡 Backlog
- **Infrastructure Observability Tab**
  - View deployed CloudFormation stacks (nested)
  - Resource inventory (Lambda, DynamoDB, S3, etc.)
  - Stack drift detection
  - Resource cost breakdown
- Distributed tracing across agent calls
- Performance profiling and bottleneck detection
- Anomaly detection for agent behavior
- Session replay functionality
- Export observability data to external systems

---

## Epic 3: Memory & Context Management

**Theme**: Enable agents to maintain context across sessions and share knowledge appropriately.

**Business Value**: Agents become more useful over time by remembering user preferences, past interactions, and learned information.

### Features

#### ✅ Completed
- AgentCore Memory integration (short-term)
- Session-based conversation history
- Actor ID extraction from JWT tokens

#### 🚧 In Progress
- Long-term memory with namespace isolation
- Memory query and visualization UI
- Agent-specific memory prefixing

#### 📋 Planned
- Memory search and filtering
- Memory lifecycle management (TTL, archival)
- Cross-agent memory sharing policies
- Memory export/import

#### 💡 Backlog
- Semantic memory search
- Memory summarization for long contexts
- User-controlled memory deletion
- Memory analytics (what agents remember most)
- Knowledge graph integration
- RAG (Retrieval Augmented Generation) patterns

---

## Epic 4: Tool Ecosystem

**Theme**: Expand agent capabilities through a rich, extensible tool ecosystem.

**Business Value**: Agents can perform real work by integrating with enterprise systems, data sources, and services.

### Features

#### ✅ Completed
- Code Interpreter integration
- AgentCore Gateway (MCP protocol)
- Inline tool definitions
- Basic tool execution tracking

#### 📋 Planned
- Tool marketplace/registry
- Tool usage analytics
- Tool versioning
- Tool access control policies

#### 💡 Backlog
- REST API wrapper tools (auto-generate from OpenAPI specs)
- Database connector tools (SQL, NoSQL)
- File system tools (S3, local)
- Email/notification tools
- Calendar/scheduling tools
- Web scraping tools
- Custom MCP server templates
- Tool composition (chain multiple tools)
- Tool testing framework
- Tool performance monitoring

---

## Epic 5: Governance & Compliance

**Theme**: Enable safe, compliant AI adoption with proper guardrails and audit trails.

**Business Value**: Reduces risk and enables deployment in regulated industries by providing built-in governance controls.

### Features

#### ✅ Completed
- User authentication (Cognito)
- Session audit logs
- JWT token validation

#### 📋 Planned
- User feedback collection and analysis
- Session rating system
- Feedback-driven agent improvements

#### 💡 Backlog
- **Evaluation Framework**
  - Automated agent testing (accuracy, safety, performance)
  - Regression testing for agent changes
  - Benchmark datasets per use case
- **Policy Engine**
  - Define and enforce agent behavior policies
  - Content filtering and guardrails
  - Rate limiting per user/agent
- **Identity & Access Management**
  - Role-based access control (RBAC)
  - Agent-level permissions
  - Tool-level permissions
  - Data access policies
- **Compliance Reporting**
  - Audit trail export
  - Compliance dashboard
  - PII detection and handling
  - Data residency controls
- **Guardrails Integration**
  - AWS Bedrock Guardrails
  - Custom guardrail policies
  - Real-time content filtering

---

## Epic 6: Multi-Channel Access

**Theme**: Expose agents through multiple interfaces beyond the web UI.

**Business Value**: Meets users where they are (voice, chat, workflows, APIs) rather than forcing a single interaction model.

### Features

#### ✅ Completed
- Web UI (React frontend)
- Direct AgentCore Runtime API access

#### 📋 Planned
- **Amazon Connect Integration** → [specs/connect-admin/](connect-admin/)
  - Voice interface for agents
  - Chat interface via Connect
  - Admin agent for platform management
  - Dev agent for codebase interaction
  - User agent for alternative UI channel

#### 💡 Backlog
- **REST API Layer**
  - Public API for agent invocation
  - API key management
  - Rate limiting and quotas
  - API documentation (OpenAPI spec)
- **CLI Interface**
  - Command-line agent interaction
  - Scripting and automation support
  - CI/CD integration
- **Workflow Integration**
  - AWS Step Functions integration
  - EventBridge triggers
  - Scheduled agent execution
- **Slack/Teams Integration**
  - Bot interface for agents
  - Notification delivery
  - Interactive commands
- **Email Interface**
  - Email-triggered agent execution
  - Response delivery via email

---

## Epic 7: Use Case Acceleration

**Theme**: Provide domain-specific templates and patterns that accelerate specific business use cases by integrating proven open-source solutions with FAST Agent Gallery's governance and observability.

**Business Value**: Reduces time-to-value for common use cases by providing pre-built patterns with production-ready agents, while adding enterprise governance, observability, and experimentation capabilities that standalone solutions lack.

**Strategic Approach**: Wrap existing open-source agent solutions (Strands on Fargate, LangGraph, etc.) with AgentCore hosting, making them visible in FAST Agent Gallery for governance and experimentation while preserving their original workflows and UIs. This creates a "best of both worlds" deployment where users get domain-specific functionality plus enterprise-grade observability.

### Features

#### 📋 Planned
- **Use Case Patterns Framework** → [specs/use-case-patterns/](use-case-patterns/)
  - Template patterns for common use cases
  - Domain-specific agent configurations
  - Reusable tool bundles per use case
  - Integration guide for wrapping existing agents

- **Agentic Data Exploration (ADE) Pattern** → [specs/ade-pattern/](ade-pattern/)
  - Source: [AWS Guidance for Agentic Data Exploration](https://github.com/aws-solutions-library-samples/guidance-for-agentic-data-exploration-on-aws)
  - Wrap Strands agents (orchestrator + specialists) with AgentCore hosting
  - Preserve existing workflows: S3 → SQS → Lambda → Bedrock Flow
  - Add Neptune knowledge graph integration
  - Deploy agents as FAST pattern while maintaining ADE UIs
  - Enable governance/observability via Gallery, operations via ADE workflows
  - Phase 1: Agent wrapping and AgentCore deployment
  - Phase 2: Neptune and data pipeline integration
  - Phase 3: Unified UI combining Gallery + ADE interfaces

- **Intelligent Document Processing (IDP) Pattern** → [specs/idp-pattern/](idp-pattern/)
  - Source: [GenAI IDP Accelerator](https://github.com/cdklabs/genai-idp)
  - Wrap document processing agents with AgentCore hosting
  - Preserve IDP workflows and operational UIs
  - Add FAST Gallery governance and observability
  - Enable experimentation with document processing agents
  - Deploy as unified stack: IDP functionality + Gallery visibility

- **Lending/Mortgage Use Case** → [specs/lending/](lending/)
  - Synthetic mortgage application generation
  - Document processing agents
  - Compliance checking
  - Application package assembly

#### 💡 Backlog
- **Customer Support Use Case**
  - Ticket classification
  - Response generation
  - Knowledge base integration
  - Wrap with AgentCore for governance
- **Code Review Use Case**
  - PR analysis
  - Code quality checks
  - Security scanning
  - Suggestion generation
- **Research Assistant Use Case**
  - Literature search
  - Summarization
  - Citation management
  - Report generation
- **Additional Open-Source Integrations**
  - Survey existing AWS/community agent solutions
  - Identify candidates for Gallery integration
  - Document wrapping patterns for different frameworks

---

## Epic 8: Developer Experience

**Theme**: Make it easy for developers to build, test, and deploy agents.

**Business Value**: Reduces friction in the development cycle, enabling faster iteration and experimentation.

### Features

#### ✅ Completed
- CDK deployment automation
- Local development setup
- Hot reload for frontend
- Auth bypass for local dev
- Kiro steering documentation

#### 📋 Planned
- Agent testing framework
- Local agent execution (without deployment)
- Agent debugging tools

#### 💡 Backlog
- **Kiro Powers for FAST**
  - Power: Convert local Strands agent to FAST pattern
  - Power: Generate use-case pattern from PRFAQ
  - Power: Scaffold new agent from template
  - Power: Generate tool from OpenAPI spec
- **Meta-Steering**
  - Capture best practices automatically
  - Generate steering from successful sessions
  - Share patterns across teams
- **Agent IDE Integration**
  - VS Code extension
  - Inline agent testing
  - Observability in IDE
- **Deployment Enhancements**
  - Blue/green deployments
  - Rollback capabilities
  - Multi-region deployment
  - Environment management (dev/staging/prod)
- **Documentation Generation**
  - Auto-generate agent docs from code
  - API documentation
  - Architecture diagrams from CDK

---

## Epic 9: Performance & Scale

**Theme**: Ensure FAST can handle production workloads efficiently and cost-effectively.

**Business Value**: Enables teams to scale from prototype to production without architectural rewrites.

### Features

#### 📋 Planned
- Performance benchmarking suite
- Cost optimization recommendations
- Resource right-sizing

#### 💡 Backlog
- **Caching Strategies**
  - Response caching for common queries
  - Tool result caching
  - Memory query caching
- **Concurrency Management**
  - Parallel agent execution
  - Request queuing
  - Load balancing
- **Cost Controls**
  - Budget alerts
  - Token usage limits
  - Automatic scaling policies
- **Performance Monitoring**
  - Latency tracking
  - Throughput metrics
  - Resource utilization
- **Optimization Tools**
  - Prompt optimization suggestions
  - Model selection recommendations
  - Tool usage optimization

---

## Backlog: Future Epics

These are larger themes that may become full epics as they mature:

### Agent Marketplace
- Share agents across teams/organizations
- Agent templates and starter kits
- Community contributions
- Rating and review system

### Advanced AI Capabilities
- Multi-modal agents (vision, audio)
- Agent fine-tuning workflows
- Custom model integration
- Prompt engineering tools

### Enterprise Integration
- SSO integration (SAML, OIDC)
- VPC deployment options
- Private endpoint support
- Hybrid cloud deployment

### Analytics & Insights
- Usage analytics dashboard
- ROI calculation
- User behavior analysis
- Agent effectiveness scoring

---

## Feature Status Legend

- ✅ **Completed**: Deployed and available in current version
- 🚧 **In Progress**: Active development, spec exists in `specs/`
- 📋 **Planned**: Spec exists, implementation not started
- 💡 **Backlog**: Concept captured, spec not yet written

---

## Contributing to the Roadmap

To propose a new feature:

1. Add it to the appropriate epic's backlog section
2. Create a placeholder directory in `specs/` if it's a major feature
3. Write a brief concept in the placeholder's `README.md`
4. When ready to spec, create `requirements.md`, `design.md`, and `tasks.md`

For questions about roadmap priorities, see the program lead.