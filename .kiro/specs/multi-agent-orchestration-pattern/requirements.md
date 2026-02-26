# Requirements Document

## Introduction

This specification defines the requirements for refactoring the current multi-agent deployment architecture from treating each agent as a separate pattern to a unified multi-agent orchestration pattern. The current implementation incorrectly uses the `patterns/` directory to hold individual agents, when it should represent different architectural approaches. This refactoring will consolidate all four agents (orchestrator + three specialists: colorado, umich, coder) into a single pattern that properly represents a multi-agent orchestration architecture.

The refactoring will maintain backward compatibility where possible, follow existing repository conventions, ensure efficient resource sharing, and enable future extensibility for exposing agents to other frontends (Amazon Connect, workflows, etc.).

## Glossary

- **Pattern**: An architectural approach for deploying agents (e.g., single Strands agent, single LangGraph agent, multi-agent orchestration)
- **Specialist_Agent**: A domain-specific agent (colorado, umich, or coder) that handles specific types of queries
- **Orchestrator_Agent**: The main agent that routes user queries to appropriate Specialist_Agents
- **AgentCore_Memory**: AWS Bedrock AgentCore service for storing conversation history and long-term memory
- **AgentCore_Gateway**: AWS Bedrock AgentCore service providing tool access via MCP protocol
- **AgentCore_Runtime**: AWS Bedrock AgentCore service that hosts and executes agent code
- **Code_Interpreter**: AWS Bedrock AgentCore service for secure Python code execution
- **Multi_Agent_Pattern**: The unified pattern directory containing all agents in the orchestration system
- **Backend_Resources**: Shared AWS resources including AgentCore_Memory, AgentCore_Gateway, Code_Interpreter, and Cognito
- **CDK_Stack**: AWS Cloud Development Kit infrastructure-as-code stack
- **Session_Manager**: Component managing conversation history and memory integration
- **Tool**: A function or service that agents can invoke to perform specific tasks
- **MCP**: Model Context Protocol for tool discovery and execution
- **JWT_Token**: JSON Web Token used for authentication with Backend_Resources
- **SSM_Parameter**: AWS Systems Manager Parameter Store for configuration storage
- **Actor_ID**: User identifier in AgentCore_Memory (extracted from JWT_Token)
- **Session_ID**: Unique identifier for a conversation session
- **Config_Manager**: TypeScript utility managing deployment configuration from config.yaml

## Requirements

### Requirement 1: Unified Pattern Directory Structure

**User Story:** As a developer, I want all agents in the multi-agent orchestration system to reside in a single pattern directory, so that the architecture correctly represents one orchestration pattern rather than multiple separate patterns.

#### Acceptance Criteria

1. THE Multi_Agent_Pattern SHALL be located at `patterns/strands-multi-agent-orchestrator/`
2. THE Multi_Agent_Pattern SHALL contain all four agent implementations in separate subdirectories: `agents/orchestrator/`, `agents/colorado/`, `agents/umich/`, and `agents/coder/`
3. THE Multi_Agent_Pattern SHALL include a shared `tools/` directory for pattern-specific tool implementations
4. THE Multi_Agent_Pattern SHALL NOT have its own `utils/` directory (agents use existing `patterns/utils/`)
5. THE Multi_Agent_Pattern SHALL include a single `requirements.txt` file listing all dependencies for all agents
6. WHEN the pattern is deployed, THE CDK_Stack SHALL deploy all four agents to AgentCore_Runtime
7. THE Multi_Agent_Pattern SHALL follow the same structural conventions as existing patterns in the repository
8. THE Multi_Agent_Pattern SHALL include an `agents.json` manifest file at the pattern root

### Requirement 2: Shared Backend Resources

**User Story:** As a system architect, I want all agents to share Backend_Resources efficiently, so that we minimize infrastructure costs and complexity while maintaining proper isolation.

#### Acceptance Criteria

