# Requirements Document

## Introduction

The FAST Agent Gallery observability dashboard currently queries CloudWatch Logs directly via the FilterLogEvents API to display session data (traces, spans, metrics) for AI agents. This approach times out when querying 7+ days of data due to Lambda's 30-second timeout limit and CloudWatch Logs' query performance characteristics.

This feature explores architectural trade-offs between five approaches:
1. Increase Lambda timeout (quick fix, may not scale)
2. Persist data in DynamoDB or S3 (own the data, faster queries)
3. Persist links to CloudWatch log groups and pull data on demand
4. Show summary view in FAST and redirect to CloudWatch for deep dives (with proper deep links)
5. Hybrid: cache recent data, redirect to CloudWatch for historical

The solution must respect the design principle that FAST Agent Gallery is owned by AI engineers for their 5-10 agents (user-friendly, focused), while centralized platform teams use CloudWatch for production-grade observability across all company AI agents (comprehensive, system of record).

### Multi-Pattern Support Philosophy

Different teams have different observability needs and constraints. Rather than forcing a single approach, the solution may support multiple configurable observability patterns:

- **Small AI teams with lightweight prototypes** might get by with Approach 1 (increased Lambda timeout)
- **Power users** might persist links only (Approach 3) and learn to love CloudWatch
- **High-volume teams** might need DynamoDB or S3 persistence (Approach 2)
- **Balanced teams** might prefer the hybrid approach (Approach 5)

This repository already supports multiple patterns for agents (type, number, etc.) using a config file to specify the selected pattern for any deployment. The observability solution should follow the same approach with different configurable observability patterns.

The design phase will investigate which patterns are worth supporting, how to make them configurable, and which pattern to implement first.

## Glossary

- **FAST_Agent_Gallery**: The user-facing web application where AI engineers manage and observe their agents
- **Observability_Dashboard**: The section of FAST Agent Gallery showing sessions, traces, spans, and metrics
- **CloudWatch_Logs**: AWS service that stores OTEL span data in the aws/spans log group (system of record)
- **Session**: A single invocation of an agent, composed of multiple spans representing operations
- **Span**: An OTEL (OpenTelemetry) trace span representing a single operation with timing and metadata
- **FilterLogEvents_API**: CloudWatch Logs API for querying log events with time ranges and filter patterns
- **Lambda_Handler**: The observability-sessions Lambda function that queries CloudWatch and returns session data
- **Time_Range**: The duration of historical data to query (e.g., 24 hours, 7 days, 30 days)
- **Deep_Link**: A URL that navigates directly to specific data in CloudWatch (log group, time range, filters)
- **AI_Engineer**: The primary user who owns 5-10 specific agents and uses FAST for daily work
- **Platform_Team**: Centralized team responsible for production observability across all company agents
- **Query_Timeout**: The 30-second Lambda execution limit that causes failures on large time ranges
- **Data_Volume**: The amount of span data stored in CloudWatch (grows with agent usage and retention)
- **Session_Summary**: Aggregated view of a session (start time, duration, status, trace count, agent name)
- **Session_Detail**: Full trace and span data for a single session (all operations, timing, errors)

## Requirements

### Requirement 1: Query Performance for Common Time Ranges

**User Story:** As an AI engineer, I want to view sessions from the last 24 hours instantly, so that I can quickly check recent agent activity without waiting.

#### Acceptance Criteria

1. WHEN an AI_Engineer requests sessions for the last 24 hours, THE Lambda_Handler SHALL return results within 5 seconds
2. WHEN an AI_Engineer requests sessions for the last 7 days, THE Lambda_Handler SHALL return results within 10 seconds
3. WHEN an AI_Engineer requests sessions for the last 30 days, THE Lambda_Handler SHALL return results or a pagination token within 15 seconds
4. IF the query exceeds the Lambda timeout, THEN THE Lambda_Handler SHALL return a descriptive error message indicating the time range is too large
5. THE Observability_Dashboard SHALL display a loading indicator while queries are in progress

### Requirement 2: Scalability with Data Volume Growth

**User Story:** As a platform team member, I want the observability solution to scale as agent usage grows, so that performance doesn't degrade over time.

#### Acceptance Criteria

1. WHEN Data_Volume increases by 10x, THE Lambda_Handler SHALL maintain query performance within 2x of baseline response times
2. WHEN an agent generates 1000+ spans per day, THE Lambda_Handler SHALL successfully query and aggregate session data
3. THE system SHALL support querying data for at least 5 agents simultaneously without performance degradation
4. IF Data_Volume exceeds query performance thresholds, THEN THE system SHALL provide alternative access methods (pagination, filtering, or CloudWatch redirection)

### Requirement 3: Data Ownership and Consistency

**User Story:** As an AI engineer, I want observability data to be consistent with CloudWatch, so that I can trust the metrics and traces I see in FAST.

#### Acceptance Criteria

