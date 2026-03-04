# MCP Documentation Access: A Critical Requirement

**IF YOU ARE AN AI ASSISTANT YOU MUST FOLLOW THESE RULES**

## The Problem: Guessing API Signatures is Unacceptable

**Real Cost Example:** During implementation of the Memory API integration, we spent over an hour debugging because we guessed the AgentCore Memory API response schema instead of consulting official documentation. The actual response structure was completely different from our assumptions, leading to:

- Wasted development time
- Multiple failed deployment attempts
- Frustration and loss of confidence
- Technical debt from incorrect assumptions

**This is unacceptable when working with complex AWS services like AgentCore.**

## The Solution: MCP Documentation Access

Model Context Protocol (MCP) servers provide direct access to official documentation during development. This is not optional - it's a critical requirement for professional development work.

### Why MCP Documentation Access is Critical

1. **Accuracy**: Official documentation is the source of truth for API signatures, response schemas, and behavior
2. **Efficiency**: Instant access to docs eliminates guessing and reduces debugging time
3. **Confidence**: Validated information leads to correct implementations on the first try
4. **Completeness**: Documentation includes edge cases, error handling, and best practices that LLMs might miss

### When to Use MCP Documentation Access

**ALWAYS use MCP documentation access when:**
- Working with AWS services (Bedrock, AgentCore, Lambda, DynamoDB, etc.)
- Implementing new API integrations
- Uncertain about request/response schemas
- Debugging unexpected API behavior
- Learning about service capabilities and limitations

**NEVER guess when documentation is available.**

## Required MCP Servers for AWS/AgentCore Development

### 1. aws-docs (CRITICAL)

**Purpose:** Access official AWS documentation for all AWS services

**Installation:**
```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["search_aws_documentation", "get_aws_documentation"]
    }
  }
}
```

**Use Cases:**
- AgentCore API documentation (Runtime, Memory, Gateway, Code Interpreter, Identity, Observability)
- AWS service documentation (Lambda, DynamoDB, S3, CloudWatch, etc.)
- SDK reference documentation
- Best practices and architecture patterns

**How to Use:**
```
Before implementing any AgentCore feature:
1. Search for relevant documentation: "AgentCore Memory API"
2. Read the API reference for request/response schemas
3. Check examples and best practices
4. Implement based on validated information
```

### 2. fetch (Recommended)

**Purpose:** Fetch content from web URLs for non-AWS documentation

**Installation:**
```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Use Cases:**
- Third-party library documentation
- GitHub repositories and READMEs
- Blog posts and tutorials
- Stack Overflow discussions

### 3. Additional Recommended Servers

**For Database Work:**
```json
{
  "postgres": {
    "command": "uvx",
    "args": ["mcp-server-postgres"],
    "env": {
      "DATABASE_URL": "postgresql://user:pass@localhost/db"
    },
    "disabled": false,
    "autoApprove": []
  }
}
```

**For Git Operations:**
```json
{
  "git": {
    "command": "uvx",
    "args": ["mcp-server-git"],
    "env": {},
    "disabled": false,
    "autoApprove": ["git_status", "git_diff", "git_log"]
  }
}
```

## Setup Instructions

### User-Level Configuration

**File:** `~/.kiro/settings/mcp.json`

This configuration applies to all workspaces for the user.

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {},
      "disabled": false,
      "autoApprove": []
    },
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["search_aws_documentation", "get_aws_documentation"]
    }
  }
}
```

### Workspace-Level Configuration

**File:** `.kiro/settings/mcp.json` (in project root)

