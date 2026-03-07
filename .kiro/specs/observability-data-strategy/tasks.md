# Implementation Plan: Observability Data Strategy

## Overview

This implementation focuses on Pattern 4 (Summary + Links) as the recommended initial approach. This pattern solves the immediate timeout issue by querying CloudWatch for session summaries only (minimal span data) and providing deep links to CloudWatch for detailed analysis. The architecture is designed to support additional patterns (Extended Timeout, Hybrid Cache) in future phases.

## Tasks

- [ ] 1. Create configuration schema and validation
  - Add `observability` section to config.yaml schema
  - Define pattern types: `extended-timeout`, `summary-links`, `hybrid-cache`
  - Add pattern-specific configuration options (lambda_timeout_seconds, cache_ttl_hours, max_sessions_per_query, cloudwatch_retention_days)
  - Implement configuration validation in CDK stack
  - _Requirements: 13.1, 13.4, 13.7_

- [ ]* 1.1 Write unit tests for configuration validation
  - Test valid pattern configurations load correctly
  - Test invalid patterns fail with clear error messages
  - Test default pattern is applied when not specified
  - Test pattern-specific config options are validated
  - _Requirements: 13.4_

- [ ] 2. Implement pattern router and base architecture
  - [ ] 2.1 Create ObservabilityPattern abstract base class
    - Define abstract `query_sessions` method with standard interface
    - Define return type: sessions, count, nextToken, dataSource, cloudwatchLink
    - Add type hints for all parameters and return values
    - _Requirements: 13.3_

  - [ ]* 2.2 Write property test for pattern router
    - **Property 15: Pattern Configuration Routing**
    - **Validates: Requirements 13.1, 13.3, 13.5**
    - Test that each valid pattern instantiates correct class
    - Test that pattern-specific query logic executes
    - Test that all patterns return consistent interface
    - _Requirements: 13.1, 13.3, 13.5_

  - [ ] 2.3 Implement pattern factory function
    - Create `get_pattern(pattern_name: str)` factory function
    - Map pattern names to implementation classes
    - Raise clear error for unknown patterns
    - _Requirements: 13.3_

  - [ ] 2.4 Update Lambda handler with pattern routing
    - Read OBSERVABILITY_PATTERN from environment variable
    - Instantiate pattern using factory function
    - Extract query parameters from API Gateway event
    - Call pattern.query_sessions() with parameters
    - Return standardized response with CORS headers
    - _Requirements: 13.3_

- [ ] 3. Implement CloudWatch deep link generator
  - [ ] 3.1 Create deep link generation module
    - Implement `generate_cloudwatch_deep_link()` function
    - Support parameters: region, log_group, start_time_ms, end_time_ms, filter_pattern, session_id
    - Build CloudWatch Logs Insights query with proper filters
    - Construct CloudWatch console URL with encoded parameters
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 3.2 Write property test for deep link correctness
    - **Property 5: Deep Link Correctness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    - Test that links point to aws/spans log group
    - Test that links include session time range
    - Test that links include session ID filter
    - Test that links are valid HTTPS URLs
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 3.3 Write unit tests for deep link edge cases
    - Test with special characters in session IDs
    - Test with very long time ranges
    - Test with missing optional parameters
    - Test URL encoding correctness
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement SummaryLinksPattern (Pattern 4)
  - [ ] 5.1 Create SummaryLinksPattern class
    - Inherit from ObservabilityPattern base class
    - Implement query_sessions method
    - Query CloudWatch with FilterLogEvents API
    - Apply time range filters to reduce scan scope
    - Limit query to 10,000 events (CloudWatch max)
    - _Requirements: 1.1, 1.2, 5.3_

  - [ ] 5.2 Implement session aggregation logic
    - Parse minimal fields from OTEL spans (sessionId, timestamp, errorType)
    - Group spans by session.id in memory
    - Calculate session metrics: startTime, endTime, duration, status, spanCount
    - Extract agent name from session ID
    - Sort sessions by startTime (newest first)
    - _Requirements: 5.3, 6.1, 10.3_

  - [ ]* 5.3 Write property test for session summary completeness
    - **Property 6: Session Summary Completeness**
    - **Validates: Requirements 5.3, 10.3**
    - Test that all key metrics are present (sessionId, agentName, startTime, endTime, duration, status, spanCount)
    - Test that summaries don't require full span details
    - _Requirements: 5.3, 10.3_

  - [ ] 5.4 Implement pagination support
    - Return nextToken when results exceed limit
    - Support nextToken parameter for fetching next page
    - Ensure no duplicates or gaps in paginated results
    - _Requirements: 6.3, 9.3_

  - [ ]* 5.5 Write property test for pagination consistency
    - **Property 8: Pagination Consistency**
    - **Validates: Requirements 6.3, 9.3**
    - Test that fetching all pages returns all sessions exactly once
    - Test that sort order is maintained across pages
    - Test that no duplicates or gaps exist
    - _Requirements: 6.3, 9.3_

  - [ ] 5.6 Add CloudWatch deep link to response
    - Generate deep link for the queried time range
    - Include link in response under cloudwatchLink field
    - Set dataSource field to "cloudwatch"
    - _Requirements: 4.1, 5.2_