1. THE CloudWatch_Logs SHALL remain the system of record for all span data
2. IF the system persists data locally (DynamoDB/S3), THEN THE system SHALL synchronize with CloudWatch_Logs within 5 minutes of span creation
3. WHEN displaying session data, THE Observability_Dashboard SHALL indicate the data freshness (e.g., "Last updated 2 minutes ago")
4. IF local data diverges from CloudWatch_Logs, THEN THE system SHALL provide a mechanism to refresh from the source of truth
5. THE system SHALL NOT delete or modify span data in CloudWatch_Logs

### Requirement 4: CloudWatch Integration and Deep Linking

**User Story:** As an AI engineer, I want to navigate from FAST to CloudWatch for detailed analysis, so that I can use CloudWatch's advanced features when needed.

#### Acceptance Criteria

1. WHEN an AI_Engineer clicks on a session in the Observability_Dashboard, THE system SHALL provide a link to view the session in CloudWatch
2. THE Deep_Link SHALL navigate to the correct log group (aws/spans) with the session's time range pre-filtered
3. THE Deep_Link SHALL include filter patterns that isolate the specific session's spans
4. WHEN an AI_Engineer views a specific agent's sessions, THE system SHALL provide a link to view all logs for that agent in CloudWatch
5. THE Deep_Link SHALL open in a new browser tab to preserve the FAST context

### Requirement 5: User Experience for Different Time Ranges

**User Story:** As an AI engineer, I want clear guidance on which tool to use for different time ranges, so that I can efficiently access the data I need.

#### Acceptance Criteria

1. WHEN an AI_Engineer selects a time range longer than 7 days, THE Observability_Dashboard SHALL display a message suggesting CloudWatch for historical analysis
2. THE Observability_Dashboard SHALL provide a "View in CloudWatch" button with a properly configured Deep_Link
3. WHEN displaying Session_Summary data, THE Observability_Dashboard SHALL show key metrics (count, duration, status) without requiring full span details
4. IF the Lambda_Handler times out, THEN THE Observability_Dashboard SHALL display the CloudWatch Deep_Link as a fallback option
5. THE system SHALL remember the user's preferred time range across sessions

### Requirement 6: Cost Optimization

**User Story:** As a platform team member, I want to minimize AWS costs for observability queries, so that the solution is economically sustainable.

#### Acceptance Criteria

1. THE system SHALL minimize redundant queries to CloudWatch_Logs by caching results where appropriate
2. IF the system persists data locally, THEN THE system SHALL use cost-effective storage (S3 for archives, DynamoDB for recent data)
3. THE Lambda_Handler SHALL use pagination to avoid querying more data than necessary
4. WHEN an AI_Engineer refreshes the dashboard, THE system SHALL reuse cached data if less than 1 minute old
5. THE system SHALL provide metrics on CloudWatch Logs query costs for monitoring

### Requirement 7: Session Detail Access

**User Story:** As an AI engineer, I want to view detailed traces and spans for a specific session, so that I can debug issues and understand agent behavior.

#### Acceptance Criteria

1. WHEN an AI_Engineer clicks on a session, THE Observability_Dashboard SHALL display Session_Detail including all spans
2. THE Session_Detail SHALL show span hierarchy (parent-child relationships) and timing information
3. IF Session_Detail data is not cached locally, THEN THE Lambda_Handler SHALL query CloudWatch_Logs for the specific session
4. THE Lambda_Handler SHALL use session ID filtering to minimize data transfer when fetching Session_Detail
5. WHEN Session_Detail exceeds 100 spans, THE Observability_Dashboard SHALL paginate or provide a "View in CloudWatch" option

### Requirement 8: Data Retention Alignment

**User Story:** As a platform team member, I want FAST's data retention to align with CloudWatch retention policies, so that users don't see inconsistent data availability.

#### Acceptance Criteria

1. THE system SHALL document the CloudWatch_Logs retention period (currently 1 week for aws/spans)
2. IF the system persists data locally, THEN THE system SHALL apply the same retention period as CloudWatch_Logs
3. WHEN an AI_Engineer queries data older than the retention period, THE system SHALL display a message indicating data is no longer available
4. THE Observability_Dashboard SHALL display the retention period in the UI
5. IF CloudWatch retention changes, THEN THE system SHALL update local retention policies accordingly

### Requirement 9: Incremental Data Loading

**User Story:** As an AI engineer, I want to see initial results quickly while more data loads in the background, so that I don't have to wait for complete queries.

#### Acceptance Criteria

1. WHEN an AI_Engineer requests a large time range, THE Lambda_Handler SHALL return the first page of results within 5 seconds
2. THE Observability_Dashboard SHALL display initial results immediately and indicate more data is loading
3. THE system SHALL support pagination tokens to fetch additional pages of session data
4. WHEN the user scrolls to the bottom of the session list, THE Observability_Dashboard SHALL automatically fetch the next page
5. THE system SHALL allow users to cancel long-running queries