This configuration applies only to the current workspace and overrides user-level settings.

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["search_aws_documentation", "get_aws_documentation"]
    }
  }
}
```

### Verification

After configuration, verify MCP servers are available:

1. Restart your IDE/editor
2. Check MCP server status in settings
3. Test by searching AWS documentation: "AgentCore Runtime API"

## Best Practices for Using MCP Documentation Access

### 1. Documentation-First Development

**ALWAYS follow this workflow:**

```
1. Identify the AWS service/API you need to use
2. Search MCP documentation for that service
3. Read the API reference and examples
4. Validate request/response schemas
5. Implement based on validated information
6. Test with real API calls
```

**NEVER:**
- Guess API signatures
- Assume response structures
- Skip documentation review
- Implement without validation

### 2. Specific Documentation Queries

**Good queries:**
- "AgentCore Memory API ListEvents response schema"
- "AgentCore Runtime InvokeAgent request parameters"
- "DynamoDB PutItem request syntax Python"
- "Lambda Powertools event handler CORS configuration"

**Poor queries:**
- "How does memory work?" (too vague)
- "AgentCore" (too broad)
- "API" (not specific enough)

### 3. Validate Before Implementing

**Before writing code:**
1. Search for the specific API endpoint documentation
2. Copy the exact request/response schemas
3. Note any required parameters or headers
4. Check for authentication requirements
5. Review error codes and handling

**During implementation:**
1. Reference the documentation continuously
2. Match your code to documented examples
3. Use exact field names and types
4. Handle all documented error cases

**After implementation:**
1. Compare your code to documentation examples
2. Verify all required fields are included
3. Test with real API calls
4. Validate response handling

### 4. Document Your Sources

When implementing features based on MCP documentation:

```python
"""
Retrieve memory records from AgentCore Memory API.

Based on AWS AgentCore Memory API documentation:
- API: ListEvents
- Response schema: {
    "events": [
        {
            "eventId": "string",
            "namespace": "string",
            "content": "string",
            "timestamp": "string"
        }
    ]
}

Reference: AWS Bedrock AgentCore Memory API Reference
"""
```

This helps future developers understand the source of truth.

### 5. Keep Documentation Updated

If you discover documentation is outdated or incorrect:

1. Note the discrepancy in code comments
2. Document the actual behavior
3. Report to AWS support if it's an AWS service
4. Update internal documentation

## Common AWS Services Requiring Documentation Access

### AgentCore Components

- **Runtime**: Agent execution, session management, trace retrieval
- **Memory**: Long-term memory storage and retrieval
- **Gateway**: Tool execution and MCP integration
- **Code Interpreter**: Sandboxed Python execution
- **Identity**: User context and authorization (future)
- **Observability**: Structured trace and metric queries

### Supporting AWS Services

- **Lambda**: Function configuration, event handling, layers
- **DynamoDB**: Table operations, query syntax, indexes
- **S3**: Bucket operations, object storage, presigned URLs
- **CloudWatch**: Log queries, metrics, alarms
- **Cognito**: User pools, authentication, JWT validation
- **API Gateway**: REST APIs, authorizers, CORS
- **SSM Parameter Store**: Parameter operations, hierarchies

## Lessons Learned: AgentCore Memory API Case Study

### What Went Wrong

**Assumption:** Memory API returns a simple list of memory objects
**Reality:** Memory API returns different schemas per memory strategy with nested structures

**Impact:**
- Frontend displayed "undefined" for all memory fields
- Backend Lambda returned incorrect data structure
- Multiple deployment cycles to fix
- Over 1 hour of debugging time

### What Should Have Happened

1. **Search MCP documentation**: "AgentCore Memory API ListEvents"
2. **Read response schema**: Understand the actual structure
3. **Validate memory strategies**: Confirm schema differences per strategy
4. **Implement correctly**: Use validated schemas from the start
5. **Test once**: Verify with real API calls

**Result:** Correct implementation on first try, no debugging needed

### Key Takeaway

**The cost of not using documentation access far exceeds the time to look it up.**

## Enforcement Rules for AI Assistants

**IF YOU ARE AN AI ASSISTANT YOU MUST:**

1. **ALWAYS check for MCP documentation access** before implementing AWS/AgentCore features
2. **NEVER guess API signatures** when documentation is available
3. **SEARCH documentation first** for any unfamiliar API
4. **VALIDATE schemas** against official documentation
5. **DOCUMENT your sources** in code comments
6. **FAIL LOUDLY** if documentation access is not available for critical work

**IF MCP documentation access is not configured:**

1. **STOP immediately** - do not proceed with guessing
2. **INFORM the user** that MCP documentation access is required
3. **PROVIDE setup instructions** from this document
4. **WAIT for confirmation** that MCP is configured
5. **VERIFY access** by testing a documentation search

**NEVER proceed with implementation based on assumptions when working with:**
- AgentCore APIs (Runtime, Memory, Gateway, etc.)
- AWS service APIs
- Third-party integrations
- Complex data structures

## Quick Reference: MCP Documentation Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Identify API/Service                                │
│ "I need to use AgentCore Memory API"                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Check MCP Access                                    │
│ Is aws-docs MCP server configured and enabled?              │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────┴───────┐
                    │               │
                   YES              NO
                    │               │
                    ↓               ↓
    ┌───────────────────────┐  ┌──────────────────────┐
    │ Step 3: Search Docs   │  │ STOP: Configure MCP  │
    │ "AgentCore Memory API"│  │ Follow setup guide   │
    └───────────────────────┘  └──────────────────────┘
                    ↓
    ┌───────────────────────────────────────────────────┐
    │ Step 4: Read API Reference                        │
    │ - Request parameters                              │
    │ - Response schema                                 │
    │ - Authentication                                  │
    │ - Error codes                                     │
    └───────────────────────────────────────────────────┘
                    ↓
    ┌───────────────────────────────────────────────────┐
    │ Step 5: Validate Understanding                    │
    │ - Copy exact schemas                              │
    │ - Note required fields                            │
    │ - Check examples                                  │
    └───────────────────────────────────────────────────┘
                    ↓
    ┌───────────────────────────────────────────────────┐
    │ Step 6: Implement                                 │
    │ - Use validated schemas                           │
    │ - Match documentation examples                    │
    │ - Document sources                                │
    └───────────────────────────────────────────────────┘
                    ↓
    ┌───────────────────────────────────────────────────┐
    │ Step 7: Test & Verify                             │
    │ - Real API calls                                  │
    │ - Validate responses                              │
    │ - Handle errors                                   │
    └───────────────────────────────────────────────────┘
```

## Conclusion

MCP documentation access is not a convenience - it's a professional requirement. The cost of guessing is too high, and the solution is readily available. Configure MCP servers, use them consistently, and never implement complex APIs without consulting official documentation.

**Remember:** An hour spent reading documentation saves days of debugging.

**ALWAYS FOLLOW THESE RULES WHEN WORKING WITH AWS SERVICES AND AGENTCORE**
