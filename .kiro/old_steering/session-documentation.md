---
inclusion: manual
---

# Session Documentation Guidelines

## Overview

When working on spec-driven development tasks, proper documentation helps maintain project continuity, enables knowledge transfer, and provides a clear audit trail of decisions and changes. This document outlines guidelines for two types of documentation:

1. **Session Summaries** - Comprehensive logs of substantial work sessions
2. **Commit Messages** - Detailed commit descriptions for version control

Both serve different but complementary purposes in the development workflow.

---

## Session Summaries

### Purpose

Session summaries capture the full context of a work session, including:
- Problems encountered and how they were solved
- Investigation process and root cause analysis
- Key learnings and architectural insights
- Files modified and why
- Testing results and validation
- Next steps and remaining work

### When to Create

Create a session summary when:
- ✅ Completing substantial work (2+ hours of focused development)
- ✅ Solving complex bugs that required investigation
- ✅ Making architectural decisions or discovering important patterns
- ✅ Completing multiple related tasks from a spec
- ✅ Encountering issues that future developers should know about

Do NOT create a session summary for:
- ❌ Trivial changes (typo fixes, minor formatting)
- ❌ Single-file quick fixes
- ❌ Work that's fully captured in commit message

### File Location and Naming

**Location:** `.kiro/dev-history/{spec-name}/`

**Naming Convention:** `session-summary-YYYY-MM-DD-{descriptor}.md`

**Examples:**
- `session-summary-2026-02-26-tasks-1-3.md` - Completed tasks 1-3
- `session-summary-2026-02-27-bug-investigation.md` - Bug investigation session
- `session-summary-2026-02-28-deployment-testing.md` - Deployment and testing

**Descriptor Guidelines:**
- Use task numbers if covering specific tasks (e.g., `tasks-1-3`)
- Use descriptive names for focused work (e.g., `bug-investigation`, `deployment-testing`)
- Keep it short and meaningful

### Content Structure