- [ ] 6. Implement error handling and timeout management
  - [ ] 6.1 Add timeout detection and handling
    - Catch Lambda timeout exceptions
    - Return partial results with nextToken if available
    - Include CloudWatch deep link in timeout responses
    - Add descriptive error message with time range details
    - _Requirements: 1.4, 12.1, 12.2_

  - [ ]* 6.2 Write property test for error handling with fallback links
    - **Property 12: Error Handling with Fallback Links**
    - **Validates: Requirements 1.4, 5.4, 12.1, 12.2**
    - Test that timeout errors include descriptive messages
    - Test that timeout errors include CloudWatch deep links
    - Test that error responses include time range that failed
    - _Requirements: 1.4, 5.4, 12.1, 12.2_

  - [ ] 6.3 Implement CloudWatch service error handling
    - Catch CloudWatch API errors (throttling, unavailable)
    - Return HTTP 503 with retry-after header
    - Log errors with sufficient context for debugging
    - _Requirements: 12.3, 12.5_

  - [ ]* 6.4 Write unit tests for error scenarios
    - Test CloudWatch throttling errors
    - Test CloudWatch service unavailable
    - Test invalid time range parameters
    - Test missing required parameters
    - _Requirements: 12.3, 12.5_

  - [ ] 6.5 Add query failure logging
    - Log all query failures with context (time range, agent filter, error type, pattern)
    - Include request ID for tracing
    - Use structured logging for CloudWatch Logs Insights queries
    - _Requirements: 12.5_

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Update CDK stack for observability configuration
  - [ ] 8.1 Add observability config to CDK stack
    - Read observability section from config.yaml
    - Set OBSERVABILITY_PATTERN environment variable on Lambda
    - Apply default pattern (summary-links) if not specified
    - Validate pattern configuration at deployment time
    - _Requirements: 13.1, 13.4_

  - [ ] 8.2 Configure Lambda timeout based on pattern
    - For summary-links pattern: use default 30 seconds
    - For extended-timeout pattern: use configured timeout (default 60s, max 900s)
    - Add timeout configuration to Lambda function definition
    - _Requirements: 13.5_

  - [ ] 8.3 Add IAM permissions for CloudWatch Logs
    - Grant logs:FilterLogEvents permission to Lambda role
    - Scope permission to aws/spans log group
    - Add permission for logs:DescribeLogGroups (for validation)
    - _Requirements: 1.1, 1.2_

  - [ ]* 8.4 Write unit tests for CDK stack configuration
    - Test that observability config is read correctly
    - Test that environment variables are set
    - Test that IAM permissions are granted
    - Test that invalid config fails deployment
    - _Requirements: 13.4_

