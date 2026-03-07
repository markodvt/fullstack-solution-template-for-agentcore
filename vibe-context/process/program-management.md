---
inclusion: manual
---

# Program and Epic Management

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## Overview

FAST Agent Gallery uses an epic-based roadmap to organize features into thematic clusters. This document explains how to work with epics, manage the backlog, and maintain program documentation.

## Documentation Hierarchy

```
.kiro/
├── README.md                    # Program vision, tenets, principles
├── specs/
│   ├── README.md               # Spec process overview
│   ├── epics.md                # Feature roadmap by epic
│   └── {feature-name}/         # Individual feature specs
│       ├── README.md           # Concept (for backlog items)
│       ├── requirements.md     # User stories & acceptance criteria
│       ├── design.md           # Technical approach
│       └── tasks.md            # Implementation breakdown
```

## Epic Lifecycle

### 1. Concept Stage (💡 Backlog)

**When:** Initial idea, not yet fully defined

**Actions:**
- Add to appropriate epic's backlog section in `epics.md`
- Include 1-2 sentence description
- Note business value or use case

**Example:**
```markdown
#### 💡 Backlog
- **Infrastructure Observability Tab**
  - View deployed CloudFormation stacks (nested)
  - Resource inventory and cost breakdown
```

### 2. Placeholder Stage (📋 Planned)

**When:** Concept is validated, ready for detailed planning

**Actions:**
- Create directory: `specs/{feature-name}/`
- Create `README.md` with:
  - Status: "Concept stage - spec not yet written"
  - Purpose (2-3 paragraphs)
  - Example use cases
  - Benefits
  - Technical approach (high-level)
  - Questions to resolve
- Update epic status to "Planned"
- Link from `epics.md` to the spec directory

**Example:**
```markdown
#### 📋 Planned
- **Use Case Patterns** → [specs/use-case-patterns/](use-case-patterns/)
  - Template patterns for common use cases
  - Domain-specific agent configurations
  - Reusable tool bundles per use case
```

### 3. Specification Stage (📋 Planned)

**When:** Ready to define detailed requirements

**Actions:**
- Create `requirements.md` with:
  - Introduction and glossary
  - User stories with acceptance criteria
  - Requirements organized by capability
- Create `design.md` with:
  - Architecture overview
  - Component interactions
  - Trade-off analysis
  - Implementation approach
- Create `tasks.md` with:
  - Phased implementation plan
  - Task breakdown with dependencies
  - Testing strategy

### 4. Implementation Stage (🚧 In Progress)

**When:** Active development begins

**Actions:**
- Update epic status to "In Progress"
- Create `.kiro/dev-history/{feature-name}/` directory
- Document sessions in dev-history (see `session-docs.md`)
- Update `tasks.md` as work progresses
- Create commit messages for each logical unit

### 5. Completion Stage (✅ Completed)

**When:** Feature is deployed and available

**Actions:**
- Update epic status to "Completed"
- Move feature to "Completed" section in epic
- Document any learnings in final session summary
- Update main README or docs/ if needed

## Epic Management Best Practices

### ✅ DO:

- **Keep epics thematic** - Group by capability area, not timeline
- **Maintain epic overview table** - Quick reference at top of `epics.md`
- **Link to specs** - Every planned/in-progress feature should link to its spec
- **Update status regularly** - Keep epic status current with actual work
- **Capture backlog ideas** - Don't lose good ideas, add them to backlog
- **Reference related specs** - Cross-link related features
- **Document "why"** - Include business value for each epic

### ❌ DON'T:

- **Don't create epics for single features** - Epics are themes, not tasks
- **Don't skip placeholder stage** - Document concepts before full specs
- **Don't let epics.md get stale** - Update as work progresses
- **Don't duplicate content** - Link to specs, don't repeat them
- **Don't create specs without epic context** - Every spec belongs to an epic
- **Don't forget to update overview table** - Keep summary current

## Adding a New Feature

### Quick Process

1. **Identify the epic** - Which theme does this belong to?
2. **Add to backlog** - Brief description in epic's backlog section
3. **Create placeholder** (when ready) - `specs/{feature-name}/README.md`
4. **Write spec** (when ready) - requirements.md, design.md, tasks.md
5. **Update epic status** - Move from backlog → planned → in progress → completed

### Example Flow

```markdown
# Step 1: Add to backlog
Epic 2: Observability & Debugging
#### 💡 Backlog
- **Infrastructure Observability Tab**
  - View deployed CloudFormation stacks

# Step 2: Create placeholder
specs/infrastructure-observability/README.md
- Status: Concept stage
- Purpose: Provide visibility into deployed infrastructure
- Questions to resolve: Which resources to show? How to handle nested stacks?

# Step 3: Write spec (when ready)
specs/infrastructure-observability/requirements.md
specs/infrastructure-observability/design.md
specs/infrastructure-observability/tasks.md

# Step 4: Update epic
Epic 2: Observability & Debugging
#### 📋 Planned
- **Infrastructure Observability Tab** → [specs/infrastructure-observability/](infrastructure-observability/)
```

