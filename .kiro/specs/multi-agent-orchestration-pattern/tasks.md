# Implementation Plan: Multi-Agent Orchestration Pattern

## Overview

This implementation plan refactors the current multi-agent deployment architecture from treating each agent as a separate pattern to a unified multi-agent orchestration pattern. The implementation consolidates all four agents (orchestrator + three specialists: colorado, umich, coder) into a single pattern directory at `patterns/strands-multi-agent-orchestrator/`, with shared resources, separate Dockerfiles per agent, and simplified configuration.

The implementation follows an incremental approach: create the new structure, implement shared utilities, implement agents, update infrastructure, update frontend, add tests, and finally migrate/cleanup the old structure.

## Tasks

- [x] 1. Create unified pattern directory structure
  - Create `patterns/strands-multi-agent-orchestrator/` directory
  - Create subdirectories: `agents/`, `tools/`, `tests/`
  - Create agent subdirectories: `agents/orchestrator/`, `agents/colorado/`, `agents/umich/`, `agents/coder/`
  - Create test subdirectories: `tests/unit/`, `tests/integration/`, `tests/property/`
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Create shared configuration files
  - [x] 2.1 Create shared requirements.txt
    - Consolidate dependencies from all existing agent implementations
    - Include: boto3, hypothesis (for property tests), pytest, and agent-specific libraries
    - Place at pattern root: `patterns/strands-multi-agent-orchestrator/requirements.txt`
    - _Requirements: 1.5_
  
  - [x] 2.2 Create agents.json manifest
    - Define all four agents with name, displayName, description, runtimeId, isDefault
    - Set orchestrator as default agent (isDefault: true)
    - Place at pattern root: `patterns/strands-multi-agent-orchestrator/agents.json`
    - _Requirements: 1.8, 4.1, 4.2_

- [x] 3. Create shared tools
  - [x] 3.1 Create code interpreter tool (tools/code_interpreter.py)
    - Implement execute_python_securely() function
    - Delegate to root tools/code_interpreter/ implementation
    - Accept code and session_id parameters
    - Return execution results or error information
    - _Requirements: 6.1, 6.2, 6.3, 6.7_
  
  - [x] 3.2 Create specialist invocation tools (tools/invoke_specialist.py)
    - Implement invoke_colorado(), invoke_umich(), invoke_coder() functions
    - Implement _invoke_specialist() internal helper function
    - Retrieve specialist runtime endpoints from SSM Parameter Store
    - Make direct calls to specialist AgentCore Runtime endpoints
    - Pass query, session_id, and actor_id to specialists
    - Return specialist responses as strings
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 5.7_
  
  - [x] 3.3 Create tools/__init__.py
    - Export execute_python_securely, invoke_colorado, invoke_umich, invoke_coder
    - _Requirements: 6.2_

- [x] 4. Implement agent code
  - [x] 4.1 Implement orchestrator agent (agents/orchestrator/orchestrator_agent.py)
    - Create OrchestratorAgent class with inline session prefixing: `session_id = f"orchestrator_{base_session_id}"`
    - Import authentication utilities from `patterns/utils/auth.py`
    - Import SSM utilities from `patterns/utils/ssm.py`
    - Implement handle_request() method
    - Import and register specialist invocation tools
    - Implement routing logic to call appropriate specialists
    - Include specialist responses in orchestrator response
    - Maintain same actor_id when calling specialists
    - _Requirements: 1.2, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_
  
  - [x] 4.2 Implement Colorado specialist agent (agents/colorado/colorado_agent.py)
    - Create SpecialistAgent class with inline session prefixing: `session_id = f"colorado_{base_session_id}"`
    - Import authentication utilities from `patterns/utils/auth.py`
    - Import SSM utilities from `patterns/utils/ssm.py`
    - Implement handle_request() method
    - Import and register code interpreter tool
    - Copy Colorado-specific logic from existing implementation
    - _Requirements: 1.2, 2.5, 2.6, 6.3_
  
  - [x] 4.3 Implement UMich specialist agent (agents/umich/umich_agent.py)
    - Create SpecialistAgent class with inline session prefixing: `session_id = f"umich_{base_session_id}"`
    - Import authentication utilities from `patterns/utils/auth.py`
    - Import SSM utilities from `patterns/utils/ssm.py`
    - Implement handle_request() method
    - Import and register code interpreter tool
    - Copy UMich-specific logic from existing implementation
    - _Requirements: 1.2, 2.5, 2.6, 6.3_
  
  - [x] 4.4 Implement Coder specialist agent (agents/coder/coder_agent.py)
    - Create SpecialistAgent class with inline session prefixing: `session_id = f"coder_{base_session_id}"`
    - Import authentication utilities from `patterns/utils/auth.py`
    - Import SSM utilities from `patterns/utils/ssm.py`
    - Implement handle_request() method
    - Import and register code interpreter tool
    - Copy Coder-specific logic from existing implementation
    - _Requirements: 1.2, 2.5, 2.6, 6.3_

