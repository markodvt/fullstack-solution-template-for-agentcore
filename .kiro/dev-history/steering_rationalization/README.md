# Steering Documentation Rationalization

**Date:** March 5, 2026
**Goal:** Streamline steering docs to protect context window while maintaining detailed guidance availability

## Problem Statement

The old steering structure had 12 docs totaling ~4,653 lines, all auto-loading into every conversation. This consumed significant context window space, leaving less room for actual code and problem-solving.

## Solution Approach

Implemented progressive disclosure strategy:
1. Lightweight index (auto-loaded) pointing to detailed docs
2. Core rules consolidated into single small doc (auto-loaded)
3. Detailed docs marked as manual inclusion or fileMatch-triggered
4. Eliminated redundancy with MCP servers (AWS docs)

## Results

### Before
- 12 files, ~4,653 lines total
- ~3,700+ lines auto-loaded every conversation
- Significant context window consumption
- Duplication with available MCP servers

### After
- 8 files in new structure
- ~80-130 lines auto-loaded (index + core-rules)
- ~97% reduction in auto-loaded content
- Detailed guidance available on-demand

## New Structure

```
.kiro/steering/
├── 00-index.md                    # 50 lines, auto-included
├── core-rules.md                  # 30 lines, auto-included
├── architecture/
│   ├── agentcore.md              # manual inclusion
│   └── strands-cdk.md            # fileMatch: infra-cdk/**
├── backend/
│   ├── api-patterns.md           # fileMatch: infra-cdk/lambdas/**
│   ├── memory.md                 # manual inclusion
│   └── observability.md          # manual inclusion
├── frontend/
│   └── ui-troubleshooting.md     # fileMatch: frontend/**
└── process/
    └── session-docs.md           # manual inclusion
```

## Key Changes

### Consolidated
- `AGENTS.md` + `coding-conventions.md` + `development-best-practices.md` → `core-rules.md`
- `strands.md` + `strands-and-cdk.md` → `architecture/strands-cdk.md`

### Converted to Manual Inclusion
- `agentcore-architecture.md` → `architecture/agentcore.md`
- `backend-api-patterns.md` → `backend/api-patterns.md`
- `memory.md` → `backend/memory.md`
- `observability.md` → `backend/observability.md`
- `session-documentation.md` → `process/session-docs.md`

### Converted to fileMatch
- `strands-cdk.md` - triggers on infra-cdk/** or strands/patterns
- `api-patterns.md` - triggers on infra-cdk/lambdas/**
- `ui-troubleshooting.md` - triggers on frontend/**

### Eliminated (Use MCP Instead)
- `mcp-documentation-access.md` - Advocated for MCP, now using AWS docs MCP server

## Progressive Disclosure Pattern

The index provides:
- Quick overview of available guidance
- Links using `#[[file:...]]` syntax for on-demand loading
- Clear indication of auto-loading vs manual docs
- Recommendation to use MCP servers for AWS services

## Usage Examples

### Auto-loaded (Always Available)
- Core rules and conventions
- Index for navigation

### On-Demand (Agent Loads When Needed)
```
User: "I need to work with AgentCore Memory"
Agent: Loads #[[file:.kiro/steering/backend/memory.md]]
```

### Context-Triggered (Auto-loads Based on Files)
```
User: Opens frontend/src/components/chat/ChatInterface.tsx
System: Auto-loads ui-troubleshooting.md (fileMatch: frontend/**)
```

## Benefits

1. **Context Window Protection:** 97% reduction in auto-loaded steering content
2. **Maintained Guidance:** All detailed docs still available on-demand
3. **Better Organization:** Logical categorization (architecture, backend, frontend, process)
4. **Smart Loading:** fileMatch triggers load docs only when relevant
5. **MCP Integration:** Leverages AWS docs MCP for latest AWS service info

## Migration Notes

Old steering docs preserved in `.kiro/old_steering/` for reference. Can be deleted after validation period.

## Testing Recommendations

1. Verify index loads automatically in new conversations
2. Test fileMatch triggers when opening files in respective directories
3. Validate manual inclusion works with `#[[file:...]]` syntax
4. Confirm context window usage is significantly reduced
5. Ensure agent can still access detailed guidance when needed

## Next Steps

1. Monitor agent performance with new structure
2. Gather feedback on guidance accessibility
3. Adjust fileMatch patterns if needed
4. Consider additional consolidation opportunities
5. Delete old_steering/ after validation period (1-2 weeks)

---

## RESULTS:
I'll implement the restructuring now. Let me start by creating the new structure and migrating the docs with appropriate frontmatter.

Now I'll create the new streamlined structure:

Perfect! The index is now active and auto-loading. Let me continue creating the streamlined structure:

Now let me create a summary document in the dev-history folder and update the index with the final structure:

Perfect! The steering rationalization is complete. Let me create a quick summary of what we accomplished:

## Steering Documentation Streamlined

Successfully restructured steering docs from 12 files (~4,653 lines, mostly auto-loaded) to a lean, progressive disclosure system:

**New Structure:**
- `00-index.md` (50 lines) - Navigation hub, auto-loaded
- `core-rules.md` (30 lines) - Essential practices, auto-loaded
- 6 detailed docs organized by category - loaded on-demand or by file pattern

**Context Window Savings:**
- Before: ~3,700+ lines auto-loaded every conversation
- After: ~80 lines auto-loaded
- Result: 97% reduction in baseline context consumption

**Access Patterns:**
- Auto-load: Index + core rules (always available)
- fileMatch: Strands/CDK, API patterns, UI troubleshooting (trigger on relevant files)
- Manual: AgentCore architecture, Memory, Observability, Session docs (load via `#[[file:...]]`)

**Key Improvements:**
1. Consolidated 3 small rule docs into one
2. Merged duplicate Strands docs
3. Eliminated MCP advocacy doc (now using AWS docs MCP server)
4. Added smart fileMatch triggers for context-specific loading
5. Maintained all detailed guidance - just on-demand instead of always-on

The old docs are preserved in `.kiro/old_steering/` for reference. After a validation period, they can be deleted.