```markdown
# Session Summary: [Brief Title]

**Date:** [Month Day, Year]
**Duration:** [Approximate time]
**Goal:** [Primary objective of the session]

## [Previous Session Recap] (if continuation)

Brief summary of where you left off:
- ✅ What was completed
- 🔧 What was in progress
- ❌ What was blocked
- ❓ What was unknown

## Issues Identified and Fixed

### 1. [Issue Name] [Status Indicator]

**Problem:** Clear description of the issue

**Root Cause Analysis:**
1. Step-by-step investigation process
2. Evidence gathered (logs, error messages, test results)
3. Why the issue occurred
4. What was misunderstood or missing

**Evidence from [Source]:**
```
Relevant logs, error messages, or code snippets
```

**Fix Applied:**

**Part A: [Component/Aspect]**
- File: `path/to/file.ext`
- Changes made
- Why this approach was chosen

**Part B: [Component/Aspect]**
- File: `path/to/file.ext`
- Changes made
- Why this approach was chosen

**Code Pattern:** (if applicable)
```language
// Example of the fix with context
```

**Result:** What happened after the fix

### 2. [Next Issue] [Status Indicator]

[Repeat structure for each issue]

## Current Status

### ✅ Working
- Feature/component that's fully functional
- Another completed item

### 🔧 Fixed, Needs Deployment
- Changes made but not yet deployed
- Pending validation

### ❓ Needs Investigation
- Known issues requiring further work
- Questions to answer

## Files Modified

### [Category 1]
- `path/to/file1.ext` - What changed and why
- `path/to/file2.ext` - What changed and why

### [Category 2]
- `path/to/file3.ext` - What changed and why

## Next Steps

### Immediate (Required)

1. **[Action Item]** with clear description:
   - Sub-step 1
   - Sub-step 2
   - Expected outcome

2. **[Action Item]** with clear description:
   - Sub-step 1
   - Sub-step 2

### Testing Checklist

After deployment:
- [ ] Test case 1
- [ ] Test case 2
- [ ] Test case 3

## Key Learnings

### [Learning Category 1]

**Critical Discovery:** Main insight

**[Specific Topic]:**
- Detailed explanation
- Why it matters
- How to apply it

**Common Mistake:**
```language
// Example of what NOT to do
```

**Correct Approach:**
```language
// Example of correct pattern
```

**Why This Matters:**
- Reason 1
- Reason 2

### [Learning Category 2]

[Repeat structure for each major learning]

## Architecture Insights

### [System/Component Name]

```
Visual representation of flow or architecture
Using ASCII art or clear text description
```

**Key Points:**
- Important architectural decision
- Why this pattern was chosen
- Trade-offs considered

## Success Metrics

- ✅ Completed item with measurable outcome
- 🔧 In-progress item with current state
- ❓ Pending item with what's needed

## Technical Debt

1. **[Debt Item 1]** - Description and why it exists
2. **[Debt Item 2]** - Description and priority

## Conclusion

Brief summary of the session's accomplishments and current state.

**Key Achievements:**
- ✅ Major accomplishment 1
- ✅ Major accomplishment 2

**Remaining Work:**
- Next priority 1
- Next priority 2

[Final assessment of readiness for next phase]

---

## Session Complete

**Status:** [Ready for Deployment | In Progress | Blocked]

### Summary of Accomplishments

[2-3 paragraph summary of what was achieved]

### Files Created

**[Category]:**
- `path/to/file.ext` - Purpose

### Files Modified

**[Category]:**
- `path/to/file.ext` - What changed

### Key Findings

**1. [Finding Name]**
- Discovery
- Impact
- Solution

### Next Steps for [Phase]

**Phase 1: [Phase Name]**
1. Action item
2. Action item

**Phase 2: [Phase Name]**
1. Action item
2. Action item

### Testing Checklist

**Before Deployment:**
- [x] Completed test
- [ ] Pending test

**After Deployment:**
- [ ] Test to run after deployment

### Lessons Learned

1. **Lesson 1** - Explanation
2. **Lesson 2** - Explanation

### Session Metrics

- **Duration:** X hours
- **Issues Resolved:** X
- **Files Created:** X
- **Files Modified:** X
- **Deployment Status:** [Status]
- **Testing Status:** [Status]

**Session End Time:** [Date and Time]

**Ready for:** [Next phase or action]
```

### Status Indicators

Use these consistently throughout the document:
- ✅ **Complete** - Fully working and tested
- 🔧 **In Progress** - Work started but not finished
- ❌ **Blocked** - Cannot proceed due to dependency
- ❓ **Unknown** - Needs investigation or clarification

### Writing Guidelines

**Be Specific:**
- Include exact file paths, line numbers, error messages
- Show actual code snippets with context
- Reference specific logs or test results

**Explain the "Why":**
- Don't just list what changed, explain why
- Include root cause analysis for bugs
- Document decision-making process

**Think About Future Readers:**
- Assume reader is unfamiliar with the problem
- Explain context and background
- Include links to documentation or resources