- [x] 5. Create Dockerfiles for each agent
  - [x] 5.1 Create orchestrator Dockerfile (agents/orchestrator/Dockerfile)
    - Use public.ecr.aws/lambda/python:3.11 base image
    - Copy shared requirements.txt from pattern root and install dependencies
    - Copy pattern-specific tools/ directory
    - Copy shared utils/ from parent patterns directory: `COPY ../../utils /app/patterns/utils`
    - Copy orchestrator_agent.py
    - Set CMD to orchestrator_agent.handler
    - Use multi-stage build for optimization
    - _Requirements: 1.2, 11.1, 11.2, 11.3_
  
  - [x] 5.2 Create Colorado Dockerfile (agents/colorado/Dockerfile)
    - Use public.ecr.aws/lambda/python:3.11 base image
    - Copy shared requirements.txt from pattern root and install dependencies
    - Copy pattern-specific tools/ directory
    - Copy shared utils/ from parent patterns directory: `COPY ../../utils /app/patterns/utils`
    - Copy colorado_agent.py
    - Set CMD to colorado_agent.handler
    - Use multi-stage build for optimization
    - _Requirements: 1.2, 11.1, 11.2, 11.3_
  
  - [x] 5.3 Create UMich Dockerfile (agents/umich/Dockerfile)
    - Use public.ecr.aws/lambda/python:3.11 base image
    - Copy shared requirements.txt from pattern root and install dependencies
    - Copy pattern-specific tools/ directory
    - Copy shared utils/ from parent patterns directory: `COPY ../../utils /app/patterns/utils`
    - Copy umich_agent.py
    - Set CMD to umich_agent.handler
    - Use multi-stage build for optimization
    - _Requirements: 1.2, 11.1, 11.2, 11.3_
  
  - [x] 5.4 Create Coder Dockerfile (agents/coder/Dockerfile)
    - Use public.ecr.aws/lambda/python:3.11 base image
    - Copy shared requirements.txt from pattern root and install dependencies
    - Copy pattern-specific tools/ directory
    - Copy shared utils/ from parent patterns directory: `COPY ../../utils /app/patterns/utils`
    - Copy coder_agent.py
    - Set CMD to coder_agent.handler
    - Use multi-stage build for optimization
    - _Requirements: 1.2, 11.1, 11.2, 11.3_

- [x] 6. Checkpoint - Verify pattern structure
  - Ensure all files are created in correct locations
  - Verify imports work correctly from `patterns/utils/` (sys.path.append('/app'))
  - Verify no pattern-specific utils directory exists
  - Ensure all tests pass, ask the user if questions arise