### Requirement 10: Agent-Specific Filtering Performance

**User Story:** As an AI engineer, I want to filter sessions by agent name instantly, so that I can focus on my specific agents without delay.

#### Acceptance Criteria

1. WHEN an AI_Engineer changes the agent filter, THE Observability_Dashboard SHALL filter client-side from already-loaded data
2. THE Lambda_Handler SHALL NOT receive agent name as a query parameter (filtering happens client-side)
3. WHEN sessions are loaded, THE Observability_Dashboard SHALL extract unique agent names for the filter dropdown
4. THE agent filter SHALL update the displayed sessions within 100ms (instant client-side filtering)
5. THE system SHALL preserve the selected agent filter when the user refreshes the page

### Requirement 11: Hybrid Approach Evaluation

**User Story:** As a platform team member, I want to evaluate a hybrid approach (cache recent + redirect historical), so that we can balance performance and cost.

#### Acceptance Criteria

1. THE system SHALL define a "recent data" threshold (e.g., last 24 hours) for local caching
2. WHEN an AI_Engineer queries recent data, THE Lambda_Handler SHALL serve from local cache if available
3. WHEN an AI_Engineer queries historical data beyond the threshold, THE system SHALL provide CloudWatch Deep_Links
4. THE system SHALL automatically populate the cache with new span data as it arrives in CloudWatch_Logs
5. THE system SHALL document the trade-offs between cache size, freshness, and query performance

### Requirement 12: Error Handling and Fallback

**User Story:** As an AI engineer, I want clear error messages and fallback options when queries fail, so that I can still access my data through alternative means.

#### Acceptance Criteria

1. WHEN the Lambda_Handler times out, THE Observability_Dashboard SHALL display an error message with the specific time range that failed
2. THE error message SHALL include a "View in CloudWatch" button with a properly configured Deep_Link
3. WHEN CloudWatch_Logs is unavailable, THE system SHALL display a message indicating the service is temporarily unavailable
4. IF local cache exists, THEN THE system SHALL serve cached data with a staleness warning
5. THE system SHALL log all query failures with sufficient context for debugging (time range, agent filter, error type)

### Requirement 13: Multi-Pattern Support and Configurability

**User Story:** As a platform team member, I want to configure which observability pattern to use for my deployment, so that I can choose the approach that best fits my team's needs and constraints.

#### Acceptance Criteria

1. THE system SHALL support configuration of the observability pattern via a deployment config file
2. THE system SHALL document the trade-offs, costs, and use cases for each supported pattern
3. WHEN a deployment is configured with a specific pattern, THE Lambda_Handler SHALL implement the query strategy for that pattern
4. THE system SHALL validate the configuration at deployment time and fail with clear error messages if invalid
5. WHERE a pattern requires additional infrastructure (DynamoDB, S3), THE system SHALL provision it automatically based on the configuration
6. THE system SHALL support at least one pattern in the initial implementation, with architecture designed to add more patterns later
7. THE configuration format SHALL follow the existing pattern used for agent configuration in this repository

## Architecture Trade-offs Summary

This requirements document captures the needs for five potential approaches. The solution may support multiple patterns as configurable options rather than selecting a single approach:

**Approach 1: Increase Lambda Timeout**
- Pros: Simple, no architecture changes
- Cons: Doesn't scale, costs increase, may still timeout on 30+ days
- Requirements addressed: 1, 12
- Best for: Small teams with lightweight prototypes and low query volumes

**Approach 2: Persist in DynamoDB/S3**
- Pros: Fast queries, full control, supports complex filtering
- Cons: Duplication, sync complexity, storage costs, eventual consistency
- Requirements addressed: 1, 2, 3, 6, 7, 8, 9, 10
- Best for: High-volume teams needing fast queries and complex filtering

**Approach 3: Persist Links Only**
- Pros: Minimal storage, always fresh, leverages CloudWatch
- Cons: Still queries CloudWatch, doesn't solve timeout
- Requirements addressed: 4, 5, 12
- Best for: Power users comfortable with CloudWatch who want quick navigation

**Approach 4: Summary + Deep Links**
- Pros: Fast summaries, leverages CloudWatch for details, clear separation
- Cons: Limited detail in FAST, requires good deep linking
- Requirements addressed: 1, 4, 5, 7, 12
- Best for: Teams that primarily need overview data with occasional deep dives

**Approach 5: Hybrid (Cache Recent + Redirect Historical)**
- Pros: Best of both worlds, optimizes for common case (recent data)
- Cons: More complex, requires cache invalidation strategy
- Requirements addressed: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
- Best for: Balanced teams wanting good performance for recent data without full persistence costs

The design phase will evaluate which patterns are worth supporting, define the configuration mechanism (following existing agent config patterns in this repo), document the trade-offs for each pattern, and recommend which pattern to implement first. The architecture should be designed to support adding additional patterns over time based on team needs.
