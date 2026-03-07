# FAST Agent Gallery - Program Overview

## Vision


*Scale your AI
*Make AI governance visible to the teams closest to your business 
*Arm teams with 
*Accelerate AI adoption by fe
*Well governed AI experimentation on the way to scaled production.*

**Accelerate well-governed AI adoption for teams closest to business problems.**

In the face of rapid AI disruption, enterprises face an impossible choice: move fast and risk governance failures, or move slowly and fall behind competitors. Leading organizations are becoming *learning organizations* that experiment safely at scale, while others remain stuck in planning phases waiting for centralized governance to catch up.

FAST Agent Gallery bridges this gap by providing a reusable starter kit that enables AI teams to:
- Deploy production-ready multi-agent systems quickly
- Maintain observability and governance from day one
- Iterate and learn through well-instrumented experiments
- Scale successful patterns across the enterprise

## The Problem

Traditional governance mechanisms fail to keep pace with AI innovation:

- **Heavy governance chokes experimentation**: Too many people can say "no" without offering "here's how"
- **Centralized bottlenecks**: Platform teams can't keep up with the rate of change in AI capabilities
- **Lack of reusable patterns**: Every team rebuilds the same infrastructure (auth, observability, memory, deployment)
- **Poor visibility**: Teams can't observe, debug, or improve their agents effectively
- **Slow learning cycles**: Without proper instrumentation, teams can't learn what works

While nimble startups accumulate real-world learnings from heavy AI usage, regulated enterprises risk falling behind.

## The Solution

FAST Agent Gallery is a **fullstack starter kit** that provides:

### Core Infrastructure
- **AgentCore Runtime**: Deploy Strands or LangGraph agents on AWS Bedrock AgentCore
- **Multi-agent orchestration**: Orchestrator + specialist agent patterns out of the box
- **Long-term memory**: AgentCore Memory integration with namespace isolation
- **Tool ecosystem**: Code Interpreter, Gateway (MCP), inline tools, and extensible patterns
- **Authentication**: Cognito-based user management with JWT token flows

### Developer Experience
- **React UI**: Agent gallery, chat interface, memory explorer, observability dashboard
- **CDK deployment**: Infrastructure-as-code with configurable patterns
- **Local development**: Fast iteration with hot reload and auth bypass options
- **Kiro steering**: Best practices and patterns captured as reusable guidance

### Observability & Governance
- **Session tracking**: View all agent interactions with full trace data
- **OTEL integration**: OpenTelemetry spans for performance analysis
- **Metrics dashboard**: Token usage, success rates, tool usage across agents
- **Memory inspection**: Audit what agents remember across sessions
- **User feedback**: Capture and analyze user satisfaction

### Extensibility
- **Multiple patterns**: Support different agent architectures via configuration
- **Channel flexibility**: Same agents accessible via UI, Connect, workflows, APIs
- **Use-case templates**: Lending, data exploration, and domain-specific patterns
- **Tool integration**: Easy addition of new tools and MCP servers

## Product Tenets

1. **Learning over Planning**: Ship instrumented experiments that generate insights, not perfect solutions that take months
2. **Governance through Visibility**: Make agent behavior observable and auditable rather than blocking innovation
3. **Reusable Patterns**: Capture successful approaches as configurable patterns, not one-off implementations
4. **Teams Own Their Agents**: AI engineers manage their 5-10 agents with full control and visibility
5. **Extensible by Default**: Every component should support multiple patterns and integration points
6. **Production-Ready from Day One**: Include auth, observability, and deployment automation from the start

## Target Users

### Primary: AI Engineers
- Own 5-10 specific agents tied to business use cases
- Need fast iteration cycles with full observability
- Want to experiment safely without heavy governance overhead
- Require production-ready infrastructure without building from scratch

### Secondary: Platform Teams
- Provide centralized observability across all company agents
- Set governance guardrails without blocking innovation
- Monitor costs, performance, and compliance at scale
- Enable self-service agent deployment for business teams

### Tertiary: Business Stakeholders
- Understand what AI agents are doing and how well they perform
- Provide feedback on agent interactions
- See ROI through metrics and usage patterns
- Trust that governance and security are maintained

## Success Metrics

- **Time to First Agent**: Deploy a working multi-agent system in < 1 hour
- **Iteration Speed**: Make changes and see results in < 5 minutes (local dev)
- **Observability Coverage**: 100% of agent interactions captured with traces
- **Pattern Reuse**: New use cases leverage existing patterns vs. building from scratch
- **Learning Velocity**: Teams can answer "what's working?" within days, not months

## Architecture Principles

- **CloudWatch as System of Record**: Don't duplicate AWS observability, integrate with it
- **Serverless First**: Minimize operational overhead with Lambda, S3, and managed services
- **Configuration over Code**: Use config files to select patterns, not code changes
- **Multi-Pattern Support**: Same repo supports single agent, multi-agent, and future patterns
- **Channel Agnostic**: Agents work via UI, Connect, workflows, or direct API calls

---

For detailed feature specifications, see [specs/epics.md](specs/epics.md).

For deployment instructions, see [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md).