1. THE Orchestrator_Agent SHALL use the same AgentCore_Memory instance as all Specialist_Agents
2. THE Orchestrator_Agent SHALL use the same AgentCore_Gateway instance as all Specialist_Agents
3. THE Orchestrator_Agent SHALL use the same Code_Interpreter instance as all Specialist_Agents
4. THE Orchestrator_Agent SHALL use the same Cognito user pool as all Specialist_Agents
5. WHEN an agent accesses AgentCore_Memory, THE Session_Manager SHALL use an agent-specific session prefix (e.g., "colorado_", "umich_", "coder_", "orchestrator_")
6. WHEN an agent accesses AgentCore_Memory, THE Session_Manager SHALL use the same Actor_ID for the same user across all agents
7. THE Backend_Resources SHALL be deployed once per CDK_Stack regardless of the number of agents
8. WHEN multiple agents access Backend_Resources concurrently, THE Backend_Resources SHALL handle requests independently without interference

### Requirement 3: Configuration Simplification

**User Story:** As a deployment engineer, I want the configuration to point to a single pattern that deploys all agents, so that the deployment process is simplified and follows the original repository design.

#### Acceptance Criteria

1. THE Config_Manager SHALL support a single pattern configuration in `infra-cdk/config.yaml`
2. THE configuration SHALL specify `pattern: strands-multi-agent-orchestrator` in the backend section
3. THE Config_Manager SHALL support only single pattern mode as per the original design
4. WHEN the CDK_Stack is deployed, THE Config_Manager SHALL read the pattern name and deploy all agents within that pattern
5. THE configuration SHALL NOT require listing individual agents separately
6. THE Multi_Agent_Pattern directory structure SHALL be self-describing for agent discovery

### Requirement 4: Agent Discovery Mechanism

**User Story:** As a frontend developer, I want the UI to dynamically discover available agents, so that users can select which agent to interact with without hardcoding agent names.

#### Acceptance Criteria

1. THE Multi_Agent_Pattern SHALL include an `agents.json` manifest file listing all available agents
2. THE agents.json manifest SHALL include for each agent: agent name, display name, description, and runtime endpoint identifier
3. THE CDK_Stack SHALL store agent metadata in SSM_Parameter store during deployment
4. THE frontend SHALL retrieve available agents from SSM_Parameter store or a discovery API endpoint
5. WHEN a new agent is added to the pattern, THE agents.json manifest SHALL be updated to include the new agent
6. THE UI SHALL display all discovered agents in a selection interface
7. WHEN a user selects an agent, THE UI SHALL route requests to the appropriate AgentCore_Runtime endpoint

### Requirement 5: Orchestrator-to-Specialist Communication

**User Story:** As an orchestrator agent, I want to call Specialist_Agents as tools, so that I can route user queries to the most appropriate specialist for handling.

#### Acceptance Criteria

1. THE Orchestrator_Agent SHALL have access to tools for invoking each Specialist_Agent
2. WHEN the Orchestrator_Agent invokes a Specialist_Agent tool, THE tool SHALL make a direct call to the Specialist_Agent's AgentCore_Runtime endpoint
3. THE Orchestrator_Agent SHALL pass the user's query and session context to the Specialist_Agent
4. THE Specialist_Agent SHALL return its response to the Orchestrator_Agent
5. THE Orchestrator_Agent SHALL include the Specialist_Agent's response in its own response to the user
6. THE Orchestrator_Agent SHALL maintain the same Actor_ID when calling Specialist_Agents
7. THE Orchestrator_Agent SHALL use agent-specific Session_IDs to maintain separate conversation histories
8. WHEN a Specialist_Agent is invoked by the Orchestrator_Agent, THE Specialist_Agent SHALL have access to the user's long-term memory via AgentCore_Memory

### Requirement 6: Code Deduplication and Shared Utilities

**User Story:** As a maintainer, I want to eliminate duplicate code across the codebase and leverage existing shared utilities, so that updates and bug fixes only need to be made in one place.

#### Acceptance Criteria

1. THE Multi_Agent_Pattern SHALL include a single implementation of `execute_python_securely` in the shared `tools/` directory
2. THE shared tools directory SHALL be located at `patterns/strands-multi-agent-orchestrator/tools/`
3. WHEN an agent needs to execute Python code, THE agent SHALL import the shared `execute_python_securely` implementation
4. THE Multi_Agent_Pattern SHALL NOT have its own `utils/` directory
5. THE agents SHALL import authentication and SSM utilities from the existing `patterns/utils/auth.py` and `patterns/utils/ssm.py`
6. WHEN an agent needs to authenticate with AgentCore_Gateway, THE agent SHALL use `get_gateway_access_token()` from `patterns/utils/auth.py`
7. WHEN an agent needs to retrieve SSM parameters, THE agent SHALL use `get_ssm_parameter()` from `patterns/utils/ssm.py`
8. THE Multi_Agent_Pattern SHALL NOT contain duplicate implementations of the same functionality across different agent files
9. THE repository root `tools/code_interpreter/` directory SHALL remain as the canonical implementation that pattern-specific wrappers delegate to
10. THE agents SHALL handle session prefixing directly in their code using simple string concatenation (no separate SessionManager class needed)

