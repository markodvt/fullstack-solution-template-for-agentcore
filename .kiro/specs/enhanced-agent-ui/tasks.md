# Implementation Plan: Enhanced Agent UI

## Overview

This implementation plan transforms the current single-agent chat interface into a comprehensive multi-agent management and observability platform. The plan follows an incremental end-to-end delivery approach, where each phase delivers working, testable functionality that users can see and use immediately. This ensures tangible results every week rather than waiting for all backend work to complete first.

**CRITICAL: Data Model Validation**

All backend Lambda implementations MUST include validation sub-tasks BEFORE writing code:
- Research AgentCore API documentation
- Confirm actual response schemas (do NOT guess)
- Test with real AgentCore services (not mocked data)
- Document actual response structures in code

**AgentCore Component Clarifications:**
- Gateway is a TOOLS gateway (not for agent discovery)
- Runtime API is the "agent gateway" (lists and invokes agents)
- Memory strategies have different response schemas
- Observability data source needs validation (Runtime API vs CloudWatch Logs)

**Implementation Language:** Python for backend Lambdas, TypeScript for frontend

## New Phase Structure

The tasks are organized into 6 phases for incremental end-to-end delivery:

1. **Phase 1: Agent Gallery (Week 1)** - Frontend + existing backend verification
2. **Phase 2: Agent Details & Chat Enhancement (Week 2)** - Frontend only, reuses existing backend
3. **Phase 3: Inline Chat Observability (Week 3)** - Frontend + one backend API
4. **Phase 4: Memory Visualization (Week 4)** - Frontend + backend together
5. **Phase 5: Observability Dashboard (Weeks 5-6)** - Frontend + backend together
6. **Phase 6: Polish & Optimization (Week 7)** - Final polish

Each phase delivers working, testable functionality that users can see and use.

## Tasks

### Phase 1: Agent Gallery (Week 1)

This phase delivers the agent discovery and browsing experience. The `/api/agents` endpoint already exists, so we focus on frontend implementation with minimal backend verification.

**Agent Metadata Enhancement:** This phase includes critical backend work to store agent source code in S3 (instead of SSM which has an 8KB limit) and extract metadata (tools, model ID) during CDK deployment. This enhancement is required because 3 out of 4 agent files exceed SSM's 8KB limit. See `.kiro/dev-history/enhanced-agent-ui/implementation-guide.md` for detailed implementation guidance.

- [x] 1. Verify existing /api/agents endpoint
  - [x] 1.1 Test /api/agents endpoint with valid JWT
    - Call existing `/api/agents` endpoint
    - Verify response contains agent list
    - Document actual response format
    - Confirm agent fields: name, description, model, tools, status, Runtime ARN
    - _Requirements: 1.1, 1.2, 10.1_
  
  - [x] 1.2 Verify agent discovery Lambda works correctly
    - Review `infra-cdk/lambdas/agent-discovery/index.py`
    - Verify Runtime API integration
    - Verify SSM parameter integration
    - Test error handling (401, 500)
    - _Requirements: 1.1, 1.2_

