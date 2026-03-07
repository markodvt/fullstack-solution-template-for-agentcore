"""
Observability Metrics API Lambda Function

This Lambda function aggregates metrics from CloudWatch Logs by querying
OTEL spans emitted by AgentCore Runtime. It calculates:
- Total sessions
- Average session duration
- Token usage (from trace attributes)
- Success rate
- Top tools used
- Per-agent breakdowns

Data Source: CloudWatch Logs aws/spans log group (OTEL format)

Environment Variables:
    STACK_NAME_BASE: Base name of the CloudFormation stack
    CORS_ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins

Query Parameters:
    timeRange: Time range in hours (optional, default: 24, options: 1, 24, 168, 720)

Returns:
    JSON response with aggregated metrics
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



def query_spans_from_cloudwatch(
    start_time: int,
    end_time: int,
    next_token: Optional[str] = None,
    limit: int = 10000
) -> Dict[str, Any]:
    """
    Query OTEL spans from CloudWatch Logs aws/spans log group.

    Args:
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch
        next_token: Pagination token (optional)
        limit: Maximum number of log events to return (max 10000)

    Returns:
        Dictionary containing log events and pagination info
    """
    try:
        params = {
            "logGroupName": SPANS_LOG_GROUP,
            "startTime": start_time,
            "endTime": end_time,
            "limit": min(limit, 10000)  # CloudWatch Logs max limit
        }
        
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
            "toolName": attributes.get("tool.name"),
            "inputTokens": attributes.get("gen_ai.usage.input_tokens"),
            "outputTokens": attributes.get("gen_ai.usage.output_tokens"),
            "timestamp": log_event.get("timestamp")
        }
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse span JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing span: {e}", exc_info=True)
        return None


def aggregate_metrics(spans: List[Dict[str, Any]], stack_name: str) -> Dict[str, Any]:
    """
    Aggregate metrics from list of spans.

    Args:
        spans: List of parsed span dictionaries
        stack_name: Stack name for SSM parameter lookups

    Returns:
        Dictionary containing aggregated metrics
    """
    # Group spans by session
    sessions_map = defaultdict(list)
    for span in spans:
        session_id = span.get("sessionId")
        if session_id:
            sessions_map[session_id].append(span)
    
    # Calculate session-level metrics
    total_sessions = len(sessions_map)
    total_duration_ms = 0
    successful_sessions = 0
    failed_sessions = 0
    total_input_tokens = 0
    total_output_tokens = 0
    
    # Per-agent metrics
    agent_metrics = defaultdict(lambda: {
        "sessionCount": 0,
        "totalDuration": 0,
        "successCount": 0,
        "failCount": 0,
        "inputTokens": 0,
        "outputTokens": 0
    })
    
    # Tool usage tracking
    tool_usage = defaultdict(int)
    
    for session_id, session_spans in sessions_map.items():
        # Sort spans by timestamp
        sorted_spans = sorted(session_spans, key=lambda s: s.get("timestamp", 0))
        
        # Calculate session duration
        if sorted_spans:
            first_span = sorted_spans[0]
            last_span = sorted_spans[-1]
            start_time = first_span.get("timestamp", 0)
            end_time = last_span.get("timestamp", 0)
            duration_ms = end_time - start_time if end_time > start_time else 0
            total_duration_ms += duration_ms
            
            # Determine session status
            has_error = any(span.get("errorType") for span in session_spans)
            if has_error:
                failed_sessions += 1
            else:
                successful_sessions += 1
            
            # Extract agent name - try session ID prefix first (most reliable)
            agent_name = extract_agent_name_from_session_id(session_id)
            
            # Fall back to span-based extraction if no prefix found
            if not agent_name:
                agent_names = [span.get("agentName") for span in session_spans if span.get("agentName")]
                agent_name = max(set(agent_names), key=agent_names.count) if agent_names else "unknown"
            
            # Map agent name to display name using SSM
            if agent_name != "unknown":
                display_name = get_agent_display_name(agent_name, stack_name)
            else:
                display_name = "unknown"
            
            # Update per-agent metrics
            agent_metrics[display_name]["sessionCount"] += 1
            agent_metrics[display_name]["totalDuration"] += duration_ms
            if has_error:
                agent_metrics[display_name]["failCount"] += 1
            else:
                agent_metrics[display_name]["successCount"] += 1
            
            # Aggregate token usage
            for span in session_spans:
                input_tokens = span.get("inputTokens", 0) or 0
                output_tokens = span.get("outputTokens", 0) or 0
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                agent_metrics[display_name]["inputTokens"] += input_tokens
                agent_metrics[display_name]["outputTokens"] += output_tokens
                
                # Track tool usage
                tool_name = span.get("toolName")
                if tool_name:
                    tool_usage[tool_name] += 1
    
    # Calculate averages
    avg_duration_ms = total_duration_ms / total_sessions if total_sessions > 0 else 0
    success_rate = (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    # Format per-agent metrics
    agent_breakdown = []
    for agent_name, metrics in agent_metrics.items():
        agent_success_rate = (
            (metrics["successCount"] / metrics["sessionCount"] * 100)
            if metrics["sessionCount"] > 0 else 0
        )
        agent_avg_duration = (
            metrics["totalDuration"] / metrics["sessionCount"]
            if metrics["sessionCount"] > 0 else 0
        )
        agent_breakdown.append({
            "agentName": agent_name,
            "sessionCount": metrics["sessionCount"],
            "avgDuration": round(agent_avg_duration, 2),
            "successRate": round(agent_success_rate, 2),
            "inputTokens": metrics["inputTokens"],
            "outputTokens": metrics["outputTokens"],
            "totalTokens": metrics["inputTokens"] + metrics["outputTokens"]
        })
    
    # Sort agent breakdown by session count (descending)
    agent_breakdown.sort(key=lambda x: x["sessionCount"], reverse=True)
    
    # Format top tools
    top_tools = [
        {"toolName": tool_name, "usageCount": count}
        for tool_name, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    return {
        "totalSessions": total_sessions,
        "avgDuration": round(avg_duration_ms, 2),
        "successRate": round(success_rate, 2),
        "totalInputTokens": total_input_tokens,
        "totalOutputTokens": total_output_tokens,
        "totalTokens": total_input_tokens + total_output_tokens,
        "agentBreakdown": agent_breakdown,
        "topTools": top_tools
    }


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
    Lambda handler for observability metrics API endpoint.

    Args:
        event: API Gateway event containing request details
        context: Lambda context object

    Returns:
        API Gateway response with aggregated metrics or error message
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
        time_range_hours = int(query_params.get("timeRange", "24"))

        # Validate time range
        if time_range_hours not in [1, 24, 168, 720]:  # 1h, 24h, 7d, 30d
            return {
                "statusCode": 400,
                "headers": cors_headers,
                "body": json.dumps(
                    {"error": "Bad request", "message": "Invalid timeRange. Must be 1, 24, 168, or 720"}
                ),
            }

        # Calculate time range in milliseconds
        end_time_ms = int(time.time() * 1000)
        start_time_ms = end_time_ms - (time_range_hours * 60 * 60 * 1000)

        logger.info(
            f"Query params - timeRange: {time_range_hours}h, "
            f"startTime: {start_time_ms}, endTime: {end_time_ms}"
        )

        # Query all spans in time range (with pagination)
        all_spans = []
        next_token = None
        
        while True:
            spans_result = query_spans_from_cloudwatch(
                start_time=start_time_ms,
                end_time=end_time_ms,
                next_token=next_token,
                limit=10000
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
                    all_spans.append(span)

            # Check for more pages
            next_token = spans_result.get("nextToken")
            if not next_token:
                break

        logger.info(f"Parsed {len(all_spans)} total spans")

        # Aggregate metrics
        stack_name = os.environ.get("STACK_NAME_BASE", "")
        metrics = aggregate_metrics(all_spans, stack_name)

        logger.info(f"Aggregated metrics: {json.dumps(metrics)}")

        # Return success response
        return {
            "statusCode": 200,
            "headers": {**cors_headers, "Content-Type": "application/json"},
            "body": json.dumps({
                "metrics": metrics,
                "timeRange": time_range_hours,
                "startTime": start_time_ms,
                "endTime": end_time_ms
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