### Requirement 7: Authentication and Authorization

**User Story:** As a security engineer, I want proper Cognito token management for all agents accessing the gateway, so that access is properly authenticated and authorized.

#### Acceptance Criteria

1. WHEN an agent needs to access AgentCore_Gateway, THE agent SHALL retrieve a JWT_Token from Cognito
2. THE agent SHALL use the machine client credentials stored in SSM_Parameter store to obtain the JWT_Token
3. THE JWT_Token SHALL be included in the Authorization header when calling AgentCore_Gateway
4. THE AgentCore_Gateway SHALL validate the JWT_Token before allowing tool access
5. WHEN a JWT_Token expires, THE agent SHALL automatically retrieve a new token
6. THE shared utils SHALL provide a `get_gateway_access_token()` function for all agents to use
7. THE Cognito configuration SHALL support all agents accessing AgentCore_Gateway with the same machine client
8. IF token retrieval fails, THEN THE agent SHALL return a descriptive error message to the user

### Requirement 8: Backward Compatibility

**User Story:** As a repository maintainer, I want to maintain backward compatibility with existing single-pattern deployments, so that existing users are not disrupted by the refactoring.

#### Acceptance Criteria

1. THE Config_Manager SHALL continue to support the existing single pattern configuration format
2. WHEN a config.yaml specifies a single pattern (e.g., `pattern: strands-single-agent` or `pattern: langgraph-single-agent`), THE CDK_Stack SHALL deploy that pattern as before
3. THE existing pattern directories (`strands-single-agent`, `langgraph-single-agent`) SHALL remain functional
4. THE Config_Manager SHALL NOT break existing single-pattern deployments when updated
5. THE documentation SHALL clearly explain both single-pattern and multi-agent pattern deployment approaches
6. WHEN migrating from the current multi-pattern approach to the unified pattern, THE migration path SHALL be documented

### Requirement 9: Frontend Agent Selection

**User Story:** As an end user, I want to select which agent to interact with from the UI, so that I can choose the most appropriate agent for my needs.

#### Acceptance Criteria

1. THE UI SHALL display a list of available agents with their display names and descriptions
2. WHEN a user selects an agent, THE UI SHALL update the active agent for the current session
3. THE UI SHALL send requests to the selected agent's AgentCore_Runtime endpoint
4. THE UI SHALL display which agent is currently active in the conversation interface
5. WHEN a user switches agents, THE UI SHALL maintain separate conversation histories for each agent
6. THE UI SHALL allow switching between agents without losing conversation context
7. THE UI SHALL default to the Orchestrator_Agent if no agent is explicitly selected
8. WHEN an agent is unavailable, THE UI SHALL display an appropriate error message and allow selecting a different agent

### Requirement 10: Extensibility for Future Frontends

**User Story:** As a solutions architect, I want the multi-agent pattern to be extensible for exposing agents to other frontends, so that agents can be accessed via Amazon Connect, workflows, or other interfaces in the future.

#### Acceptance Criteria

1. THE Multi_Agent_Pattern SHALL NOT contain frontend-specific logic in agent implementations
2. THE agent implementations SHALL use standard AgentCore_Runtime interfaces for receiving requests and sending responses
3. THE agent metadata in SSM_Parameter store SHALL include all information needed for external systems to discover and invoke agents
4. THE CDK_Stack SHALL expose agent endpoints in CloudFormation outputs
5. THE agents SHALL accept requests in a standard format that can be constructed by any frontend
6. THE agents SHALL return responses in a standard format that can be consumed by any frontend
7. THE documentation SHALL include examples of how to invoke agents from different frontend types
8. WHEN a new frontend needs to access agents, THE Multi_Agent_Pattern SHALL NOT require modification

