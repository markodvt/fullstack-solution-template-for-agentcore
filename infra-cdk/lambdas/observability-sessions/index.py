"""
Observability Sessions API Lambda Function

This Lambda function retrieves session data from CloudWatch Logs by querying
OTEL spans emitted by AgentCore Runtime. Since AgentCore Runtime does not provide
a direct API to list sessions, we extract session information from the aws/spans
log group.

Data Source: CloudWatch Logs aws/spans log group (OTEL format)
Approach: Query spans using FilterLogEvents API, group by session.id attribute

Environment Variables:
    STACK_NAME_BASE: Base name of the CloudFormation stack
    CORS_ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins

Query Parameters:
    agentName: Filter sessions by agent name (optional)
    startTime: Start of time range in milliseconds since epoch (optional)
    endTime: End of time range in milliseconds since epoch (optional)
    limit: Maximum results per page (optional, default: 50, max: 100)
    nextToken: Pagination token (optional)

Returns:
    JSON response with list of session summaries
"""

import json
import logging
import os
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
logs_client = boto3.client("logs")
ssm_client = boto3.client("ssm")

# CloudWatch Logs configuration
SPANS_LOG_GROUP = "aws/spans"

# Cache for agent display names (to avoid repeated SSM calls)
_agent_display_name_cache: Dict[str, str] = {}


def get_agent_display_name(agent_name: str, stack_name: str) -> str:
    """
    Get agent display name from SSM Parameter Store.
    Uses caching to avoid repeated SSM calls.

    Args:
        agent_name: Agent name (e.g., "umich", "orchestrator")
        stack_name: Stack name base for SSM parameter path

    Returns:
        Display name if found, otherwise returns the agent name
    """
    # Check cache first
    cache_key = f"{stack_name}:{agent_name}"
    if cache_key in _agent_display_name_cache:
        return _agent_display_name_cache[cache_key]
    
    try:
        # Query SSM for display name
        param_name = f"/{stack_name}/agents/{agent_name}/display-name"
        response = ssm_client.get_parameter(Name=param_name)
        display_name = response["Parameter"]["Value"]
        
        # Cache the result
        _agent_display_name_cache[cache_key] = display_name
        logger.info(f"Mapped agent '{agent_name}' to display name '{display_name}'")
        
        return display_name
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "ParameterNotFound":
            logger.warning(f"Display name not found for agent '{agent_name}' in SSM")
        else:
            logger.error(f"Error fetching display name for '{agent_name}': {e}")
        
        # Cache the agent name itself as fallback
        _agent_display_name_cache[cache_key] = agent_name
        return agent_name
    except Exception as e:
        logger.error(f"Unexpected error fetching display name for '{agent_name}': {e}")
        _agent_display_name_cache[cache_key] = agent_name
        return agent_name