**Use Clear Structure:**
- Break complex issues into numbered sections
- Use headings and subheadings liberally
- Include visual separators (---, ###)

**Include Evidence:**
- Show error messages and logs
- Include before/after code comparisons
- Reference test results

**Document Learnings:**
- Capture insights that aren't obvious from code
- Explain common mistakes and how to avoid them
- Share architectural patterns discovered

---

## Commit Messages

### Purpose

Commit messages provide a concise but complete description of changes for version control. They should:
- Summarize what changed and why
- Include root cause analysis for bug fixes
- Reference related session summaries
- Enable quick understanding without reading code

### When to Create

Create a commit message when:
- ✅ You have code changes ready to commit
- ✅ Changes are tested and working
- ✅ Changes represent a logical unit of work

Do NOT create a commit message for:
- ❌ Exploratory work with no code changes
- ❌ Planning sessions without implementation
- ❌ Work that's not ready to commit

### File Location

**Location:** `commit.txt` at project root

**Usage:** `git add . && git commit -eF commit.txt`

**Note:** This file is overwritten each time - it's a template for the current commit, not a permanent record.

### Content Structure

```plaintext
[Brief summary line - what was fixed/added]

Root Cause Analysis:
[For bug fixes: Explain what was wrong and why it happened.
 For features: Explain the need and approach.
 2-4 sentences providing context.]

What Was Fixed/Added:
- Bullet point 1: Specific change
- Bullet point 2: Specific change
- Bullet point 3: Specific change
[Focus on the actual changes made]

Key Changes:
- path/to/file1.ext
- path/to/file2.ext
- path/to/file3.ext
[List the most important files changed]

Why This Matters:
- Impact 1: How this helps users/developers
- Impact 2: What problem this solves
- Impact 3: What this enables
[Explain the significance]

Next Steps:
1. What needs to happen after this commit
2. Follow-up work required
3. Testing or deployment needed
[Keep it brief - 3-5 items max]

Testing:
- Test result 1
- Test result 2
- What was validated
[Show that changes were verified]

Documentation:
- Session summary reference (if exists)
- Other documentation created/updated
[Link to related documentation]
```

### Writing Guidelines

**Summary Line:**
- Start with action verb (Fix, Add, Update, Refactor, Remove)
- Be specific but concise (50-70 characters)
- Focus on the main change

**Root Cause Analysis:**
- Essential for bug fixes
- Explain what was wrong, not just what changed
- Include how the issue was discovered

**Be Concise:**
- Commit messages should be shorter than session summaries
- Focus on what changed, not the investigation process
- Include enough context to understand the change

**Reference Session Summaries:**
- If a session summary exists, reference it
- Don't duplicate all details from session summary
- Provide enough info to understand commit standalone

**Focus on Impact:**
- Explain why the change matters
- What problem does it solve?
- What does it enable?

**Include Testing:**
- Show that changes were validated
- Mention key test results
- Note any manual testing performed

---

## Relationship Between Session Summaries and Commit Messages

### When to Create Both

Create both when:
- ✅ Substantial work session (2+ hours) with code changes
- ✅ Complex bug fix requiring investigation
- ✅ Multiple related changes across many files
- ✅ Architectural decisions or pattern discoveries

**Pattern:**
1. Work on the problem (investigation, implementation, testing)
2. Create session summary documenting the full journey
3. Create commit message summarizing the changes
4. Reference session summary in commit message

**Example:**
```plaintext
# In commit.txt
Fix multi-agent orchestration: strands-agents-tools dependency

[... commit details ...]

Documentation:
- Created .kiro/dev-history/multi-agent-orchestration-pattern/session-summary-2026-02-26-continued.md
- Session summary contains full investigation and root cause analysis
```

### When to Create Session Summary Only

Create session summary only when:
- ✅ Exploratory work without code changes
- ✅ Planning and design sessions
- ✅ Investigation that doesn't result in immediate fix
- ✅ Work in progress that spans multiple commits

**Example Scenarios:**
- Investigating a bug but not yet fixing it
- Planning architecture for a new feature
- Researching documentation and patterns
- Setting up local testing environment for exploration

### When to Create Commit Message Only

Create commit message only when:
- ✅ Simple, straightforward changes
- ✅ Quick bug fixes with obvious cause
- ✅ Minor refactoring or cleanup
- ✅ Documentation updates

**Example Scenarios:**
- Fixing a typo in code
- Updating a dependency version
- Renaming a variable for clarity
- Adding a missing import

**Note:** This should be rare. Most commits benefit from at least brief documentation.

### Cross-Referencing

**In Session Summary:**
```markdown
## Conclusion

[... summary ...]

**Ready for:** Deployment

See commit.txt for deployment commit message.
```

**In Commit Message:**
```plaintext
Documentation:
- Created .kiro/dev-history/{spec-name}/session-summary-YYYY-MM-DD-{descriptor}.md
- Session summary contains detailed investigation and learnings
```

---

## Multi-Session Work

### Handling Work That Spans Multiple Sessions

**Pattern 1: Continuation Sessions**

When work continues across multiple days:

**First Session:**
- File: `session-summary-2026-02-26-tasks-1-2.md`
- Document initial work, discoveries, and current state
- End with clear "Next Steps" section

**Second Session:**
- File: `session-summary-2026-02-27-continued.md`
- Start with "Previous Session Recap" section
- Reference previous session summary
- Document new work and discoveries

**Example:**
```markdown
# Session Summary: Multi-Agent Orchestration UAT (Continued)

**Date:** February 27, 2026
**Duration:** ~2 hours
**Goal:** Complete deployment and testing from previous session

## Previous Session Recap

From session-summary-2026-02-26-continued.md:
- ✅ Identified strands-agents-tools dependency issue
- ✅ Fixed all agent requirements.txt files
- 🔧 Orchestrator tool registration needs wrapper class pattern
- ❓ Deployment and testing pending

[... continue with current session work ...]
```

**Pattern 2: Multiple Commits in One Session**

When a session results in multiple logical commits:

**Session Summary:**
- Document the entire session's work
- Include all changes and learnings
- Reference all commits made

**Commit Messages:**
- Create separate commit.txt for each logical unit
- Each commit message stands alone
- Reference the session summary in each

**Example:**
```plaintext
# First commit
Add strands-agents-tools dependency to all agents

[... commit details ...]

Documentation:
- Part of session documented in session-summary-2026-02-26-continued.md

---

# Second commit (overwrites commit.txt)
Implement wrapper class pattern for orchestrator tools

[... commit details ...]

Documentation:
- Part of session documented in session-summary-2026-02-26-continued.md
```

**Pattern 3: Incremental Progress**

When making incremental progress on a large task:

**Option A: Single Session Summary at End**
- Work across multiple sessions
- Create one comprehensive summary when complete
- Name it: `session-summary-2026-02-26-to-28-tasks-1-5.md`

**Option B: Session Summaries for Each Major Milestone**
- Create summary after each significant milestone
- Each summary references previous ones
- Useful for very long tasks (1+ week)

---

## Examples

### Example 1: Complex Bug Fix with Investigation

**Session Summary:** `session-summary-2026-02-26-continued.md`
```markdown
# Session Summary: Multi-Agent Orchestration UAT and Tool Registration Fixes

**Date:** February 26, 2026 (Continued)
**Duration:** ~3 hours
**Goal:** Complete UAT testing and fix orchestrator specialist invocation

## Previous Session Recap

From earlier today:
- ✅ Fixed pattern field missing
- 🔧 UMich agent 424 error
- 🔧 Orchestrator can't invoke specialists

## Issues Identified and Fixed

### 1. UMich Agent 424 Error ✅ SOLVED

**Problem:** UMich agent fails with ModuleNotFoundError for 'strands_tools'

**Root Cause Analysis:**
1. Created local test environment
2. Discovered strands_tools is a SEPARATE package
3. strands-agents-tools not in requirements.txt

**Fix Applied:**
- Added strands-agents-tools>=1.0.0 to all requirements.txt files
- Verified locally with test agent
- Ready for deployment

[... detailed investigation and learnings ...]

## Key Learnings

### Strands Package Architecture

**Critical Discovery:** strands-agents and strands-agents-tools are SEPARATE

[... detailed explanation ...]

## Conclusion

Successfully identified root cause and implemented fix. Ready for deployment.
```

**Commit Message:** `commit.txt`
```plaintext
Fix multi-agent orchestration: strands-agents-tools dependency

Root Cause Analysis:
The UMich agent was failing with ModuleNotFoundError for 'strands_tools'
because strands_tools comes from a separate package (strands-agents-tools),
not included in strands-agents. Discovered through local testing.

What Was Fixed:
- Added strands-agents-tools>=1.0.0 to all agent requirements.txt
- Created local testing environment for validation
- Updated strands.md steering documentation

Key Changes:
- patterns/strands-umich-agent/requirements.txt
- patterns/strands-colorado-agent/requirements.txt
- patterns/strands-coder-agent/requirements.txt
- .kiro/steering/strands.md (new)

Why This Matters:
- UMich agent will now start successfully in AWS
- All agents have correct dependencies
- Local testing prevents future deployment issues

Next Steps:
1. Deploy updated Docker images
2. Run UAT testing of all agents
3. Verify end-to-end orchestration flow

Testing:
- Local UMich agent successfully uses http_request tool
- Import verification tests pass

Documentation:
- Created session-summary-2026-02-26-continued.md
- Full investigation and learnings documented
```

### Example 2: Feature Implementation

**Session Summary:** `session-summary-2026-03-01-tasks-4-6.md`
```markdown
# Session Summary: Agent Gallery UI Implementation

**Date:** March 1, 2026
**Duration:** ~4 hours
**Goal:** Implement tasks 4-6 from enhanced-agent-ui spec

## Tasks Completed

### Task 4: Agent Card Component ✅

**Implementation:**
- Created AgentCard.tsx with Tailwind styling
- Added agent metadata display
- Implemented click navigation

**Files Created:**
- `frontend/src/components/agents/AgentCard.tsx`
- `frontend/src/components/agents/AgentCard.test.tsx`

**Testing:**
- Unit tests pass
- Visual review in Storybook

[... detailed implementation notes ...]

## Key Learnings

### Tailwind Component Patterns

Discovered reusable pattern for card components:
[... pattern explanation ...]

## Next Steps

1. Deploy to staging for review
2. Implement tasks 7-8 (agent details page)
3. Integration testing with backend
```

**Commit Message:** `commit.txt`
```plaintext
Add agent gallery UI components (tasks 4-6)

Root Cause Analysis:
Users needed a visual way to browse and select agents instead of
dropdown-only interface. Implemented gallery view with cards.

What Was Added:
- AgentCard component with metadata display
- AgentGallery grid layout with responsive design
- Navigation integration with React Router
- Unit tests and Storybook stories

Key Changes:
- frontend/src/components/agents/AgentCard.tsx (new)
- frontend/src/components/agents/AgentGallery.tsx (new)
- frontend/src/pages/AgentGalleryPage.tsx (new)

Why This Matters:
- Improves agent discoverability
- Better user experience for agent selection
- Foundation for agent details page

Next Steps:
1. Deploy to staging for review
2. Implement agent details page
3. Add filtering and search

Testing:
- Unit tests pass (12/12)
- Visual review in Storybook
- Manual testing in dev environment

Documentation:
- Created session-summary-2026-03-01-tasks-4-6.md
- Updated component documentation
```

### Example 3: Exploratory Session (No Commit)

**Session Summary:** `session-summary-2026-03-05-architecture-investigation.md`
```markdown
# Session Summary: Memory Service Architecture Investigation

**Date:** March 5, 2026
**Duration:** ~2 hours
**Goal:** Understand AgentCore Memory service for upcoming feature

## Investigation Process

### 1. Documentation Review

Read through:
- AWS Bedrock AgentCore Memory API docs
- docs/MEMORY_INTEGRATION.md
- backend-stack.ts memory configuration

### 2. Code Analysis

Examined:
- Existing memory strategy implementations
- SSM parameter structure
- Lambda integration patterns

### 3. Key Findings

**Memory Strategies:**
1. SummaryMemoryStrategy - Session summaries
2. UserPreferenceMemoryStrategy - User preferences
3. SemanticMemoryStrategy - Long-term facts

**Namespace Structure:**
- `/summaries/{actorId}/{sessionId}`
- `/preferences/{actorId}`
- `/facts/{actorId}`

[... detailed findings ...]

## Architecture Insights

[... diagrams and explanations ...]

## Next Steps

1. Create design document for memory UI feature
2. Prototype memory retrieval Lambda
3. Design frontend components

## No Code Changes

This was an exploratory session. No commit needed.
```

**No commit.txt created** - This was investigation only.

---

## Best Practices

### Do's ✅

**Session Summaries:**
- ✅ Document the investigation process, not just the solution
- ✅ Include error messages, logs, and evidence
- ✅ Explain root causes and why issues occurred
- ✅ Capture learnings and insights for future reference
- ✅ Use status indicators consistently (✅ 🔧 ❌ ❓)
- ✅ Include code snippets with context
- ✅ Reference related documentation and resources
- ✅ End with clear next steps and testing checklist

**Commit Messages:**
- ✅ Start with clear, action-oriented summary
- ✅ Include root cause analysis for bug fixes
- ✅ List key files changed
- ✅ Explain why changes matter
- ✅ Reference session summary if it exists
- ✅ Include testing validation
- ✅ Keep it concise but complete

**Both:**
- ✅ Write for future readers (including yourself in 6 months)
- ✅ Be specific with file paths and line numbers
- ✅ Include enough context to understand standalone
- ✅ Use consistent formatting and structure

### Don'ts ❌

**Session Summaries:**
- ❌ Don't create summaries for trivial changes
- ❌ Don't just list changes without explaining why
- ❌ Don't skip root cause analysis for bugs
- ❌ Don't assume reader knows the context
- ❌ Don't forget to document key learnings
- ❌ Don't leave out testing results
- ❌ Don't skip the "Next Steps" section

**Commit Messages:**
- ❌ Don't use vague summaries ("fix bug", "update code")
- ❌ Don't skip root cause analysis for bug fixes
- ❌ Don't forget to list key files changed
- ❌ Don't omit testing validation
- ❌ Don't duplicate entire session summary
- ❌ Don't forget to reference session summary if it exists

**Both:**
- ❌ Don't assume changes are self-explanatory
- ❌ Don't skip documentation because you're tired
- ❌ Don't write documentation that only you can understand
- ❌ Don't forget to proofread before committing

---

## Quick Reference

### When to Create What

| Scenario | Session Summary | Commit Message |
|----------|----------------|----------------|
| Complex bug fix with investigation | ✅ Yes | ✅ Yes |
| Simple bug fix (obvious cause) | ❌ No | ✅ Yes |
| Feature implementation (2+ hours) | ✅ Yes | ✅ Yes |
| Quick feature addition | ❌ No | ✅ Yes |
| Exploratory investigation | ✅ Yes | ❌ No |
| Planning session | ✅ Yes | ❌ No |
| Typo fix | ❌ No | ✅ Yes (brief) |
| Multi-day feature work | ✅ Yes (per milestone) | ✅ Yes (per commit) |

### File Locations

- **Session Summaries:** `.kiro/dev-history/{spec-name}/session-summary-YYYY-MM-DD-{descriptor}.md`
- **Commit Messages:** `commit.txt` (project root, overwritten each time)

### Status Indicators

- ✅ **Complete** - Fully working and tested
- 🔧 **In Progress** - Work started but not finished
- ❌ **Blocked** - Cannot proceed due to dependency
- ❓ **Unknown** - Needs investigation or clarification

### Commit Message Template

```plaintext
[Action verb] [brief summary]

Root Cause Analysis:
[Why this change was needed]

What Was Fixed/Added:
- Change 1
- Change 2

Key Changes:
- file1.ext
- file2.ext

Why This Matters:
- Impact 1
- Impact 2

Next Steps:
1. Step 1
2. Step 2

Testing:
- Test result 1
- Test result 2

Documentation:
- Session summary reference (if exists)
```

---

**ALWAYS FOLLOW THESE RULES WHEN DOCUMENTING SESSIONS**