### Requirement 11: Deployment and Build Process

**User Story:** As a DevOps engineer, I want a streamlined build and deployment process for the multi-agent pattern, so that individual agents can be built and deployed independently for efficient iteration.

#### Acceptance Criteria

1. EACH agent subdirectory SHALL include its own Dockerfile (e.g., `agents/orchestrator/Dockerfile`, `agents/colorado/Dockerfile`)
2. THE Dockerfile for each agent SHALL install dependencies from the shared requirements.txt file at the pattern root
3. THE Dockerfile for each agent SHALL use multi-stage builds to optimize image size
4. THE CDK_Stack SHALL build separate Docker images for each agent
5. WHEN an agent is updated, THE CDK_Stack SHALL only rebuild and redeploy that specific agent's image
6. THE build process SHALL validate that all required agent files are present before building each agent
7. THE deployment process SHALL verify that all Backend_Resources are available before deploying agents
8. IF a build fails for one agent, THEN THE deployment SHALL fail with a descriptive error message indicating which agent failed

### Requirement 12: Testing and Validation

**User Story:** As a quality assurance engineer, I want comprehensive testing for the multi-agent pattern, so that I can verify all agents work correctly and interact properly.

#### Acceptance Criteria

1. THE repository SHALL include unit tests for each agent implementation
2. THE repository SHALL include integration tests for orchestrator-to-specialist communication
3. THE repository SHALL include tests for shared tools and utilities
4. THE tests SHALL verify that agents can access Backend_Resources correctly
5. THE tests SHALL verify that agents maintain separate session histories
6. THE tests SHALL verify that agents share long-term memory correctly
7. THE tests SHALL verify that the Orchestrator_Agent can successfully invoke Specialist_Agents
8. WHEN tests are run, THE test suite SHALL provide clear pass/fail results for each test case

### Requirement 13: Documentation Updates

**User Story:** As a developer using FAST, I want comprehensive documentation for the multi-agent pattern, so that I understand how to use, customize, and extend the multi-agent orchestration system.

#### Acceptance Criteria

1. THE repository SHALL include a `docs/MULTI_AGENT_ORCHESTRATION.md` document explaining the pattern
2. THE documentation SHALL explain the directory structure of the Multi_Agent_Pattern
3. THE documentation SHALL provide examples of adding a new Specialist_Agent
4. THE documentation SHALL explain how the Orchestrator_Agent routes queries to specialists
5. THE documentation SHALL explain how agents share Backend_Resources
6. THE documentation SHALL include diagrams showing the multi-agent architecture
7. THE documentation SHALL explain the agent discovery mechanism
8. THE documentation SHALL include troubleshooting guidance for common issues

### Requirement 14: Migration Path

**User Story:** As a repository maintainer, I want a clear migration path from the current implementation to the refactored implementation, so that the transition is smooth and well-documented.

#### Acceptance Criteria

1. THE repository SHALL include a migration guide document
2. THE migration guide SHALL list all files that need to be moved or modified
3. THE migration guide SHALL explain how to update config.yaml for the new pattern
4. THE migration guide SHALL explain how to clean up old pattern directories
5. THE migration guide SHALL include a checklist of migration steps
6. THE migration guide SHALL explain how to verify the migration was successful
7. THE migration guide SHALL include rollback instructions in case of issues
8. WHEN following the migration guide, THE system SHALL transition from the old structure to the new structure without data loss

### Requirement 15: Cleanup of Legacy Structure

**User Story:** As a repository maintainer, I want to remove the incorrectly structured agent pattern directories, so that the repository structure is clean and follows the correct architectural approach.

#### Acceptance Criteria

1. WHEN the migration is complete, THE `patterns/strands-colorado-agent/` directory SHALL be removed
2. WHEN the migration is complete, THE `patterns/strands-umich-agent/` directory SHALL be removed
3. WHEN the migration is complete, THE `patterns/strands-coder-agent/` directory SHALL be removed
4. WHEN the migration is complete, THE `agents/` directory SHALL be removed or repurposed
5. THE Multi_Agent_Pattern SHALL be the single source of truth for all multi-agent orchestration code
6. THE repository SHALL include a CHANGELOG entry documenting the structural changes
7. THE cleanup SHALL NOT remove any functionality, only reorganize the code structure
