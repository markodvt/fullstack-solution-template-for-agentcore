"""
Observability Traces API Lambda Function

This Lambda function retrieves trace data for a specific session from CloudWatch Logs
by querying OTEL spans emitted by AgentCore Runtime. It builds a hierarchical trace
structure showing the parent-child relationships between spans.

Data Source: CloudWatch Logs aws/spans log group (OTEL format)
Approach: Query spans using FilterLogEvents API filtered by session.id attribute

Environment Variables:
    STACK_NAME_BASE: Base name of the CloudFormation stack
    CORS_ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins

Path Parameters:
    sessionId: Session ID to retrieve traces for (required)

Returns:
    JSON response with trace structure including spans and their relationships
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
logs_client = boto3.client("logs")

# CloudWatch Logs configuration
SPANS_LOG_GROUP = "aws/spans"


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


def query_spans_for_session(session_id: str) -> Dict[str, Any]:
    """
    Query OTEL spans from CloudWatch Logs for a specific session.

    Args:
        session_id: Session ID to filter spans by

    Returns:
        Dictionary containing log events and query status
    """
    try:
        # Build filter pattern to match session.id attribute
        # OTEL spans have attributes.session.id field
        filter_pattern = f'{{ $.attributes.session.id = "{session_id}" }}'
        
        params = {
            "logGroupName": SPANS_LOG_GROUP,
            "filterPattern": filter_pattern,
            "limit": 10000  # CloudWatch Logs max limit
        }
        
        logger.info(f"Querying CloudWatch Logs for session: {session_id}")
        
        response = logs_client.filter_log_events(**params)
        
        events = response.get("events", [])
        logger.info(f"FilterLogEvents returned {len(events)} events for session {session_id}")
        
        return {
            "success": True,
            "events": events,
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
        "attributes": {
            "session.id": "...",
            "tool.name": "...",
            "llm.model": "...",
            "llm.usage.input_tokens": 100,
            "llm.usage.output_tokens": 50,
            "error_type": "...",
            "error_message": "..."
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
        
        # Determine span type based on attributes and name
        span_type = determine_span_type(span.get("name", ""), attributes)
        
        # Calculate duration in milliseconds
        start_time = span.get("startTime", "")
        end_time = span.get("endTime", "")
        duration_ms = calculate_duration(start_time, end_time)
        
        # Determine status
        status = "error" if attributes.get("error_type") else "ok"
        
        # Return simplified span structure
        return {
            "spanId": span.get("spanId"),
            "parentSpanId": span.get("parentSpanId"),
            "traceId": span.get("traceId"),
            "name": span.get("name"),
            "spanType": span_type,
            "startTime": parse_timestamp(start_time),
            "endTime": parse_timestamp(end_time),
            "duration": duration_ms,
            "status": status,
            "attributes": extract_relevant_attributes(attributes, span_type)
        }
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse span JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing span: {e}", exc_info=True)
        return None


def determine_span_type(name: str, attributes: Dict[str, Any]) -> str:
    """
    Determine span type based on span name and attributes.

    Args:
        name: Span name
        attributes: Span attributes

    Returns:
        Span type: agent_invocation, llm_invocation, tool_call, or unknown
    """
    # Check attributes first (most reliable)
    if "tool.name" in attributes:
        return "tool_call"
    if "llm.model" in attributes or "llm.usage.input_tokens" in attributes:
        return "llm_invocation"
    
    # Fall back to name-based detection
    name_lower = name.lower()
    if "agent" in name_lower or "invocation" in name_lower:
        return "agent_invocation"
    if "llm" in name_lower or "model" in name_lower:
        return "llm_invocation"
    if "tool" in name_lower:
        return "tool_call"
    
    return "unknown"


def extract_relevant_attributes(attributes: Dict[str, Any], span_type: str) -> Dict[str, Any]:
    """
    Extract relevant attributes based on span type.

    Args:
        attributes: All span attributes
        span_type: Type of span

    Returns:
        Dictionary of relevant attributes for this span type
    """
    relevant = {}
    
    if span_type == "tool_call":
        if "tool.name" in attributes:
            relevant["toolName"] = attributes["tool.name"]
        if "tool.input" in attributes:
            relevant["toolInput"] = attributes["tool.input"]
        if "tool.output" in attributes:
            relevant["toolOutput"] = attributes["tool.output"]
    
    elif span_type == "llm_invocation":
        if "llm.model" in attributes:
            relevant["model"] = attributes["llm.model"]
        if "llm.usage.input_tokens" in attributes:
            relevant["inputTokens"] = attributes["llm.usage.input_tokens"]
        if "llm.usage.output_tokens" in attributes:
            relevant["outputTokens"] = attributes["llm.usage.output_tokens"]
        if "llm.usage.total_tokens" in attributes:
            relevant["totalTokens"] = attributes["llm.usage.total_tokens"]
    
    # Include error information for all span types
    if "error_type" in attributes:
        relevant["errorType"] = attributes["error_type"]
    if "error_message" in attributes:
        relevant["errorMessage"] = attributes["error_message"]
    
    return relevant


def parse_timestamp(timestamp_str: str) -> int:
    """
    Parse ISO 8601 timestamp to milliseconds since epoch.

    Args:
        timestamp_str: ISO 8601 timestamp string

    Returns:
        Milliseconds since epoch
    """
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except Exception as e:
        logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
        return 0


def calculate_duration(start_time: str, end_time: str) -> int:
    """
    Calculate duration between two timestamps in milliseconds.

    Args:
        start_time: ISO 8601 start timestamp
        end_time: ISO 8601 end timestamp

    Returns:
        Duration in milliseconds
    """
    try:
        start_ms = parse_timestamp(start_time)
        end_ms = parse_timestamp(end_time)
        return end_ms - start_ms if end_ms > start_ms else 0
    except Exception as e:
        logger.warning(f"Failed to calculate duration: {e}")
        return 0


def build_trace_structure(spans: List[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
    """
    Build trace structure from list of spans.

    Args:
        spans: List of parsed span dictionaries
        session_id: Session ID for this trace

    Returns:
        Trace structure with hierarchical span relationships
    """
    if not spans:
        return {
            "traceId": None,
            "sessionId": session_id,
            "spans": [],
            "startTime": 0,
            "endTime": 0,
            "duration": 0
        }
    
    # Sort spans by start time
    sorted_spans = sorted(spans, key=lambda s: s.get("startTime", 0))
    
    # Get trace ID from first span
    trace_id = sorted_spans[0].get("traceId")
    
    # Calculate overall trace timing
    start_time = sorted_spans[0].get("startTime", 0)
    end_time = max(span.get("endTime", 0) for span in sorted_spans)
    duration = end_time - start_time if end_time > start_time else 0
    
    return {
        "traceId": trace_id,
        "sessionId": session_id,
        "spans": sorted_spans,
        "startTime": start_time,
        "endTime": end_time,
        "duration": duration
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
    Lambda handler for observability traces API endpoint.

    Args:
        event: API Gateway event containing request details
        context: Lambda context object

    Returns:
        API Gateway response with trace data or error message
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

        # Extract session ID from path parameters
        path_params = event.get("pathParameters") or {}
        session_id = path_params.get("sessionId")
        
        if not session_id:
            logger.error("Missing sessionId path parameter")
            return {
                "statusCode": 400,
                "headers": cors_headers,
                "body": json.dumps(
                    {"error": "Bad request", "message": "Missing sessionId parameter"}
                ),
            }

        logger.info(f"Retrieving traces for session: {session_id}")

        # Query spans for this session from CloudWatch Logs
        spans_result = query_spans_for_session(session_id)

        if not spans_result["success"]:
            logger.error(f"Failed to query spans: {spans_result.get('error')}")
            return {
                "statusCode": 500,
                "headers": cors_headers,
                "body": json.dumps(
                    {"error": "Internal server error", "message": "Failed to query trace data"}
                ),
            }

        # Parse OTEL spans
        log_events = spans_result.get("events", [])
        
        if not log_events:
            logger.warning(f"No spans found for session: {session_id}")
            return {
                "statusCode": 404,
                "headers": cors_headers,
                "body": json.dumps(
                    {"error": "Not found", "message": f"No trace data found for session {session_id}"}
                ),
            }
        
        parsed_spans = []
        for event_data in log_events:
            span = parse_otel_span(event_data)
            if span:
                parsed_spans.append(span)

        logger.info(f"Parsed {len(parsed_spans)} spans for session {session_id}")

        # Build trace structure
        trace = build_trace_structure(parsed_spans, session_id)

        # Return success response
        return {
            "statusCode": 200,
            "headers": {**cors_headers, "Content-Type": "application/json"},
            "body": json.dumps({"trace": trace}),
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