- [x] 7. Update CDK stack for multi-agent deployment
  - [x] 7.1 Update Config_Manager to support single pattern mode
    - Ensure config.yaml can specify `pattern: strands-multi-agent-orchestrator`
    - Remove any multi-pattern configuration logic
    - Validate that Config_Manager reads pattern name correctly
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 8.1, 8.2_
  
  - [x] 7.2 Create CDK construct for multi-agent pattern deployment
    - Read agents.json manifest to discover agents
    - Create separate AgentCore Runtime instance for each agent
    - Build separate Docker image for each agent using agent-specific Dockerfile
    - Deploy shared backend resources once (Memory, Gateway, Code Interpreter, Cognito)
    - Store agent metadata in SSM Parameter Store
    - Create API Gateway routes to each runtime endpoint
    - Export agent endpoints in CloudFormation outputs
    - _Requirements: 1.6, 2.1, 2.2, 2.3, 2.4, 2.7, 4.3, 4.4, 10.4, 10.5, 11.4, 11.5_
  
  - [x] 7.3 Implement agent-specific Docker image building
    - Build each agent's Docker image from its Dockerfile
    - Tag images with agent name and version
    - Push images to ECR
    - Ensure only changed agents trigger rebuilds
    - _Requirements: 11.4, 11.5_
  
  - [x] 7.4 Implement deployment validation
    - Validate all required agent files exist before building
    - Verify backend resources are available before deploying agents
    - Fail deployment with descriptive error if any agent build fails
    - _Requirements: 11.6, 11.7, 11.8_

- [-] 8. Update frontend for agent selection
  - [x] 8.1 Create agent discovery API endpoint
    - Retrieve agent metadata from SSM Parameter Store
    - Return list of available agents with display names and descriptions
    - _Requirements: 4.3, 4.4_
  
  - [x] 8.2 Update UI to display agent selection interface
    - Fetch available agents from discovery API
    - Display agents with display names and descriptions
    - Allow user to select active agent
    - Default to orchestrator agent if none selected
    - _Requirements: 4.6, 9.1, 9.7_
  
  - [x] 8.3 Implement agent switching logic
    - Update active agent when user selects different agent
    - Route requests to selected agent's runtime endpoint
    - Display currently active agent in conversation interface
    - Maintain separate conversation histories per agent
    - Preserve conversation context when switching agents
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [ ] 8.4 Implement error handling for unavailable agents
    - Display error message when agent is unavailable
    - Allow selecting different agent on error
    - _Requirements: 9.8_

- [x] 9. Checkpoint - Test end-to-end flow
  - Deploy to test environment
  - Verify all agents are accessible via UI
  - Test direct interaction with each specialist
  - Test orchestrator routing to specialists
  - Ensure all tests pass, ask the user if questions arise

- [ ] 10. Implement unit tests
  - [ ]* 10.1 Write unit tests for orchestrator agent (tests/unit/test_orchestrator_agent.py)
    - Test agent initialization with valid configuration
    - Test handle_request() with various query types
    - Test specialist invocation logic
    - Test inline session prefix application
    - Test error handling scenarios
    - _Requirements: 12.1_
  
  - [ ]* 10.2 Write unit tests for specialist agents (tests/unit/test_colorado_agent.py, test_umich_agent.py, test_coder_agent.py)
    - Test agent initialization for each specialist
    - Test handle_request() for each specialist
    - Test inline session prefix application (f"{agent_name}_{base_session_id}")
    - Test imports from `patterns/utils/auth.py` and `patterns/utils/ssm.py`
    - Test error handling scenarios
    - _Requirements: 12.1_
  
  - [ ]* 10.3 Write unit tests for shared tools (tests/unit/test_code_interpreter.py, test_invoke_specialist.py)
    - Test execute_python_securely() with valid code
    - Test execute_python_securely() with errors
    - Test invoke_specialist() functions
    - Test specialist endpoint retrieval from SSM
    - _Requirements: 12.3_

- [ ] 11. Implement integration tests
  - [ ]* 11.1 Write orchestrator-to-specialist integration tests (tests/integration/test_orchestrator_to_specialist.py)
    - Test complete flow from orchestrator to each specialist
    - Test specialist response inclusion in orchestrator response
    - Test actor_id consistency across invocations
    - Test session_id isolation per agent
    - _Requirements: 12.2, 12.7_
  
  - [ ]* 11.2 Write memory integration tests (tests/integration/test_memory_integration.py)
    - Test conversation turn storage and retrieval
    - Test separate session histories per agent
    - Test shared long-term memory across agents
    - Test concurrent memory access
    - _Requirements: 12.4, 12.5, 12.6_
  
  - [ ]* 11.3 Write gateway integration tests (tests/integration/test_gateway_integration.py)
    - Test tool invocation via AgentCore Gateway
    - Test authentication token inclusion
    - Test concurrent gateway access
    - _Requirements: 12.4_