def extract_user_id_from_jwt(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract user ID from JWT token in the request context.

    Args:
        event: API Gateway event containing request details

    Returns:
        User ID string, or None if not found
    """
    try:
        # API Gateway puts Cognito claims in requestContext.authorizer.claims
        claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
        
        # Try common claim names
        user_id = claims.get("sub") or claims.get("cognito:username") or claims.get("username")
        
        if user_id:
            logger.info(f"Extracted user ID from JWT: {user_id}")
            return user_id
        
        logger.warning("Could not extract user ID from JWT claims")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting user ID from JWT: {e}")
        return None


def query_spans_from_cloudwatch(
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    filter_pattern: Optional[str] = None,
    next_token: Optional[str] = None,
    limit: int = 1000
) -> Dict[str, Any]:
    """
    Query OTEL spans from CloudWatch Logs aws/spans log group.

    Args:
        start_time: Start time in milliseconds since epoch (optional)
        end_time: End time in milliseconds since epoch (optional)
        filter_pattern: CloudWatch Logs filter pattern (optional)
        next_token: Pagination token (optional)
        limit: Maximum number of log events to return (max 10000)

    Returns:
        Dictionary containing log events and pagination info
    """
    try:
        params = {
            "logGroupName": SPANS_LOG_GROUP,
            "limit": min(limit, 10000)  # CloudWatch Logs max limit
        }
        
        # Add time range if provided
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        # Add filter pattern if provided
        if filter_pattern:
            params["filterPattern"] = filter_pattern
        
        # Add pagination token if provided
        if next_token:
            params["nextToken"] = next_token
        
        logger.info(f"Querying CloudWatch Logs with params: {params}")
        
        response = logs_client.filter_log_events(**params)
        
        logger.info(
            f"FilterLogEvents returned {len(response.get('events', []))} events"
        )
        
        return {
            "success": True,
            "events": response.get("events", []),
            "nextToken": response.get("nextToken")
        }
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        
        logger.error(f"FilterLogEvents failed: {error_code} - {error_message}")
        
        # Handle specific error cases
        if error_code == "ResourceNotFoundException":
            logger.warning(f"Log group {SPANS_LOG_GROUP} not found - no spans available yet")
            return {
                "success": True,
                "events": [],
                "nextToken": None
            }
        
        return {
            "success": False,
            "error": error_message,
            "events": []
        }
    except Exception as e:
        logger.error(f"Unexpected error querying CloudWatch Logs: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "events": []
        }


def parse_otel_span(log_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse OTEL span from CloudWatch Logs event.

    OTEL spans in CloudWatch Logs are JSON objects with the following structure:
    {
        "traceId": "...",
        "spanId": "...",
        "parentSpanId": "...",
        "name": "POST /invocations http receive",
        "startTime": "2024-01-01T00:00:00.000Z",
        "endTime": "2024-01-01T00:00:01.000Z",
        "resource": {
            "attributes": {
                "service.name": "stack_agent.endpoint",
                "cloud.resource_id": "arn:aws:bedrock-agentcore:...:runtime/stack_agent-ID/..."
            }
        },
        "attributes": {
            "session.id": "...",
            "error_type": "..."
        }
    }

    Args:
        log_event: CloudWatch Logs event containing OTEL span

    Returns:
        Parsed span dictionary, or None if parsing fails
    """
    try:
        # Parse JSON message
        message = log_event.get("message", "")
        if not message:
            return None
        
        span = json.loads(message)
        
        # Extract attributes
        attributes = span.get("attributes", {})
        resource_attributes = span.get("resource", {}).get("attributes", {})
        
        # Extract agent ID and agent name from cloud.resource_id ARN
        # Format: arn:aws:bedrock-agentcore:region:account:runtime/stack_agent-RandomID/runtime-endpoint/...
        # Example: arn:aws:bedrock-agentcore:us-east-1:123:runtime/marodon_fast_umich-v3vPp178fn/...
        agent_id = None
        agent_name = None
        cloud_resource_id = resource_attributes.get("cloud.resource_id", "")
        if cloud_resource_id:
            # Extract runtime ID from ARN (e.g., "marodon_fast_umich-v3vPp178fn")
            parts = cloud_resource_id.split("/")
            if len(parts) >= 2:
                runtime_id = parts[1]  # e.g., "marodon_fast_umich-v3vPp178fn"
                agent_id = runtime_id
                
                # Extract agent name from runtime ID
                # Format: stack_agent-randomID (e.g., "marodon_fast_umich-v3vPp178fn")
                # Split by dash to separate agent part from random ID
                if "-" in runtime_id:
                    base_part = runtime_id.rsplit("-", 1)[0]  # e.g., "marodon_fast_umich"
                    
                    # Now extract agent name by taking the last underscore-separated part
                    # This handles multi-part stack names like "marodon_fast"
                    if "_" in base_part:
                        agent_name = base_part.rsplit("_", 1)[1]  # e.g., "umich"
                        logger.debug(f"Extracted agent name '{agent_name}' from runtime ID '{runtime_id}'")
        
        # Return simplified span structure
        return {
            "traceId": span.get("traceId"),
            "spanId": span.get("spanId"),
            "parentSpanId": span.get("parentSpanId"),
            "name": span.get("name"),
            "startTime": span.get("startTime"),
            "endTime": span.get("endTime"),
            "sessionId": attributes.get("session.id"),
            "agentId": agent_id,
            "agentName": agent_name,
            "latencyMs": attributes.get("latency_ms"),
            "errorType": attributes.get("error_type"),
            "timestamp": log_event.get("timestamp")
        }
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse span JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing span: {e}", exc_info=True)
        return None


def extract_agent_name_from_session_id(session_id: str) -> Optional[str]:
    """
    Extract agent name from session ID prefix.
    
    Session IDs often have format: {agent_name}_{uuid}
    Examples:
        - "orchestrator_7a289a85-c421-4520-8dcc-5c11121f133c" -> "orchestrator"
        - "coder_2b386568-8356-4c14-8c47-f073e75f77e2" -> "coder"
        - "7a289a85-c421-4520-8dcc-5c11121f133c" -> None (no prefix)
    
    Args:
        session_id: Session ID string
        
    Returns:
        Agent name if prefix found, None otherwise
    """
    if "_" in session_id:
        prefix = session_id.split("_", 1)[0]
        # Validate it's not just a UUID part (UUIDs don't start with letters only)
        if prefix and not prefix[0].isdigit():
            return prefix
    return None


def group_spans_by_session(spans: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group spans by session ID.

    Args:
        spans: List of parsed span dictionaries

    Returns:
        Dictionary mapping session ID to list of spans
    """
    sessions = defaultdict(list)
    
    for span in spans:
        session_id = span.get("sessionId")
        if session_id:
            sessions[session_id].append(span)
    
    return dict(sessions)


def build_session_summary(session_id: str, spans: List[Dict[str, Any]], stack_name: str) -> Dict[str, Any]:
    """
    Build session summary from list of spans.

    Args:
        session_id: Session ID
        spans: List of spans for this session
        stack_name: Stack name for SSM parameter lookups

    Returns:
        Session summary dictionary
    """
    # Sort spans by timestamp
    sorted_spans = sorted(spans, key=lambda s: s.get("timestamp", 0))
    
    # Get first and last span for timing
    first_span = sorted_spans[0] if sorted_spans else {}
    last_span = sorted_spans[-1] if sorted_spans else {}
    
    # Calculate duration (milliseconds)
    start_time = first_span.get("timestamp", 0)
    end_time = last_span.get("timestamp", 0)
    duration_ms = end_time - start_time if end_time > start_time else 0
    
    # Determine status (completed, failed, or in-progress)
    has_error = any(span.get("errorType") for span in spans)
    status = "failed" if has_error else "completed"
    
    # Extract agent name - try session ID prefix first (most reliable)
    agent_name = extract_agent_name_from_session_id(session_id)
    
    # Fall back to span-based extraction if no prefix found
    if not agent_name:
        agent_names = [span.get("agentName") for span in spans if span.get("agentName")]
        agent_name = max(set(agent_names), key=agent_names.count) if agent_names else "unknown"
    
    # Map agent name to display name using SSM
    if agent_name != "unknown":
        display_name = get_agent_display_name(agent_name, stack_name)
    else:
        display_name = "unknown"
    
    # Extract agent ID
    agent_ids = [span.get("agentId") for span in spans if span.get("agentId")]
    agent_id = agent_ids[0] if agent_ids else None
    
    # Count spans
    span_count = len(spans)
    
    return {
        "sessionId": session_id,
        "agentName": agent_name,  # Internal name for filtering (e.g., "umich", "coder")
        "agentDisplayName": display_name,  # Display name for UI (e.g., "UMich Specialist", "Coder Agent")
        "agentId": agent_id,
        "startTime": start_time,
        "endTime": end_time,
        "duration": duration_ms,
        "status": status,
        "spanCount": span_count
    }


def filter_sessions(
    sessions: List[Dict[str, Any]],
    agent_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter sessions by agent name.

    Args:
        sessions: List of session summaries
        agent_name: Filter by agent name (optional, exact match)

    Returns:
        Filtered list of sessions
    """
    if not agent_name:
        logger.info(f"No agent filter applied, returning all {len(sessions)} sessions")
        return sessions
    
    # Log all unique agent names in sessions for debugging
    unique_agents = set(session.get("agentName") for session in sessions)
    logger.info(f"Filter requested for: '{agent_name}'")
    logger.info(f"Available agent names in sessions: {unique_agents}")
    
    filtered = [
        session for session in sessions
        if session.get("agentName") == agent_name
    ]
    
    logger.info(
        f"Filtered by agent name '{agent_name}': "
        f"{len(filtered)} sessions (from {len(sessions)})"
    )
    
    # Log first few sessions for debugging if filter returns nothing
    if len(filtered) == 0 and len(sessions) > 0:
        logger.warning(f"Filter returned 0 sessions. First session agentName: '{sessions[0].get('agentName')}'")
    
    return filtered


def get_cors_headers(origin: Optional[str] = None) -> Dict[str, str]:
    """
    Generate CORS headers for the response.

    Args:
        origin: Origin header from the request

    Returns:
        Dictionary of CORS headers
    """
    allowed_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")

    # Check if origin is allowed
    if origin and origin in allowed_origins:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        }

    # Default to first allowed origin if no match
    default_origin = allowed_origins[0] if allowed_origins else "*"
    return {
        "Access-Control-Allow-Origin": default_origin,
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
    }


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for observability sessions API endpoint.

    Args:
        event: API Gateway event containing request details
        context: Lambda context object

    Returns:
        API Gateway response with session list or error message
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # Get origin for CORS
    origin = event.get("headers", {}).get("origin") or event.get("headers", {}).get(
        "Origin"
    )
    cors_headers = get_cors_headers(origin)

    # Handle OPTIONS request for CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": ""
        }

    try:
        # Extract user ID from JWT token (for future user scoping)
        user_id = extract_user_id_from_jwt(event)
        if not user_id:
            logger.error("Could not extract user ID from JWT token")
            return {
                "statusCode": 401,
                "headers": cors_headers,
                "body": json.dumps(
                    {"error": "Unauthorized", "message": "Invalid authentication token"}
                ),
            }

        # Parse query parameters
        query_params = event.get("queryStringParameters") or {}
        agent_name_filter = query_params.get("agentName")
        start_time = query_params.get("startTime")
        end_time = query_params.get("endTime")
        next_token = query_params.get("nextToken")
        limit = int(query_params.get("limit", "50"))

        # Convert time strings to integers if provided
        # Default to last 24 hours if not specified
        end_time_ms = int(end_time) if end_time else int(time.time() * 1000)
        start_time_ms = int(start_time) if start_time else end_time_ms - (24 * 60 * 60 * 1000)

        logger.info(
            f"Query params - agentName: {agent_name_filter}, "
            f"startTime: {start_time_ms}, endTime: {end_time_ms}, limit: {limit}"
        )

        # Query all spans from CloudWatch Logs (with pagination)
        all_parsed_spans = []
        next_token = None
        
        while True:
            spans_result = query_spans_from_cloudwatch(
                start_time=start_time_ms,
                end_time=end_time_ms,
                next_token=next_token,
                limit=10000  # Query max spans per page
            )

            if not spans_result["success"]:
                logger.error(f"Failed to query spans: {spans_result.get('error')}")
                return {
                    "statusCode": 500,
                    "headers": cors_headers,
                    "body": json.dumps(
                        {"error": "Internal server error", "message": "Failed to query observability data"}
                    ),
                }

            # Parse OTEL spans
            log_events = spans_result.get("events", [])
            for event_data in log_events:
                span = parse_otel_span(event_data)
                if span:
                    all_parsed_spans.append(span)

            # Check for more pages
            next_token = spans_result.get("nextToken")
            if not next_token:
                break
                
        logger.info(f"Parsed {len(all_parsed_spans)} total spans from CloudWatch")

        # Group spans by session
        sessions_map = group_spans_by_session(all_parsed_spans)
        
        logger.info(f"Found {len(sessions_map)} unique sessions")

        # Build session summaries
        sessions = []
        stack_name = os.environ.get("STACK_NAME_BASE", "")
        for session_id, session_spans in sessions_map.items():
            summary = build_session_summary(session_id, session_spans, stack_name)
            sessions.append(summary)

        # Sort sessions by start time (newest first)
        sessions.sort(key=lambda s: s.get("startTime", 0), reverse=True)

        # Apply agent name filter
        sessions = filter_sessions(sessions, agent_name_filter)

        # Apply pagination limit
        paginated_sessions = sessions[:limit]

        logger.info(f"Returning {len(paginated_sessions)} sessions")

        # Return success response
        return {
            "statusCode": 200,
            "headers": {**cors_headers, "Content-Type": "application/json"},
            "body": json.dumps({
                "sessions": paginated_sessions,
                "count": len(paginated_sessions),
                "nextToken": spans_result.get("nextToken")
            }),
        }

    except ValueError as e:
        logger.error(f"Invalid parameter: {str(e)}")
        return {
            "statusCode": 400,
            "headers": cors_headers,
            "body": json.dumps(
                {"error": "Bad request", "message": str(e)}
            ),
        }

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": "Internal server error", "message": str(e)}),
        }