- [ ] 9. Update frontend to display CloudWatch links
  - [ ] 9.1 Update SessionsResponse TypeScript interface
    - Add cloudwatchLink optional field
    - Add dataSource field ("cloudwatch" | "cache" | "hybrid")
    - Add cacheAge optional field for future hybrid pattern
    - _Requirements: 4.1, 5.2_

  - [ ] 9.2 Add "View in CloudWatch" button to UI
    - Display button when cloudwatchLink is present in response
    - Open link in new tab to preserve FAST context
    - Position button prominently in session list header
    - _Requirements: 4.5, 5.2_

  - [ ] 9.3 Display CloudWatch link on timeout errors
    - Show error message with time range that failed
    - Display "View in CloudWatch" button as fallback option
    - Include suggestions for reducing time range
    - _Requirements: 5.4, 12.1, 12.2_

  - [ ] 9.4 Add loading indicator for queries
    - Display spinner while query is in progress
    - Show estimated time remaining for long queries
    - Allow users to cancel long-running queries
    - _Requirements: 1.5, 9.2_

- [ ] 10. Add performance monitoring and cost tracking
  - [ ] 10.1 Implement CloudWatch metrics emission
    - Emit query duration metric (milliseconds)
    - Emit query result count metric
    - Emit query timeout metric (boolean)
    - Emit pattern type dimension for all metrics
    - _Requirements: 6.5_

  - [ ]* 10.2 Write property test for cost monitoring
    - **Property 9: Cost Monitoring**
    - **Validates: Requirements 6.5**
    - Test that all CloudWatch queries emit cost tracking metrics
    - Test that metrics include pattern type dimension
    - _Requirements: 6.5_

  - [ ] 10.3 Add query performance logging
    - Log query start time, end time, duration
    - Log time range queried (start, end, duration in days)
    - Log result count and pagination status
    - Log pattern type used
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Create documentation and deployment guide
  - [ ] 12.1 Document configuration options
    - Document observability.pattern options and trade-offs
    - Document pattern-specific configuration parameters
    - Provide configuration examples for each pattern
    - Document default values and limits
    - _Requirements: 13.2_

  - [ ] 12.2 Create migration guide
    - Document migration path for existing deployments
    - Explain default behavior (summary-links pattern)
    - Provide rollback strategy
    - Document breaking changes (none expected)
    - _Requirements: 13.2_

  - [ ] 12.3 Add README section for observability patterns
    - Explain pattern comparison matrix
    - Document when to use each pattern
    - Provide deployment instructions
    - Link to CloudWatch deep linking documentation
    - _Requirements: 13.2_

  - [ ] 12.4 Document CloudWatch retention alignment
    - Document current CloudWatch retention period (7 days)
    - Explain how retention affects query results
    - Document UI messaging for expired data
    - _Requirements: 8.1, 8.4_

- [ ] 13. Final integration and deployment
  - [ ] 13.1 Deploy to development environment
    - Deploy CDK stack with summary-links pattern
    - Verify Lambda function deploys successfully
    - Verify environment variables are set correctly
    - Test API endpoint with various time ranges
    - _Requirements: 13.1, 13.3_

  - [ ] 13.2 Verify end-to-end functionality
    - Test 24-hour query performance (should be <5s)
    - Test 7-day query performance (should be <10s)
    - Test CloudWatch deep links open correctly
    - Test pagination with large result sets
    - Test error handling with invalid parameters
    - _Requirements: 1.1, 1.2, 4.1, 6.3, 9.3_

  - [ ]* 13.3 Run property-based tests with 100 iterations
    - Run all property tests with minimum 100 examples
    - Verify all properties pass consistently
    - Document any edge cases discovered
    - _Requirements: All property tests_

  - [ ] 13.4 Performance validation
    - Measure p50 and p95 response times for 24h, 7d, 30d queries
    - Verify SLAs are met (24h: <5s, 7d: <10s, 30d: <15s or pagination)
    - Test with 10x data volume to verify scalability
    - Test with 5 concurrent agents to verify no degradation
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.3_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Pattern 4 (Summary + Links) is the recommended initial implementation (1-2 weeks)
- Architecture is designed to support Pattern 1 (Extended Timeout) and Pattern 5 (Hybrid Cache) in future phases
- All property tests must use Hypothesis with minimum 100 iterations
- Each property test must reference its design document property with tag format: `# Feature: observability-data-strategy, Property N: Title`
- CloudWatch remains the system of record for all patterns
- Default configuration maintains backward compatibility with improved timeout handling