- [ ] 12. Implement property-based tests
  - [ ]* 12.1 Write property test for session prefix isolation (tests/property/test_properties.py)
    - **Property 1: Session Prefix Isolation**
    - **Validates: Requirements 2.5**
    - Test that any agent with any session ID applies correct inline prefix: `f"{agent_name}_{base_session_id}"`
    - Use Hypothesis with 100 iterations
  
  - [ ]* 12.2 Write property test for actor ID consistency (tests/property/test_properties.py)
    - **Property 2: Actor ID Consistency**
    - **Validates: Requirements 2.6**
    - Test that same user has same actor_id across all agents
    - Use Hypothesis with 100 iterations
  
  - [ ]* 12.3 Write property test for agent manifest completeness (tests/property/test_properties.py)
    - **Property 4: Agent Manifest Completeness**
    - **Validates: Requirements 4.2**
    - Test that any agent entry has all required fields
    - Use Hypothesis with 100 iterations
  
  - [ ]* 12.4 Write property test for shared resource imports (tests/property/test_properties.py)
    - **Property 7: Shared Resource Import Consistency**
    - **Validates: Requirements 6.3, 6.6**
    - Test that agents import from `patterns/utils/` (not pattern-specific utils)
    - Verify no pattern-specific utils directory exists
    - Use Hypothesis with 100 iterations
  
  - [ ]* 12.5 Write property test for gateway authentication flow (tests/property/test_properties.py)
    - **Property 8: Gateway Authentication Flow**
    - **Validates: Requirements 7.1, 7.2, 7.3**
    - Test that gateway access includes JWT token in Authorization header
    - Use Hypothesis with 100 iterations
  
  - [ ]* 12.6 Write property test for Dockerfile dependency consistency (tests/property/test_properties.py)
    - **Property 10: Dockerfile Dependency Consistency**
    - **Validates: Requirements 11.2**
    - Test that all Dockerfiles reference shared requirements.txt from pattern root
    - Test that all Dockerfiles copy utils from parent patterns directory
    - Use Hypothesis with 100 iterations
  
  - [ ]* 12.7 Create test data generators (tests/property/generators.py)
    - Create Hypothesis strategies for agent names, session IDs, actor IDs
    - Create strategies for user messages, agent requests, agent metadata
    - _Requirements: 12.1, 12.2, 12.3_

- [ ] 13. Create documentation
  - [ ] 13.1 Create multi-agent orchestration documentation (docs/MULTI_AGENT_ORCHESTRATION.md)
    - Explain the pattern architecture and directory structure
    - Document how orchestrator routes queries to specialists
    - Explain how agents share backend resources
    - Document agent discovery mechanism
    - Include architecture diagrams
    - Provide examples of adding new specialist agents
    - Include troubleshooting guidance
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8_
  
  - [ ] 13.2 Create migration guide (docs/MIGRATION_MULTI_AGENT.md)
    - List all files to move or modify
    - Explain config.yaml updates
    - Provide migration checklist
    - Include verification steps
    - Document rollback instructions
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8_
  
  - [ ] 13.3 Update main README
    - Add reference to multi-agent orchestration pattern
    - Update deployment instructions for new pattern
    - _Requirements: 8.5, 13.1_

- [ ] 14. Checkpoint - Verify documentation and tests
  - Review all documentation for completeness and accuracy
  - Run full test suite (unit, integration, property tests)
  - Verify test coverage ≥ 80%
  - Ensure all tests pass, ask the user if questions arise

