# Colorado Agent Deployment Guide

## What We Created

A new agent pattern at `patterns/strands-colorado-agent/` with:
- ✅ `colorado_agent.py` - Fully adapted agent code
- ✅ `requirements.txt` - Python dependencies
- ✅ `Dockerfile` - Container configuration

## Key Adaptations Made

### 1. Updated to FAST Patterns
- Uses `bedrock_agentcore.runtime` (not old `bedrock_agentcore`)
- Proper `RequestContext` for authentication
- Secure user ID extraction via `extract_user_id_from_context()`

### 2. Added Memory Integration
- Shares memory with other agents (same `memory_id`)
- Uses unique session prefix: `colorado_{session_id}`
- Retrieves user preferences, facts, and summaries
- Configured retrieval thresholds for optimal context

### 3. Upgraded Model
- Changed from Claude 3.5 Sonnet v2 to Claude Sonnet 4.5
- Kept temperature at 0.7 for conversational personality
- Model ID: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`

### 4. Enhanced System Prompt
- Added memory awareness
- Kept original personality (Denver teacher with cat Napoleon)
- Added instructions to reference past conversations

### 5. Added Comprehensive Documentation
- Detailed docstrings for all functions
- Type hints on function signatures
- Thorough comments explaining non-obvious code
- Follows all project coding conventions

### 6. Proper Error Handling
- Fails loudly (no silent fallbacks)
- Comprehensive error logging
- Traceback printing for debugging

## Deployment Options

### Option A: Deploy as New Stack (Separate Runtime)
Deploy Colorado agent as a completely separate stack with its own runtime.

**Pros**:
- Independent scaling
- Isolated from other agents
- Easy to test independently

**Cons**:
- More infrastructure to manage
- Requires frontend changes to support multiple runtimes

**Steps**:
1. Update `infra-cdk/config.yaml`:
   ```yaml
   stack_name_base: "marodon-fast-colorado"
   backend:
     pattern: "strands-colorado-agent"
   ```
2. Deploy: `cd infra-cdk && cdk deploy`
3. Note the new runtime ARN
4. Update frontend to include Colorado runtime option

### Option B: Replace Existing Agent (Temporary Test)
Temporarily replace the basic agent to test Colorado agent.

**Pros**:
- Quick testing
- No infrastructure changes
- Uses existing frontend

**Cons**:
- Loses basic agent temporarily
- Not a long-term solution

**Steps**:
1. Update `infra-cdk/config.yaml`:
   ```yaml
   backend:
     pattern: "strands-colorado-agent"  # Changed from strands-single-agent
   ```
2. Deploy: `cd infra-cdk && cdk deploy`
3. Test at existing URL: https://main.dy356n1qt88fa.amplifyapp.com
4. Revert when done testing

### Option C: Multi-Agent Router (Future)
Create a router pattern that selects agent based on payload.

**Pros**:
- Single deployment
- All agents available
- Shared infrastructure

**Cons**:
- More complex
- Requires router implementation
- All agents in one container

**Not recommended for initial testing** - better to test individually first.

## Recommended Deployment Strategy

**For Testing**: Use Option B (replace existing agent temporarily)

1. **Backup current config**:
   ```bash
   cd infra-cdk
   cp config.yaml config.yaml.backup
   ```

2. **Update config.yaml**:
   ```yaml
   backend:
     pattern: "strands-colorado-agent"
   ```

3. **Deploy**:
   ```bash
   cdk deploy --require-approval never
   ```

4. **Test**:
   - Go to: https://main.dy356n1qt88fa.amplifyapp.com
   - Log in with your Cognito user
   - Chat with Colorado agent
   - Ask about Denver, teaching, Napoleon the cat
   - Test memory: share a preference, log out, log back in, verify it remembers

5. **Verify Memory Sharing**:
   - Preferences/facts from basic agent should be accessible
   - Colorado agent should learn new preferences
   - Session history is separate (colorado_ prefix)

6. **Revert when done** (if needed):
   ```bash
   cp config.yaml.backup config.yaml
   cdk deploy --require-approval never
   ```

## Testing Checklist

- [ ] Agent deploys successfully
- [ ] Can log in and start conversation
- [ ] Agent responds with Colorado personality
- [ ] Mentions Denver, teaching, education program when relevant
- [ ] Talks about Napoleon the cat when asked
- [ ] Memory works: preferences persist across sessions
- [ ] Shared memory: can access facts from other agents
- [ ] Error handling: fails gracefully with clear messages
- [ ] Streaming works: responses appear token-by-token

## Memory Behavior

### What's Shared Across All Agents
- User preferences (e.g., "I prefer Python")
- Important facts (e.g., "My project is called FastAI")
- User identity (`actor_id`)

### What's Agent-Specific
- Conversation history (short-term memory)
- Session summaries
- Session ID (prefixed with `colorado_`)

### Example Memory Flow
1. User tells basic agent: "I prefer Python"
2. Memory stores in `/preferences/{actorId}`
3. User switches to Colorado agent
4. Colorado agent retrieves preferences
5. Colorado agent knows user prefers Python
6. But Colorado agent doesn't see basic agent's conversation history

## Troubleshooting

### Deployment Fails
- Check CloudWatch logs for errors
- Verify `patterns/strands-colorado-agent/` exists
- Ensure all files are present (colorado_agent.py, requirements.txt, Dockerfile)

### Agent Doesn't Respond
- Check CloudWatch logs: `/aws/lambda/marodon-fast-*`
- Verify MEMORY_ID environment variable is set
- Check authentication: user ID extraction working?

### Memory Not Working
- Verify MEMORY_ID matches deployed memory resource
- Check retrieval_config settings
- Look for memory-related errors in logs

### Personality Not Showing
- Verify system prompt is being used
- Check temperature setting (should be 0.7)
- Test with specific questions about Denver/teaching/Napoleon

## Next Steps After Testing

1. **If Colorado works well**:
   - Deploy as separate stack (Option A)
   - Or keep as replacement
   - Or implement multi-agent router

2. **Adapt remaining agents**:
   - UMich agent (with tools)
   - Coder agent (with Code Interpreter)

3. **Frontend enhancements**:
   - Agent selector dropdown
   - Display which agent is active
   - Show agent-specific features

4. **Documentation**:
   - Update main README
   - Document multi-agent architecture
   - Add agent selection guide for users

## Configuration Reference

### Current Stack
- **Stack Name**: `marodon-fast`
- **Memory ID**: `marodonfastmarodonfastbackend8EA31761-64aLtD8bP1`
- **Frontend**: https://main.dy356n1qt88fa.amplifyapp.com
- **Region**: `us-east-1`

### Colorado Agent Config
- **Pattern**: `strands-colorado-agent`
- **Model**: Claude Sonnet 4.5
- **Temperature**: 0.7
- **Tools**: None (conversational only)
- **Session Prefix**: `colorado_`
- **Memory**: Shared with all agents

## Questions?

If you encounter issues:
1. Check CloudWatch logs
2. Review error messages
3. Verify environment variables
4. Test memory access separately
5. Check authentication flow

Ready to deploy!
