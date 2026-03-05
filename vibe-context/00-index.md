# FAST Development Guide Index

This is your navigation hub for detailed guidance. Most docs are available on-demand to keep context lean.

## Core Rules (Always Active)

See `core-rules.md` for essential coding standards, conventions, and workflow practices.

## Architecture & Components

**AgentCore Architecture** - Detailed component definitions, APIs, integration patterns
→ Use `#[[file:.kiro/steering/architecture/agentcore.md]]` when working with AgentCore services

**Strands & CDK** - Strands agent development, CDK patterns, Docker builds, tool registration
→ Auto-loads when working in `infra-cdk/` or with strands/patterns

**Memory** - AgentCore Memory namespaces, strategies, event storage patterns
→ Use `#[[file:.kiro/steering/backend/memory.md]]` when implementing memory features

## Backend Development

**API Patterns** - Lambda creation, API Gateway integration, deployment configuration
→ Auto-loads when working in `infra-cdk/lambdas/`

**Observability** - CloudWatch metrics, OTEL instrumentation, tracing setup
→ Use `#[[file:.kiro/steering/backend/observability.md]]` or AWS docs MCP server

## Frontend Development

**UI Troubleshooting** - Browser console debugging, CORS issues, common error patterns
→ Auto-loads when working in `frontend/`

## Process & Documentation

**Session Documentation** - Guidelines for session summaries and commit messages
→ Use `#[[file:.kiro/steering/process/session-docs.md]]` when documenting work sessions

## Using This Index

- Links with `#[[file:...]]` can be referenced in chat to load specific guidance
- Some docs auto-load based on file patterns (e.g., working in `frontend/` loads UI guide)
- For AWS services (Bedrock, AgentCore), prefer using the AWS docs MCP server for latest info
- Keep context lean - only load what you need for the current task