- [ ] 15. Migrate existing agent code to new structure
  - [ ] 15.1 Migrate orchestrator agent code
    - Copy relevant code from `agents/` directory to `agents/orchestrator/orchestrator_agent.py`
    - Update imports to use `patterns/utils/auth.py` and `patterns/utils/ssm.py`
    - Implement inline session prefixing: `session_id = f"orchestrator_{base_session_id}"`
    - Remove duplicate code that now exists in shared directories
    - _Requirements: 6.7, 14.8_
  
  - [ ] 15.2 Migrate Colorado agent code
    - Copy relevant code from `patterns/strands-colorado-agent/` to `agents/colorado/colorado_agent.py`
    - Update imports to use `patterns/utils/auth.py` and `patterns/utils/ssm.py`
    - Implement inline session prefixing: `session_id = f"colorado_{base_session_id}"`
    - Remove duplicate code that now exists in shared directories
    - _Requirements: 6.7, 14.8_
  
  - [ ] 15.3 Migrate UMich agent code
    - Copy relevant code from `patterns/strands-umich-agent/` to `agents/umich/umich_agent.py`
    - Update imports to use `patterns/utils/auth.py` and `patterns/utils/ssm.py`
    - Implement inline session prefixing: `session_id = f"umich_{base_session_id}"`
    - Remove duplicate code that now exists in shared directories
    - _Requirements: 6.7, 14.8_
  
  - [ ] 15.4 Migrate Coder agent code
    - Copy relevant code from `patterns/strands-coder-agent/` to `agents/coder/coder_agent.py`
    - Update imports to use `patterns/utils/auth.py` and `patterns/utils/ssm.py`
    - Implement inline session prefixing: `session_id = f"coder_{base_session_id}"`
    - Remove duplicate code that now exists in shared directories
    - _Requirements: 6.7, 14.8_

- [ ] 16. Update configuration and deploy
  - [ ] 16.1 Update config.yaml
    - Change pattern configuration to `pattern: strands-multi-agent-orchestrator`
    - Remove any multi-pattern configuration entries
    - _Requirements: 3.2, 3.5, 14.3_
  
  - [ ] 16.2 Deploy to test environment
    - Run CDK synthesis to validate stack
    - Deploy to test environment
    - Verify all four agents are deployed successfully
    - Verify backend resources are shared correctly
    - _Requirements: 1.6, 2.7, 11.7_
  
  - [ ] 16.3 Run acceptance tests
    - Test direct interaction with each specialist agent
    - Test orchestrator routing to specialists
    - Verify conversation history per agent
    - Verify switching between agents preserves context
    - Test error scenarios (agent unavailable, gateway down)
    - Verify authentication works correctly
    - Test code execution via code interpreter
    - Verify memory sharing across agents
    - _Requirements: 12.8_

- [ ] 17. Cleanup legacy structure
  - [ ] 17.1 Remove old pattern directories
    - Remove `patterns/strands-colorado-agent/` directory
    - Remove `patterns/strands-umich-agent/` directory
    - Remove `patterns/strands-coder-agent/` directory
    - _Requirements: 15.1, 15.2, 15.3_
  
  - [ ] 17.2 Clean up or repurpose agents/ directory
    - Remove or repurpose root `agents/` directory
    - Ensure no orphaned agent code remains
    - _Requirements: 15.4_
  
  - [ ] 17.3 Update CHANGELOG
    - Document structural changes and migration
    - Note breaking changes and migration path
    - _Requirements: 15.6_
  
  - [ ] 17.4 Final verification
    - Verify no functionality was lost in migration
    - Verify all tests still pass
    - Verify deployment works correctly
    - _Requirements: 15.7_

- [ ] 18. Final checkpoint - Complete verification
  - Run full test suite one final time
  - Verify deployment to test environment is stable
  - Confirm all requirements are met
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties with 100 iterations each
- Unit and integration tests validate specific examples and edge cases
- The implementation follows an incremental approach: structure → shared code → agents → infrastructure → frontend → tests → documentation → migration → cleanup
- Separate Dockerfiles per agent enable fast iteration - only changed agents need rebuilding
- All agents share backend resources (Memory, Gateway, Code Interpreter, Cognito) for efficiency
- Session prefixes are applied inline using string concatenation: `f"{agent_name}_{base_session_id}"`
- Actor ID consistency ensures shared long-term memory across agents for the same user
- Pattern leverages existing `patterns/utils/` for auth and SSM utilities (no pattern-specific utils)
- Pattern only contains: `agents/`, `tools/`, `tests/`, `requirements.txt`, `agents.json`