## Creating a New Epic

### When to Create

Create a new epic when:
- ✅ You have 3+ related features that form a coherent theme
- ✅ The theme represents a major capability area
- ✅ The theme aligns with product tenets and vision
- ✅ The theme has clear business value

Do NOT create for:
- ❌ Single features (add to existing epic)
- ❌ Timeline-based groupings ("Q1 features")
- ❌ Team-based groupings ("Frontend work")

### Epic Template

```markdown
## Epic N: [Theme Name]

**Theme**: [One sentence describing the capability area]

**Business Value**: [Why this matters to users/business]

### Features

#### ✅ Completed
- [List completed features]

#### 🚧 In Progress
- **[Feature Name]** → [specs/feature-name/](feature-name/)
  - Brief description
  - Key capabilities

#### 📋 Planned
- **[Feature Name]** → [specs/feature-name/](feature-name/)
  - Brief description

#### 💡 Backlog
- **[Feature Concept]**
  - Brief description
  - Business value
```

## Backlog Grooming

### Regular Maintenance

**Monthly:**
- Review backlog items for relevance
- Promote concepts to planned when ready
- Archive or remove obsolete ideas
- Update epic descriptions if themes evolve

**Per Session:**
- Add new ideas as they emerge
- Update status of active features
- Link to new specs as created
- Document decisions in session summaries

### Prioritization Factors

Consider when moving from backlog to planned:
1. **Business value** - Impact on users and adoption
2. **Dependencies** - What must exist first?
3. **Effort** - Complexity and time required
4. **Risk** - Technical or organizational challenges
5. **Learning** - Does this help us learn faster?

## Integration with Other Docs

### Vision (.kiro/README.md)
- Epics implement the vision
- Tenets guide epic prioritization
- Success metrics measure epic outcomes

### Specs (specs/{feature-name}/)
- Each spec belongs to an epic
- Specs provide detailed requirements
- Epics provide thematic context

### Dev History (dev-history/{feature-name}/)
- Session summaries document implementation
- Reference epic and spec for context
- Capture learnings that inform future epics

### Steering (steering/)
- This doc explains epic management
- Other steering docs guide implementation
- Progressive disclosure - load as needed

## Common Patterns

### Pattern: Feature Clusters

When multiple related features emerge:
```markdown
Epic 4: Tool Ecosystem
#### 💡 Backlog
- **REST API Wrapper Tools**
  - Auto-generate from OpenAPI specs
- **Database Connector Tools**
  - SQL and NoSQL connectors
- **File System Tools**
  - S3 and local file operations
```

### Pattern: Phased Features

When a feature has multiple phases:
```markdown
Epic 7: Use Case Acceleration
#### 🚧 In Progress
- **Lending Use Case** → [specs/lending/](lending/)
  - Phase 1: Synthetic data generation (in progress)
  - Phase 2: Document processing agents (planned)
  - Phase 3: Compliance checking (backlog)
```

### Pattern: Cross-Epic Dependencies

When features span multiple epics:
```markdown
Epic 5: Governance & Compliance
#### 💡 Backlog
- **Evaluation Framework**
  - Automated agent testing
  - Depends on: Observability dashboard (Epic 2)
  - Enables: Policy enforcement (Epic 5)
```

## Questions and Decisions

### When to Split an Epic

Split when:
- Epic has 10+ features
- Features cluster into distinct sub-themes
- Epic spans multiple product areas

### When to Merge Epics

Merge when:
- Epics have < 3 features each
- Themes are closely related
- Separation creates confusion

### When to Archive an Epic

Archive when:
- All features completed
- Theme no longer relevant
- Superseded by new approach

Move to "Completed Epics" section at bottom of `epics.md`.

## Quick Reference

### File Locations
- **Program vision**: `.kiro/README.md`
- **Epic roadmap**: `.kiro/specs/epics.md`
- **Spec index**: `.kiro/specs/README.md`
- **Feature specs**: `.kiro/specs/{feature-name}/`
- **Dev history**: `.kiro/dev-history/{feature-name}/`

### Status Indicators
- ✅ **Completed** - Deployed and available
- 🚧 **In Progress** - Active development
- 📋 **Planned** - Spec exists
- 💡 **Backlog** - Concept only

### Key Commands
```bash
# View epic overview
cat .kiro/specs/epics.md | head -50

# List all specs
ls .kiro/specs/

# Find backlog items
grep -A 2 "💡 Backlog" .kiro/specs/epics.md
```

**ALWAYS FOLLOW THESE RULES WHEN MANAGING EPICS AND PROGRAM DOCUMENTATION**