- [ ] 1.5 Agent Metadata Enhancement - S3 Storage and Metadata Extraction
  - [ ] 1.5.1 Add S3 bucket for agent source code storage
    - Add `aws-cdk-lib/aws-s3-deployment` import to `backend-stack.ts`
    - Create S3 bucket in `createSharedAgentResources()` method
    - Configure bucket: versioned, encrypted, block public access
    - Set bucket name: `${config.stack_name_base}-agent-source-code`
    - Set removal policy: DESTROY with auto-delete objects
    - Update `SharedAgentResources` interface to include bucket
    - Update return statement to include `agentSourceCodeBucket`
    - _Requirements: 1.4, 3.6_
  
  - [ ] 1.5.2 Implement agent metadata extraction method
    - Add `extractAgentMetadata()` method to `BackendStack` class
    - Parse agent Python source code to extract tools list
    - Parse agent Python source code to extract model ID
    - Handle parsing errors gracefully with fallback values
    - Return structured metadata: `{ tools: string[], modelId: string }`
    - Add comprehensive error handling for missing files
    - _Requirements: 1.4, 1.5, 1.6, 3.4, 3.5_
  
  - [ ] 1.5.3 Implement S3 upload method for agent source code
    - Add `uploadAgentSourceToS3()` method to `BackendStack` class
    - Use `s3deploy.BucketDeployment` to upload source code
    - Generate S3 key: `agents/${agentName}/${agentName}_agent.py`
    - Return S3 URL: `s3://${bucketName}/${key}`
    - Set prune: false to preserve existing files
    - _Requirements: 3.6_
  
  - [ ] 1.5.4 Update storeAgentMetadata to extract and store metadata
    - Add `sharedResources` parameter to `storeAgentMetadata()` method
    - Extract metadata using `extractAgentMetadata()` at method start
    - Upload source code to S3 using `uploadAgentSourceToS3()`
    - Create SSM parameter for tools: `${baseParam}/tools` (JSON array)
    - Create SSM parameter for model: `${baseParam}/model` (string)
    - Create SSM parameter for source code URL: `${baseParam}/source-code-url` (S3 URL)
    - Handle extraction failures gracefully with logging
    - _Requirements: 1.4, 1.5, 1.6, 3.4, 3.5, 3.6_
  
  - [ ] 1.5.5 Update storeAgentMetadata call sites
    - Update `createMultiAgentRuntimes()` method
    - Pass `sharedResources` parameter to `storeAgentMetadata()` calls
    - Verify all call sites are updated
    - _Requirements: 1.4_
  
  - [ ] 1.5.6 Enhance extractAgentMetadata to extract system prompt
    - Update `extractAgentMetadata()` method to extract system_prompt variable
    - Parse multi-line string assignments (triple-quoted strings)
    - Handle both `system_prompt = """..."""` and `system_prompt = '''...'''` formats
    - Look for system_prompt variable in create_*_agent function body
    - Return system prompt in metadata structure
    - Add error handling for missing system prompts (return empty string)
    - _Requirements: 1.4, 3.2_
  
  - [ ] 1.5.7 Create post-deployment script to generate long descriptions
    - Create Python script `infra-cdk/scripts/generate-long-descriptions.py`
    - Script should run after CDK deployment completes
    - For each agent:
      - Fetch the agent's source code from S3
      - Extract the docstring and system prompt from the source code
      - Invoke the default agent via AgentCore Runtime API with a prompt like: "Based on this agent's docstring and system prompt, generate a 2-3 sentence user-friendly description that explains what this agent does and what makes it unique. Focus on capabilities and personality."
      - Parse the agent's response to extract the generated description
      - Store the long description in SSM parameter: `/${stack}/agents/{agent_name}/long-description`
    - Add error handling for agent invocation failures (skip that agent, log warning)
    - Add error handling for missing source code (skip that agent, log warning)
    - Use boto3 for S3, SSM, and Bedrock AgentCore Runtime API calls
    - Script should be idempotent (can be run multiple times safely)
    - _Requirements: 1.4, 3.2_
  
  - [ ] 1.5.8 Update storeAgentMetadata to store system prompt
    - Create SSM parameter for system prompt: `${baseParam}/system-prompt`
    - Handle cases where this field might be empty string
    - Store empty string if extraction failed (don't skip parameter creation)
    - **Note:** Long descriptions are generated by the post-deployment script (task 1.5.7), not during CDK deployment
    - _Requirements: 1.4, 3.2_
  
  - [ ]* 1.5.9 Write unit tests for metadata extraction
    - Test `extractAgentMetadata()` with valid agent files
    - Test tools extraction with various formats
    - Test model ID extraction with various formats
    - Test system prompt extraction with triple-quoted strings
    - Test error handling for missing files
    - Test error handling for malformed source code
    - Test error handling for missing system prompts
    - **Note:** Long description generation is tested separately in the post-deployment script tests
    - _Requirements: 1.4, 1.5, 1.6, 3.2, 3.4, 3.5_
  
  - [ ]* 1.5.10 Write property test for metadata extraction
    - **Property 43: Metadata Extraction Robustness**
    - **Validates: Requirements 1.4, 1.5, 1.6, 3.2**
    - Test that metadata extraction handles any valid Python source
    - Use Hypothesis with minimum 100 iterations

- [ ] 1.6 Agent Discovery Lambda Enhancement - S3 Integration
  - [ ] 1.6.1 Add S3 client to agent-discovery Lambda
    - Import boto3 S3 client in `index.py`
    - Initialize S3 client: `s3_client = boto3.client("s3")`
    - _Requirements: 3.6_
  
  - [ ] 1.6.2 Update get_agent_metadata to handle new SSM parameters
    - Add handling for `tools` parameter (parse JSON array)
    - Add handling for `model` parameter (string)
    - Add handling for `source-code-url` parameter
    - Add handling for `system-prompt` parameter (string)
    - Add handling for `long-description` parameter (string)
    - Parse S3 URL to extract bucket and key
    - Generate presigned URL for source code (1 hour expiry)
    - Fetch source code from S3 using `get_object`
    - Decode source code from bytes to UTF-8 string
    - Add comprehensive error handling for S3 operations
    - Log warnings for S3 failures without breaking response
    - Return system prompt and long description in metadata response
    - _Requirements: 1.4, 1.5, 1.6, 3.2, 3.4, 3.5, 3.6_
  
  - [ ] 1.6.3 Add S3 permissions to agent-discovery Lambda
    - Update `createAgentDiscoveryApi()` in `backend-stack.ts`
    - Add IAM policy statement for S3 GetObject
    - Add IAM policy statement for S3 ListBucket
    - Set resource ARNs: bucket and bucket/*
    - Use `config.stack_name_base` for bucket name
    - _Requirements: 3.6_
  
  - [ ]* 1.6.4 Write unit tests for S3 integration
    - Test presigned URL generation
    - Test source code fetching from S3
    - Test S3 URL parsing
    - Test error handling for missing S3 objects
    - Test error handling for S3 access denied
    - Test JSON parsing for tools parameter
    - Test system prompt parameter retrieval
    - Test long description parameter retrieval
    - _Requirements: 1.4, 1.5, 1.6, 3.2, 3.6_
  
  - [ ]* 1.6.5 Write property test for S3 URL parsing
    - **Property 44: S3 URL Parsing**
    - **Validates: Requirements 3.6**
    - Test that S3 URL parsing handles any valid S3 URL format
    - Use Hypothesis with minimum 100 iterations

- [ ] 1.7 Deploy and verify agent metadata enhancement
  - [ ] 1.7.1 Deploy CDK stack with metadata changes
    - Run `cdk deploy` from `infra-cdk` directory
    - Verify S3 bucket is created
    - Verify agent source files are uploaded to S3
    - Verify SSM parameters include new fields (tools, model, source-code-url)
    - Check CloudWatch logs for any deployment errors
    - _Requirements: 1.4, 1.5, 1.6, 3.4, 3.5, 3.6_
  
  - [ ] 1.7.2 Test agent discovery API with new fields
    - Call `/api/agents` endpoint with valid JWT
    - Verify response includes `tools` array for each agent
    - Verify response includes `model` string for each agent
    - Verify response includes `sourceCode` string for each agent
    - Verify response includes `sourceCodeUrl` presigned URL for each agent
    - Verify response includes `systemPrompt` string for each agent
    - Test with multiple agents to ensure consistency
    - Verify presigned URLs are accessible
    - **Note:** `longDescription` will be available after running the post-deployment script (task 1.5.7)
    - _Requirements: 1.4, 1.5, 1.6, 3.2, 3.4, 3.5, 3.6_
  
  - [ ] 1.7.3 Verify SSM parameters are correctly populated
    - Use AWS CLI to list SSM parameters: `aws ssm get-parameters-by-path --path "/<stack>/agents" --recursive`
    - Verify each agent has `/tools`, `/model`, and `/source-code-url` parameters
    - Verify tools parameter contains valid JSON array
    - Verify model parameter contains model ID string
    - Verify source-code-url parameter contains S3 URL
    - _Requirements: 1.4, 1.5, 1.6, 3.4, 3.5, 3.6_
  
  - [ ] 1.7.4 Verify S3 bucket contents
    - Use AWS CLI to list S3 objects: `aws s3 ls s3://<stack>-agent-source-code/agents/ --recursive`
    - Verify each agent has a source file in S3
    - Verify file paths match expected pattern: `agents/${agentName}/${agentName}_agent.py`
    - Download a sample file to verify content integrity
    - _Requirements: 3.6_
  
  - [ ] 1.7.5 Run post-deployment script to generate long descriptions
    - Run `python infra-cdk/scripts/generate-long-descriptions.py` after CDK deployment
    - Verify script completes without errors
    - Check script logs for any warnings about skipped agents
    - Verify SSM parameters are created: `/<stack>/agents/{agent_name}/long-description`
    - Use AWS CLI to verify: `aws ssm get-parameters-by-path --path "/<stack>/agents" --recursive | grep long-description`
    - _Requirements: 1.4, 3.2_
  
  - [ ] 1.7.6 Test agent discovery API with long descriptions
    - Call `/api/agents` endpoint with valid JWT after running post-deployment script
    - Verify response includes `longDescription` string for each agent
    - Verify long descriptions are user-friendly and 2-3 sentences
    - Verify long descriptions differ from system prompts (not just copied)
    - _Requirements: 1.4, 3.2_
  
  - [ ]* 1.7.7 Write integration test for end-to-end metadata flow
    - Test CDK deployment creates all resources
    - Test metadata extraction during deployment
    - Test S3 upload during deployment
    - Test SSM parameter creation during deployment
    - Test Lambda retrieves metadata from SSM and S3
    - Test API returns complete agent metadata
    - Test post-deployment script generates long descriptions
    - _Requirements: 1.4, 1.5, 1.6, 3.2, 3.4, 3.5, 3.6_

- [ ] 1.9 UI-Based Long Description Generation (Alternative to Script)
  - [ ] 1.9.1 Create backend Lambda for description generation
    - Create `infra-cdk/lambdas/generate-description/index.py`
    - Accept POST request with agent name
    - Fetch agent source code from S3
    - Extract docstring and system prompt from source
    - Invoke default agent via AgentCore Runtime API to generate description
    - Use prompt: "Based on this agent's docstring and system prompt, generate a 2-3 sentence user-friendly description that explains what this agent does and what makes it unique. Focus on capabilities and personality."
    - Parse agent response to extract generated description
    - Store description in SSM parameter: `/${stack}/agents/{agent_name}/long-description`
    - Return generated description in response
    - Add comprehensive error handling (400, 401, 404, 500)
    - Add CORS headers
    - Use JWT token from request for AgentCore authentication
    - _Requirements: 1.4, 3.2_
  
  - [ ] 1.9.2 Add CDK infrastructure for description generation Lambda
    - Define Lambda function in `backend-stack.ts`
    - Set memory: 1024MB, timeout: 120 seconds (agent invocation can be slow)
    - Add environment variables: STACK_NAME_BASE, CORS_ALLOWED_ORIGINS
    - Grant IAM permissions: s3:GetObject (for source code)
    - Grant IAM permissions: ssm:GetParameter, ssm:PutParameter
    - Grant IAM permissions: bedrock-agentcore:InvokeAgent
    - Create CloudWatch log group with 7-day retention
    - Add API Gateway resource: `/agents/{agentName}/generate-description`
    - Add POST method with Cognito authorizer
    - Configure CORS
    - _Requirements: 1.4, 3.2_
  
  - [ ] 1.9.3 Create frontend UI for description generation
    - Add "Generate Description" button to Agent Details page
    - Show button only for admin users (check user role from JWT)
    - Display loading state during generation (can take 30-60 seconds)
    - Show success message with generated description
    - Show error message if generation fails
    - Refresh agent data after successful generation
    - Add confirmation dialog before generating (warns about cost/time)
    - _Requirements: 1.4, 3.2_
  
  - [ ] 1.9.4 Deploy and test UI-based description generation
    - Run `cdk deploy` to deploy Lambda and API
    - Test API endpoint with valid JWT and agent name
    - Verify description is generated and stored in SSM
    - Test UI button in Agent Details page
    - Verify loading state and success/error messages
    - Verify description appears in agent details after generation
    - Test with multiple agents
    - _Requirements: 1.4, 3.2_
  
  - [ ]* 1.9.5 Write unit tests for description generation
    - Test Lambda handler with valid request
    - Test source code extraction from S3
    - Test docstring and system prompt parsing
    - Test agent invocation for description generation
    - Test SSM parameter storage
    - Test error handling for missing source code
    - Test error handling for agent invocation failures
    - Test frontend button visibility for admin users
    - Test frontend loading and success states
    - _Requirements: 1.4, 3.2_

**Note:** This is an alternative to the post-deployment script approach (task 1.5.7). The UI-based approach allows on-demand generation with user authentication, avoiding the JWT token issues encountered with the script approach. Implement this if the script approach continues to have authentication problems.

- [ ] 1.10 Checkpoint - Agent Metadata Enhancement Complete
  - Ensure S3 bucket is created and populated with agent source files
  - Ensure SSM parameters include tools, model, and source-code-url
  - Ensure agent-discovery Lambda fetches and returns new fields
  - Ensure API response includes tools, model, sourceCode, and sourceCodeUrl
  - Users can now see enhanced agent metadata in the UI
  - Ask the user if questions arise

- [ ] 2. Agent Context and State Management (Frontend)
  - [x] 2.1 Create AgentContext for global agent state
    - Create `frontend/src/contexts/AgentContext.tsx`
    - Define AgentContextType interface (agents, loading, error, refetch)
    - Implement AgentProvider component
    - Fetch agents from `/api/agents` on mount
    - Implement useAgents hook for consuming context
    - Add error handling and retry logic
    - _Requirements: 1.1, 1.2, 10.1_
  
  - [x] 2.2 Wrap app root with AgentProvider
    - Update `frontend/src/App.tsx` or main entry point
    - Wrap application with AgentProvider
    - Ensure all pages have access to agent context
    - _Requirements: 1.1, 1.2_
  
  - [ ]* 2.3 Write unit tests for AgentContext
    - Test AgentProvider fetches agents on mount
    - Test useAgents hook returns context
    - Test error handling
    - Test refetch functionality
    - _Requirements: 1.1, 1.2_

- [ ] 3. Agent Gallery Page
  - [x] 3.1 Create Agent Gallery page component structure
    - Create `frontend/src/pages/AgentGalleryPage.tsx`
    - Create AgentGalleryHeader component
    - Create AgentGalleryGrid component
    - Create AgentTile component
    - Use useAgents hook to get agent list
    - Implement responsive grid layout (1 col mobile, 2-3 cols desktop)
    - Add loading skeleton components
    - Add error state with retry button
    - Add empty state for no agents
    - _Requirements: 1.1, 1.2, 1.3, 15.1, 15.2, 15.3_
  
  - [x] 3.2 Implement AgentTile component
    - Display agent name
    - Display agent description
    - Display agent model
    - Display tools count
    - Display deployment status badge (green=deployed, red=failed)
    - Add click handler to navigate to details page
    - Use shadcn/ui Card component
    - Use Lucide React icons
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10_
  
  - [x] 3.3 Add route for Agent Gallery page
    - Update React Router configuration
    - Add `/agents` route
    - Add navigation link in main navigation
    - _Requirements: 1.1_
  
  - [ ]* 3.4 Write unit tests for Agent Gallery
    - Test gallery renders with mock agents
    - Test tiles display all required fields
    - Test click navigation to details page
    - Test loading state
    - Test error state
    - Test empty state
    - Test responsive grid layout
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_
  
  - [ ]* 3.5 Write property test for agent tile completeness
    - **Property 1: Agent Tile Completeness**
    - **Validates: Requirements 1.3, 1.4, 1.5, 1.6, 1.7, 1.8**
    - Test that all agent fields are displayed for any agent
    - Use fast-check with minimum 100 iterations

- [x] 4. Checkpoint - Agent Gallery Complete
  - Ensure S3-based agent metadata enhancement is complete
  - Ensure Agent Gallery page displays all agents with enhanced metadata
  - Ensure navigation works correctly
  - Ensure error handling works
  - Users can now browse and discover agents with tools and model information
  - Ask the user if questions arise


### Phase 2: Agent Details & Chat Enhancement (Week 2)

This phase delivers agent details and enhanced chat functionality. No new backend work is needed - we reuse existing endpoints.

- [ ] 5. Agent Details Page
  - [x] 5.1 Create Agent Details page component structure
    - Create `frontend/src/pages/AgentDetailsPage.tsx`
    - Create AgentDetailsHeader component (name, status, back button)
    - Create AgentDetailsOverview component
    - Create AgentCodeViewer component
    - Create AgentDetailsActions component
    - Use useAgents hook and filter by agent name from route params
    - Add breadcrumb navigation
    - _Requirements: 3.1, 3.2_
  
  - [x] 5.2 Implement agent metadata display
    - Display agent name
    - Display agent description
    - Display agent model specification
    - Display complete tools list with descriptions (expandable)
    - Display Runtime ARN with copy-to-clipboard
    - Display deployment status
    - Use shadcn/ui components (Card, Badge, Button)
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.7, 3.8_
  
  - [x] 5.3 Implement code viewer with syntax highlighting
    - Install react-syntax-highlighter dependency
    - Display agent Python source code
    - Add syntax highlighting for Python
    - Add copy-to-clipboard button for code
    - Handle missing source code gracefully
    - _Requirements: 3.6_
  
  - [x] 5.4 Implement chat button with status handling
    - Add "Chat" button in actions section
    - Disable button if deployment status is "failed"
    - Navigate to `/chat?agent=:agentName` on click
    - Add visual indicator for disabled state
    - _Requirements: 3.9, 3.10_
  
  - [x] 5.5 Add route for Agent Details page
    - Update React Router configuration
    - Add `/agents/:agentName` route
    - Extract agentName from route params
    - _Requirements: 3.1_
  
  - [ ]* 5.6 Write unit tests for Agent Details
    - Test details page renders with mock agent
    - Test all metadata fields are displayed
    - Test code viewer displays source code
    - Test chat button navigation
    - Test chat button disabled for failed agents
    - Test breadcrumb navigation
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_
  
  - [ ]* 5.7 Write property test for agent details completeness
    - **Property 3: Agent Details Completeness**
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**
    - Test that all agent detail fields are displayed for any agent
    - Use fast-check with minimum 100 iterations
  
  - [ ]* 5.8 Write property test for chat button availability
    - **Property 4: Chat Button Availability**
    - **Validates: Requirements 3.10**
    - Test that chat button is disabled for failed agents
    - Use fast-check with minimum 100 iterations

- [ ] 6. Chat Page Enhancement
  - [x] 6.1 Add agent selector to chat page
    - Update `frontend/src/pages/ChatPage.tsx` (or equivalent)
    - Add AgentSelector dropdown component in chat header
    - Populate dropdown with agents from useAgents hook
    - Display selected agent name prominently in header
    - _Requirements: 4.1, 4.3_
  
  - [x] 6.2 Implement URL query parameter handling
    - Read `agent` query parameter from URL on page load
    - If present, select that agent in dropdown
    - If not present, use default agent
    - Update URL when agent is changed via dropdown
    - _Requirements: 4.1_
  
  - [x] 6.3 Update AgentCore client connection logic
    - Retrieve Runtime ARN for selected agent
    - Establish connection to selected agent's Runtime ARN
    - Disconnect from previous agent when switching
    - Clear conversation history when switching agents
    - Maintain existing streaming functionality
    - _Requirements: 4.2, 4.5, 4.6_
  
  - [x] 6.4 Implement agent switching functionality
    - Handle agent selector change event
    - Update URL query parameter
    - Disconnect current agent connection
    - Connect to new agent's Runtime ARN
    - Clear conversation UI
    - Display loading state during connection
    - _Requirements: 4.8_
  
  - [ ]* 6.5 Write unit tests for chat enhancements
    - Test agent selector renders with agents
    - Test URL query parameter parsing
    - Test agent selection updates connection
    - Test agent switching clears conversation
    - Test selected agent name display
    - _Requirements: 4.1, 4.2, 4.3, 4.8_
  
  - [ ]* 6.6 Write property test for agent selection connection
    - **Property 5: Agent Selection Connection**
    - **Validates: Requirements 4.2, 4.3**
    - Test that selected agent establishes correct connection
    - Use fast-check with minimum 100 iterations
  
  - [ ]* 6.7 Write property test for message persistence
    - **Property 6: Message Persistence**
    - **Validates: Requirements 4.7**
    - Test that messages remain visible during session
    - Use fast-check with minimum 100 iterations

- [ ] 7. Navigation Enhancement
  - [x] 7.1 Update main navigation component
    - Add "Agents" link to `/agents`
    - Add active link highlighting
    - Use Lucide React icons
    - Maintain existing navigation patterns
    - _Requirements: 1.1_
  
  - [ ]* 7.2 Write unit tests for navigation
    - Test all navigation links are present
    - Test active link highlighting
    - Test navigation to each page
    - _Requirements: 1.1_

- [x] 8. Checkpoint - Agent Details & Chat Complete
  - Ensure Agent Details page displays all information
  - Ensure chat page has agent selector
  - Ensure agent switching works
  - Users can now view agent details and chat with any agent
  - Ask the user if questions arise


### Phase 3: Inline Chat Observability (Week 3)

This phase delivers real-time observability in the chat interface. We implement the Observability Traces API Lambda and inline trace visualization.

- [ ] 9. Observability Traces API Lambda - Validation and Implementation
  - [ ] 9.1 Research trace data source options
    - Read AgentCore Runtime API documentation for GetTrace
    - Read AgentCore Observability API documentation (if available)
    - Review CloudWatch Logs API documentation
    - Test Runtime API GetTrace with real service
    - Test CloudWatch Logs FilterLogEvents for OTEL traces
    - **DECISION REQUIRED:** Choose Runtime API vs CloudWatch Logs
    - Document chosen approach and rationale
    - _Requirements: 7.1, 12.4_
  
  - [ ] 9.2 Validate OTEL trace format structure
    - Retrieve real trace data from chosen API source
    - Document OTEL trace structure (traces, spans, attributes)
    - Document span types: agent_invocation, llm_invocation, tool_call
    - Document span attributes for each type
    - Document parent-child relationship structure (parentSpanId)
    - Confirm timestamp format (ISO 8601)
    - Confirm duration units (milliseconds)
    - **CRITICAL:** Do NOT guess OTEL format - validate with real traces
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 12.8_
  
  - [ ] 9.3 Implement Observability Traces API Lambda handler
    - Create `infra-cdk/lambdas/observability-traces/index.py`
    - Implement JWT token validation using Cognito
    - Extract user ID from JWT token for scoping
    - Query chosen API source for trace data
    - Parse OTEL format into simplified JSON structure
    - Build span parent-child relationships
    - Extract span attributes (tool name, LLM model, tokens, etc.)
    - Handle missing or malformed traces
    - Add comprehensive error handling (400, 401, 404, 500)
    - Add CORS headers
    - Use AWS Lambda Powertools for structured logging
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 12.4, 12.8_
  
  - [ ]* 9.4 Write unit tests for Traces Lambda
    - Test valid requests return 200
    - Test missing auth returns 401
    - Test invalid session ID returns 400
    - Test session not found returns 404
    - Test service errors return 500
    - Test CORS headers are present
    - Test OTEL parsing logic
    - Test span tree building
    - Test span attribute extraction
    - _Requirements: 7.1, 7.2, 7.3, 12.4_
  
  - [ ]* 9.5 Write property test for span hierarchy
    - **Property 16: Span Hierarchy**
    - **Validates: Requirements 7.10**
    - Test that span tree correctly represents parent-child relationships
    - Use Hypothesis with minimum 100 iterations

- [ ] 10. CDK Infrastructure for Traces API
  - [ ] 10.1 Add Traces Lambda to CDK stack
    - Define Lambda function in `backend-stack.ts`
    - Set memory: 512MB, timeout: 30 seconds
    - Add environment variables: STACK_NAME_BASE, CORS_ALLOWED_ORIGINS
    - Grant IAM permissions: bedrock-agentcore:GetTrace (or logs:FilterLogEvents)
    - Grant IAM permissions: ssm:GetParameter
    - Create CloudWatch log group with 7-day retention
    - _Requirements: 7.1, 12.4_
  
  - [ ] 10.2 Add API Gateway resource for traces
    - Add `/observability/traces/{sessionId}` resource to API Gateway
    - Add GET method with Cognito authorizer
    - Configure CORS
    - _Requirements: 12.4_
  
  - [ ] 10.3 Deploy and test Traces API
    - Run `cdk deploy` to deploy backend changes
    - Call `/api/observability/traces/:sessionId` endpoint with valid JWT
    - Verify response contains trace data
    - Verify span parsing is correct
    - Test error handling (401, 400, 404, 500)
    - **CRITICAL:** Validate actual response format matches documented schema
    - _Requirements: 7.1, 7.2, 7.3, 12.4_

- [ ] 11. Inline Observability Component (Frontend)
  - [ ] 11.1 Create Observability service layer
    - Create `frontend/src/services/observabilityService.ts`
    - Define Span, Trace interfaces
    - Implement fetchTraces function
    - Add JWT token handling
    - Add error handling
    - _Requirements: 7.1_
  
  - [ ] 11.2 Create inline trace visualization component
    - Create `frontend/src/components/InlineTraceViewer.tsx`
    - Display expandable trace section in chat message
    - Show "View Trace" button for each assistant message
    - Fetch trace data when expanded
    - Display loading state while fetching
    - Handle trace retrieval errors
    - _Requirements: 7.1, 7.2_
  
  - [ ] 11.3 Create compact span timeline
    - Create CompactSpanTimeline component
    - Display spans on horizontal timeline
    - Color code spans by type (tool=blue, LLM=green, agent=purple)
    - Show span duration visually
    - Add hover tooltips with span details
    - Keep visualization compact for inline display
    - _Requirements: 7.2, 7.3_
  
  - [ ] 11.4 Create span details panel
    - Create SpanDetails component
    - Display span name, duration, and status
    - For tool spans: display tool name, input, output
    - For LLM spans: display model, prompt, response, token counts
    - For error spans: display error message
    - Add expand/collapse functionality
    - _Requirements: 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_
  
  - [ ] 11.5 Integrate inline trace viewer into chat
    - Update chat message component to include InlineTraceViewer
    - Pass session ID to trace viewer
    - Ensure trace viewer only shows for assistant messages
    - Test with real chat sessions
    - _Requirements: 7.1, 7.2_
  
  - [ ]* 11.6 Write unit tests for inline observability
    - Test trace viewer renders correctly
    - Test span timeline displays spans
    - Test span details show all attributes
    - Test tool span rendering
    - Test LLM span rendering
    - Test error handling
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_
  
  - [ ]* 11.7 Write property test for span completeness
    - **Property 13: Span Completeness**
    - **Validates: Requirements 7.3, 7.4, 7.5, 7.6, 7.7, 12.8**
    - Test that all span fields are displayed for any span
    - Use fast-check with minimum 100 iterations

- [ ] 12. Checkpoint - Inline Chat Observability Complete
  - Ensure Traces API Lambda is deployed and working
  - Ensure inline trace viewer displays in chat
  - Ensure span visualization works correctly
  - Users can now see real-time observability in chat
  - Ask the user if questions arise


### Phase 4: Memory Visualization (Week 4)

This phase delivers the memory visualization feature end-to-end with both backend and frontend.

- [ ] 13. Memory API Lambda - Validation and Implementation
  - [ ] 13.1 Research AgentCore Memory API documentation
    - Read AWS Bedrock AgentCore Memory API documentation
    - Review `docs/MEMORY_INTEGRATION.md` in repository
    - Review memory configuration in `backend-stack.ts` (lines 310-330)
    - Document memory strategies: SummaryMemoryStrategy, UserPreferenceMemoryStrategy, SemanticMemoryStrategy
    - _Requirements: 11.1, 11.2_
  
  - [ ] 13.2 Validate memory strategy response schemas
    - Deploy test Lambda to call Memory API
    - Test ListEvents API with real Memory service
    - Test RetrieveMemoryRecords API with real Memory service
    - Document actual response format for EACH memory strategy type
    - Confirm namespace patterns for each strategy
    - **CRITICAL:** Do NOT guess schemas - validate with real responses
    - _Requirements: 11.5, 11.6, 11.7, 11.8, 11.9, 11.10_
  
  - [ ] 13.3 Implement Memory API Lambda handler
    - Create `infra-cdk/lambdas/memory/index.py`
    - Implement JWT token validation using Cognito
    - Extract user ID from JWT token for scoping
    - Query AgentCore Memory API with user scoping
    - Implement filtering by agent name (query parameter)
    - Implement filtering by user ID (query parameter)
    - Implement sorting by timestamp (query parameter)
    - Implement pagination with nextToken
    - Handle empty results (return empty array)
    - Add comprehensive error handling (400, 401, 500)
    - Add CORS headers
    - Use AWS Lambda Powertools for structured logging
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.11, 11.12_
  
  - [ ]* 13.4 Write unit tests for Memory Lambda
    - Test valid requests return 200
    - Test missing auth returns 401
    - Test invalid parameters return 400
    - Test service errors return 500
    - Test CORS headers are present
    - Test user ID extraction from JWT
    - Test filtering by agent name
    - Test filtering by user ID
    - Test sorting by timestamp
    - Test pagination
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  
  - [ ]* 13.5 Write property test for memory filtering
    - **Property 8: Memory Agent Filtering**
    - **Validates: Requirements 5.8, 11.3**
    - Test that filtered memories only include matching agent names
    - Use Hypothesis with minimum 100 iterations
  
  - [ ]* 13.6 Write property test for memory user filtering
    - **Property 9: Memory User Filtering**
    - **Validates: Requirements 5.9, 11.4**
    - Test that filtered memories only include matching user IDs
    - Use Hypothesis with minimum 100 iterations
  
  - [ ]* 13.7 Write property test for memory sorting
    - **Property 10: Memory Timestamp Sorting**
    - **Validates: Requirements 5.10**
    - Test that sorted memories are ordered correctly by timestamp
    - Use Hypothesis with minimum 100 iterations

- [ ] 14. CDK Infrastructure for Memory API
  - [ ] 14.1 Add Memory API Lambda to CDK stack
    - Define Lambda function in `backend-stack.ts`
    - Set memory: 512MB, timeout: 30 seconds
    - Add environment variables: STACK_NAME_BASE, CORS_ALLOWED_ORIGINS, MEMORY_ID
    - Grant IAM permissions: bedrock-agentcore:GetEvent, ListEvents, RetrieveMemoryRecords
    - Grant IAM permissions: ssm:GetParameter
    - Create CloudWatch log group with 7-day retention
    - _Requirements: 11.1, 11.2_
  
  - [ ] 14.2 Add API Gateway resource for memory
    - Add `/memory` resource to API Gateway
    - Add GET method with Cognito authorizer
    - Configure CORS
    - _Requirements: 11.1_
  
  - [ ] 14.3 Deploy and test Memory API
    - Run `cdk deploy` to deploy backend changes
    - Call `/api/memory` endpoint with valid JWT
    - Verify response contains memory entries
    - Test filtering by agent name
    - Test filtering by user ID
    - Test sorting by timestamp
    - Test pagination
    - Test error handling (401, 400, 500)
    - **CRITICAL:** Validate actual response format matches documented schema
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [ ] 15. Memory Page (Frontend)
  - [ ] 15.1 Create Memory service layer
    - Create `frontend/src/services/memoryService.ts`
    - Define Memory interface
    - Define MemoryResponse interface
    - Implement fetchMemories function with filters
    - Add JWT token handling
    - Add error handling
    - _Requirements: 5.1, 5.2, 11.1_
  
  - [ ] 15.2 Create Memory page component structure
    - Create `frontend/src/pages/MemoryPage.tsx`
    - Create MemoryPageHeader component
    - Create MemoryFilters component
    - Create MemoryList component
    - Create MemoryCard component
    - Use memoryService to fetch data
    - Add loading skeleton components
    - Add error state with retry button
    - Add empty state for no memories
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ] 15.3 Implement memory filters
    - Add agent name filter dropdown (populated from useAgents)
    - Add user ID filter text input with debounce
    - Add sort order toggle (timestamp asc/desc)
    - Refetch memories when filters change
    - Display active filters
    - Add clear filters button
    - _Requirements: 5.8, 5.9, 5.10_
  
  - [ ] 15.4 Implement MemoryCard component
    - Display agent name
    - Display user identifier
    - Display memory content
    - Display timestamp (formatted)
    - Display memory ID
    - Use shadcn/ui Card component
    - _Requirements: 5.3, 5.4, 5.5, 5.6, 5.7_
  
  - [ ] 15.5 Add route for Memory page
    - Update React Router configuration
    - Add `/memory` route
    - Add navigation link in main navigation
    - _Requirements: 5.1_
  
  - [ ]* 15.6 Write unit tests for Memory page
    - Test memory page renders with mock data
    - Test memory cards display all fields
    - Test agent filter works
    - Test user filter works
    - Test sort order toggle works
    - Test loading state
    - Test error state
    - Test empty state
    - _Requirements: 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10_
  
  - [ ]* 15.7 Write property test for memory entry completeness
    - **Property 7: Memory Entry Completeness**
    - **Validates: Requirements 5.3, 5.4, 5.5, 5.6, 5.7**
    - Test that all memory fields are displayed for any memory
    - Use fast-check with minimum 100 iterations

- [ ] 16. Checkpoint - Memory Visualization Complete
  - Ensure Memory API Lambda is deployed and working
  - Ensure Memory page displays all memories
  - Ensure filtering and sorting work correctly
  - Users can now visualize agent memories
  - Ask the user if questions arise


### Phase 5: Observability Dashboard (Weeks 5-6)

This phase delivers the standalone observability dashboard with sessions and metrics.

- [ ] 17. Observability Sessions API Lambda - Validation and Implementation
  - [ ] 17.1 Research AgentCore Runtime API documentation
    - Read AWS Bedrock AgentCore Runtime API documentation
    - Review Runtime configuration in `backend-stack.ts`
    - Document ListSessions API parameters and response format
    - Document GetSession API parameters and response format
    - Confirm session metadata fields available
    - _Requirements: 6.1, 6.2, 12.1, 12.2_
  
  - [ ] 17.2 Validate session response schemas
    - Deploy test Lambda to call Runtime API
    - Test ListSessions API with real Runtime service
    - Test GetSession API with real Runtime service
    - Document actual response format for sessions
    - Confirm available session fields (ID, agent, user, duration, status)
    - **CRITICAL:** Do NOT guess schemas - validate with real responses
    - _Requirements: 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 12.7_
  
  - [ ] 17.3 Implement Observability Sessions API Lambda handler
    - Create `infra-cdk/lambdas/observability-sessions/index.py`
    - Implement JWT token validation using Cognito
    - Extract user ID from JWT token for scoping
    - Query AgentCore Runtime API for sessions
    - Implement filtering by agent name (query parameter)
    - Implement filtering by time range (query parameter)
    - Implement pagination with nextToken
    - Handle empty results (return empty array)
    - Add comprehensive error handling (400, 401, 500)
    - Add CORS headers
    - Use AWS Lambda Powertools for structured logging
    - _Requirements: 6.1, 6.2, 12.1, 12.2, 12.3, 12.5, 12.6, 12.9, 12.10_
  
  - [ ]* 17.4 Write unit tests for Sessions Lambda
    - Test valid requests return 200
    - Test missing auth returns 401
    - Test invalid parameters return 400
    - Test service errors return 500
    - Test CORS headers are present
    - Test user ID extraction from JWT
    - Test filtering by agent name
    - Test filtering by time range
    - Test pagination
    - _Requirements: 12.1, 12.2, 12.5, 12.6_
  
  - [ ]* 17.5 Write property test for session filtering
    - **Property 20: Agent Session Filtering**
    - **Validates: Requirements 12.6**
    - Test that filtered sessions only include matching agent names
    - Use Hypothesis with minimum 100 iterations

- [ ] 18. Observability Metrics API Lambda - Validation and Implementation
  - [ ] 18.1 Research metrics aggregation approach
    - Review Runtime API session data structure
    - Determine how to calculate total sessions
    - Determine how to calculate average duration
    - Determine how to calculate token usage (from traces)
    - Determine how to calculate success rate
    - Determine how to identify top tools
    - Document aggregation logic
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_
  
  - [ ] 18.2 Implement Observability Metrics API Lambda handler
    - Create `infra-cdk/lambdas/observability-metrics/index.py`
    - Implement JWT token validation using Cognito
    - Extract user ID from JWT token for scoping
    - Query Runtime API for sessions in time range
    - Aggregate metrics: total sessions, avg duration, token usage, success rate
    - Calculate per-agent breakdowns
    - Identify top tools from trace data
    - Implement time range filtering (query parameter)
    - Add comprehensive error handling (400, 401, 500)
    - Add CORS headers
    - Use AWS Lambda Powertools for structured logging
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9_
  
  - [ ]* 18.3 Write unit tests for Metrics Lambda
    - Test valid requests return 200
    - Test missing auth returns 401
    - Test invalid parameters return 400
    - Test service errors return 500
    - Test CORS headers are present
    - Test metrics aggregation logic
    - Test per-agent breakdown calculation
    - Test top tools identification
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [ ] 19. CDK Infrastructure for Observability APIs
  - [ ] 19.1 Add Sessions and Metrics Lambdas to CDK stack
    - Define Sessions Lambda function in `backend-stack.ts`
    - Define Metrics Lambda function in `backend-stack.ts`
    - Set memory: 512MB, timeout: 30 seconds for each
    - Add environment variables: STACK_NAME_BASE, CORS_ALLOWED_ORIGINS
    - Grant IAM permissions: bedrock-agentcore:ListSessions, GetSession, GetTrace
    - Grant IAM permissions: ssm:GetParameter
    - Create CloudWatch log groups with 7-day retention
    - _Requirements: 6.1, 6.2, 8.1, 12.1, 12.2_
  
  - [ ] 19.2 Add API Gateway resources for observability
    - Add `/observability/sessions` resource
    - Add GET method to `/observability/sessions` with Cognito authorizer
    - Add `/observability/metrics` resource
    - Add GET method to `/observability/metrics` with Cognito authorizer
    - Configure CORS for all endpoints
    - _Requirements: 12.1, 12.2_
  
  - [ ] 19.3 Deploy and test Observability APIs
    - Run `cdk deploy` to deploy backend changes
    - Call `/api/observability/sessions` endpoint with valid JWT
    - Verify response contains session entries
    - Test filtering by agent name and time range
    - Call `/api/observability/metrics` endpoint
    - Verify metrics aggregation is correct
    - Test error handling (401, 400, 500)
    - **CRITICAL:** Validate actual response formats match documented schemas
    - _Requirements: 6.1, 6.2, 8.1, 12.1, 12.2_

- [ ] 20. Observability Dashboard Page (Frontend)
  - [ ] 20.1 Create Observability Dashboard page structure
    - Create `frontend/src/pages/ObservabilityDashboard.tsx`
    - Create ObservabilityTabs component (Metrics, Sessions)
    - Create MetricsTab component
    - Create SessionsTab component
    - Use observabilityService to fetch data
    - Add loading states
    - Add error states
    - _Requirements: 6.1, 6.2, 8.1_
  
  - [ ] 20.2 Implement Sessions Tab
    - Create SessionFilters component (agent, time range)
    - Create SessionList component
    - Create SessionCard component
    - Display session ID, agent name, user ID, start time, duration, status
    - Add status indicators (completed=green, failed=red, in-progress=yellow)
    - Add click handler to expand session and show traces inline
    - Implement time range filtering (1h, 24h, 7d, 30d)
    - Implement agent name filtering
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10_
  
  - [ ] 20.3 Integrate trace viewer into Sessions Tab
    - Reuse InlineTraceViewer component from Phase 3
    - Show traces when session is expanded
    - Display full trace timeline and span details
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10_
  
  - [ ] 20.4 Implement Metrics Tab
    - Install recharts dependency
    - Create MetricsSummary component
    - Display total sessions count
    - Display total token usage
    - Display average session duration
    - Display success rate
    - Use shadcn/ui Card components
    - _Requirements: 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_
  
  - [ ] 20.5 Create per-agent metrics breakdown
    - Create AgentMetricsTable component
    - Display table with columns: agent name, session count, token usage, avg duration, success rate
    - Add sorting by each column
    - Use shadcn/ui Table component
    - _Requirements: 8.3, 8.4, 8.6, 8.7_
  
  - [ ] 20.6 Create top tools chart
    - Create TopToolsChart component
    - Display bar chart of most frequently used tools
    - Use recharts BarChart component
    - _Requirements: 8.8_
  
  - [ ] 20.7 Implement time range selector
    - Create TimeRangeSelector component
    - Add buttons for 1h, 24h, 7d, 30d
    - Refetch metrics when time range changes
    - Display selected time range
    - _Requirements: 8.9_
  
  - [ ] 20.8 Implement auto-refresh for metrics
    - Add auto-refresh every 30 seconds
    - Display last updated timestamp
    - Add manual refresh button
    - Pause auto-refresh when user is interacting
    - _Requirements: 8.10_
  
  - [ ] 20.9 Add route for Observability Dashboard
    - Update React Router configuration
    - Add `/observability` route
    - Add navigation link in main navigation
    - _Requirements: 6.1_
  
  - [ ]* 20.10 Write unit tests for Observability Dashboard
    - Test dashboard renders with tabs
    - Test sessions tab displays sessions
    - Test session cards display all fields
    - Test time range filtering
    - Test agent filtering
    - Test session expansion with traces
    - Test metrics tab displays all metrics
    - Test per-agent breakdown table
    - Test top tools chart
    - Test auto-refresh functionality
    - _Requirements: 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10_
  
  - [ ]* 20.11 Write property test for session entry completeness
    - **Property 11: Session Entry Completeness**
    - **Validates: Requirements 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 12.7**
    - Test that all session fields are displayed for any session
    - Use fast-check with minimum 100 iterations
  
  - [ ]* 20.12 Write property test for metrics completeness
    - **Property 18: Metrics Completeness**
    - **Validates: Requirements 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8**
    - Test that all metrics are displayed for any time range
    - Use fast-check with minimum 100 iterations

- [ ] 21. Checkpoint - Observability Dashboard Complete
  - Ensure Sessions and Metrics APIs are deployed and working
  - Ensure Observability Dashboard displays all data
  - Ensure filtering and time range selection work
  - Ensure trace integration works in sessions
  - Users can now access comprehensive observability dashboard
  - Ask the user if questions arise


### Phase 6: Polish & Optimization (Week 7)

This phase adds final polish, accessibility, error handling, and performance optimization.

- [ ] 22. Responsive Design Implementation
  - [ ] 22.1 Implement responsive layouts for all pages
    - Test all pages at mobile breakpoint (< 768px)
    - Test all pages at tablet breakpoint (768px - 1024px)
    - Test all pages at desktop breakpoint (> 1024px)
    - Adjust grid layouts, spacing, and component sizes
    - Ensure touch-friendly button sizes (min 44x44px)
    - _Requirements: 15.1, 15.2, 15.3_
  
  - [ ]* 22.2 Write property test for responsive grid layout
    - **Property 37: Responsive Grid Layout**
    - **Validates: Requirements 15.1, 15.2, 15.3**
    - Test that grid adapts to viewport width
    - Use fast-check with minimum 100 iterations

- [ ] 23. Keyboard Navigation Implementation
  - [ ] 23.1 Add keyboard navigation support
    - Ensure Tab key navigates through interactive elements
    - Ensure Enter/Space activates buttons and links
    - Ensure Arrow keys navigate lists
    - Ensure Escape closes modals and dropdowns
    - Test keyboard navigation on all pages
    - _Requirements: 15.4_
  
  - [ ]* 23.2 Write property test for keyboard navigation
    - **Property 38: Keyboard Navigation**
    - **Validates: Requirements 15.4**
    - Test that all interactive elements support keyboard navigation
    - Use fast-check with minimum 100 iterations

- [ ] 24. Accessibility Enhancements
  - [ ] 24.1 Add ARIA labels to all interactive elements
    - Add aria-label to buttons without text
    - Add aria-describedby for form inputs
    - Add role attributes where needed
    - Add aria-expanded for expandable sections
    - Add aria-selected for selected items
    - _Requirements: 15.5_
  
  - [ ] 24.2 Add focus indicators
    - Ensure visible focus rings on all focusable elements
    - Use consistent focus styling across all components
    - Test focus indicators with keyboard navigation
    - _Requirements: 15.8_
  
  - [ ] 24.3 Verify color contrast
    - Test all text against backgrounds for 4.5:1 contrast ratio
    - Adjust colors if needed to meet WCAG AA standards
    - Test status indicators (green, red, yellow) for contrast
    - _Requirements: 15.6_
  
  - [ ] 24.4 Add alternative text for images and icons
    - Add alt text to all images
    - Add aria-label to icon-only buttons
    - Ensure screen readers can understand all visual elements
    - _Requirements: 15.10_
  
  - [ ] 24.5 Test with screen readers
    - Test with NVDA (Windows) or VoiceOver (Mac)
    - Verify all content is accessible
    - Verify navigation makes sense
    - Fix any issues found
    - _Requirements: 15.7_
  
  - [ ]* 24.6 Write property test for ARIA labels
    - **Property 39: ARIA Labels**
    - **Validates: Requirements 15.5**
    - Test that all interactive elements have ARIA labels
    - Use fast-check with minimum 100 iterations
  
  - [ ]* 24.7 Write property test for color contrast
    - **Property 40: Color Contrast**
    - **Validates: Requirements 15.6**
    - Test that all text meets 4.5:1 contrast ratio
    - Use fast-check with minimum 100 iterations
  
  - [ ]* 24.8 Write property test for focus indicators
    - **Property 41: Focus Indicators**
    - **Validates: Requirements 15.8**
    - Test that all focusable elements have visible focus indicators
    - Use fast-check with minimum 100 iterations

- [ ] 25. Zoom Support Testing
  - [ ] 25.1 Test zoom functionality
    - Test all pages at 100%, 150%, and 200% zoom
    - Ensure all functionality remains usable
    - Ensure no content is cut off or overlapping
    - Fix any layout issues
    - _Requirements: 15.9_
  
  - [ ]* 25.2 Write property test for zoom support
    - **Property 42: Zoom Support**
    - **Validates: Requirements 15.9**
    - Test that all pages remain functional at 200% zoom
    - Use fast-check with minimum 100 iterations

- [ ] 26. Error Handling Polish
  - [ ] 26.1 Implement comprehensive error states
    - Add user-friendly error messages for all API failures
    - Add retry buttons for failed operations
    - Add error boundaries for React errors
    - Ensure no technical details exposed to users
    - Log detailed errors to CloudWatch
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_
  
  - [ ] 26.2 Implement timeout handling
    - Set 30-second timeout for all API requests
    - Display timeout error message
    - Add retry button for timeout errors
    - _Requirements: 14.8, 14.9, 14.10_
  
  - [ ]* 26.3 Write property test for error message display
    - **Property 33: Error Message Display**
    - **Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5, 14.6**
    - Test that user-friendly errors are displayed for any failure
    - Use fast-check with minimum 100 iterations
  
  - [ ]* 26.4 Write property test for retry functionality
    - **Property 36: Retry Functionality**
    - **Validates: Requirements 14.9, 14.10**
    - Test that retry button reattempts failed operations
    - Use fast-check with minimum 100 iterations

- [ ] 27. Frontend Performance Optimization
  - [ ] 27.1 Implement code splitting by route
    - Use React.lazy for route-level code splitting
    - Add Suspense boundaries with loading states
    - Verify bundle sizes are reduced
    - _Requirements: Performance optimization_
  
  - [ ] 27.2 Implement lazy loading for heavy components
    - Lazy load syntax highlighter component
    - Lazy load recharts components
    - Lazy load trace visualization components
    - _Requirements: Performance optimization_
  
  - [ ] 27.3 Add memoization for expensive computations
    - Use React.memo for expensive components
    - Use useMemo for expensive calculations
    - Use useCallback for event handlers
    - Profile and optimize render performance
    - _Requirements: Performance optimization_
  
  - [ ] 27.4 Implement debouncing for filter inputs
    - Add debounce to memory user ID filter
    - Add debounce to search inputs
    - Set debounce delay to 300ms
    - _Requirements: Performance optimization_
  
  - [ ] 27.5 Implement virtual scrolling for large lists
    - Add virtual scrolling to memory list (if > 100 items)
    - Add virtual scrolling to session list (if > 100 items)
    - Use react-window or similar library
    - _Requirements: Performance optimization_

- [ ] 28. Backend Performance Optimization
  - [ ] 28.1 Optimize Lambda memory allocation
    - Profile Lambda execution times
    - Adjust memory allocation based on profiling
    - Test with different memory settings (256MB, 512MB, 1024MB)
    - Choose optimal memory for cost/performance balance
    - _Requirements: Performance optimization_
  
  - [ ] 28.2 Implement SSM parameter caching
    - Cache SSM parameters in Lambda with 5-minute TTL
    - Reduce SSM API calls
    - Improve Lambda cold start performance
    - _Requirements: Performance optimization_
  
  - [ ] 28.3 Add response compression
    - Enable gzip compression in API Gateway
    - Verify response sizes are reduced
    - _Requirements: Performance optimization_
  
  - [ ] 28.4 Implement pagination for large result sets
    - Add pagination to memory API (limit 50 per page)
    - Add pagination to sessions API (limit 50 per page)
    - Return nextToken for pagination
    - Update frontend to handle pagination
    - _Requirements: Performance optimization_

- [ ] 29. Monitoring and Observability Setup
  - [ ] 29.1 Create CloudWatch dashboard
    - Add Lambda invocation metrics
    - Add Lambda error metrics
    - Add Lambda duration metrics
    - Add API Gateway 4xx/5xx metrics
    - Add API Gateway latency metrics
    - _Requirements: Monitoring_
  
  - [ ] 29.2 Create CloudWatch alarms
    - Add alarm for Lambda error rate > 5%
    - Add alarm for API Gateway 5xx rate > 1%
    - Add alarm for Lambda duration > 25 seconds
    - Add alarm for Memory API failures
    - Configure SNS notifications
    - _Requirements: Monitoring_
  
  - [ ] 29.3 Verify structured logging
    - Ensure all Lambdas use AWS Lambda Powertools
    - Ensure all errors are logged with stack traces
    - Ensure all requests are logged with user ID
    - Set CloudWatch log retention to 7 days
    - _Requirements: Monitoring_

- [ ] 30. Final Testing and Deployment
  - [ ] 30.1 Run full test suite
    - Run all unit tests (frontend and backend)
    - Run all property-based tests
    - Run linting and type checking
    - Ensure all tests pass
    - _Requirements: Testing_
  
  - [ ] 30.2 Run integration tests
    - Test all user flows end-to-end
    - Test agent discovery flow
    - Test memory visualization flow
    - Test observability flow
    - Test chat integration flow
    - Test error handling flow
    - _Requirements: Testing_
  
  - [ ] 30.3 Deploy to staging environment
    - Deploy backend CDK stack to staging
    - Deploy frontend to Amplify staging
    - Run smoke tests against staging
    - Verify all functionality works
    - _Requirements: Deployment_
  
  - [ ] 30.4 Performance testing
    - Test with large datasets (100+ agents, 1000+ memories, 1000+ sessions)
    - Measure page load times
    - Measure API response times
    - Verify performance is acceptable
    - _Requirements: Performance testing_
  
  - [ ] 30.5 Security review
    - Verify all API endpoints require authentication
    - Verify CORS configuration is correct
    - Verify no sensitive data in logs
    - Verify rate limiting works
    - Verify user data scoping works
    - _Requirements: Security_
  
  - [ ] 30.6 Deploy to production
    - Deploy backend CDK stack to production
    - Deploy frontend to Amplify production
    - Run smoke tests against production
    - Monitor CloudWatch metrics and alarms
    - Verify all functionality works
    - _Requirements: Deployment_

- [ ] 31. Final Checkpoint - Feature Complete
  - Ensure all phases are complete
  - Ensure all tests pass
  - Ensure performance is optimized
  - Ensure monitoring is set up
  - Ensure production deployment is successful
  - Ask the user if questions arise


## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation after each phase
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- Validation sub-tasks in backend phases are CRITICAL and must be completed before implementation
- All backend Lambda implementations must validate API response schemas against AgentCore documentation
- Test with real AgentCore services, not mocked data
- Document actual response structures in code

## Incremental Delivery Benefits

This restructured plan delivers value incrementally:

- **Week 1:** Users can browse and discover agents
- **Week 2:** Users can view agent details and chat with any agent
- **Week 3:** Users see real-time observability in chat
- **Week 4:** Users can visualize agent memories
- **Weeks 5-6:** Users access comprehensive observability dashboard
- **Week 7:** Final polish and optimization

Each week delivers working functionality that can be tested and used immediately.

## Implementation Language

- Backend Lambdas: Python 3.13
- Frontend: TypeScript with React 18
- Infrastructure: AWS CDK with TypeScript

## Estimated Timeline

- Phase 1: Agent Gallery (Week 1)
- Phase 2: Agent Details & Chat Enhancement (Week 2)
- Phase 3: Inline Chat Observability (Week 3)
- Phase 4: Memory Visualization (Week 4)
- Phase 5: Observability Dashboard (Weeks 5-6)
- Phase 6: Polish & Optimization (Week 7)

**Total: 7 weeks**

## Dependencies

- AWS SDK for Python (boto3)
- AWS Lambda Powertools for Python
- React 18 with TypeScript
- shadcn/ui component library
- Tailwind CSS 4
- Lucide React icons
- React Router
- react-syntax-highlighter
- recharts
- fast-check (property testing)
- Hypothesis (property testing)
- Vitest (unit testing)
- pytest (unit testing)
- React Testing Library
- Playwright (E2E testing)

## Critical Reminders

1. **VALIDATION FIRST:** Complete all validation sub-tasks before writing Lambda code
2. **NO GUESSING:** Do NOT guess API response schemas - validate with real AgentCore services
3. **TEST WITH REAL DATA:** Use real AgentCore APIs, not mocked data
4. **DOCUMENT SCHEMAS:** Document actual response structures in code comments
5. **GATEWAY CLARIFICATION:** Gateway is for tools, NOT agent discovery
6. **RUNTIME IS AGENT GATEWAY:** Use Runtime API for agent listing and invocation
7. **MEMORY STRATEGIES:** Each memory strategy has different response schema
8. **OBSERVABILITY SOURCE:** Validate whether to use Runtime API or CloudWatch Logs for traces
9. **INCREMENTAL DELIVERY:** Each phase delivers working functionality - test and validate before moving to next phase
10. **USER FEEDBACK:** Checkpoints allow for user feedback and course correction

