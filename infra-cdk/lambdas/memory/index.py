"""
Memory API Lambda Function

This Lambda function retrieves memory records from AgentCore Memory service
and returns them for the frontend Memory page.

Environment Variables:
    MEMORY_ID: AgentCore Memory ID
    STACK_NAME_BASE: Base name of the CloudFormation stack
    CORS_ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins

Query Parameters:
    agentName: Filter memories by agent name (optional)
    userId: Filter memories by user ID (optional)
    sortOrder: Sort order - "asc" or "desc" (optional, default: "desc")
    nextToken: Pagination token (optional)
    limit: Maximum results per page (optional, default: 50, max: 100)

Returns:
    JSON response with list of memory records
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
agentcore_client = boto3.client("bedrock-agentcore")


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


def convert_strategy_type_to_singular(strategy_type: str) -> str:
    """
    Convert plural strategy type to singular form for frontend compatibility.
    
    Args:
        strategy_type: Strategy type in plural form (e.g., "summaries", "preferences", "facts")
    
    Returns:
        Strategy type in singular form (e.g., "summary", "preference", "fact")
    """
    mapping = {
        "summaries": "summary",
        "preferences": "preference",
        "facts": "fact"
    }
    return mapping.get(strategy_type, strategy_type)


def extract_agent_name_from_session_id(session_id: Optional[str]) -> Optional[str]:
    """
    Extract agent name from session ID prefix.
    
    Agents use session ID prefixing to distinguish themselves:
    - Colorado agent: colorado_{session_id}
    - Coder agent: coder_{session_id}
    - UMich agent: umich_{session_id}
    - Orchestrator: base session_id (no prefix)
    
    Args:
        session_id: Session ID string (may contain agent prefix)
    
    Returns:
        Agent name extracted from prefix, "orchestrator" if no prefix, or None if session_id is None
    """
    if not session_id:
        return None
    
    # Check if session ID has a prefix (contains underscore)
    if "_" in session_id:
        # Extract prefix as agent name
        agent_name = session_id.split("_")[0]
        logger.debug(f"Extracted agent name '{agent_name}' from session ID '{session_id}'")
        return agent_name
    
    # No prefix means orchestrator
    logger.debug(f"No prefix in session ID '{session_id}', assuming orchestrator")
    return "orchestrator"





def retrieve_memory_records_by_namespace(
    memory_id: str,
    namespace: str,
    max_results: int = 50,
    next_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve memory records from a specific namespace using ListMemoryRecords API.

    Args:
        memory_id: AgentCore Memory ID
        namespace: Memory namespace (e.g., "/summaries/{actorId}/{sessionId}")
        max_results: Maximum number of results to return
        next_token: Pagination token

    Returns:
        Dictionary containing memory records and pagination info
    """
    try:
        params = {
            "memoryId": memory_id,
            "namespace": namespace,
            "maxResults": min(max_results, 100)  # Cap at 100
        }
        
        if next_token:
            params["nextToken"] = next_token
        
        response = agentcore_client.list_memory_records(**params)
        
        logger.info(
            f"ListMemoryRecords ({namespace}) returned "
            f"{len(response.get('memoryRecordSummaries', []))} records"
        )
        
        return {
            "success": True,
            "records": response.get("memoryRecordSummaries", []),
            "nextToken": response.get("nextToken")
        }
        
    except ClientError as e:
        logger.error(f"ListMemoryRecords ({namespace}) failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "records": []
        }


def retrieve_all_memory_records(
    memory_id: str,
    actor_id: str,
    max_results: int = 50,
    next_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve memory records from all memory strategies.

    Args:
        memory_id: AgentCore Memory ID
        actor_id: User ID for scoping
        max_results: Maximum number of results to return
        next_token: Pagination token

    Returns:
        Dictionary containing all memory records and pagination info
    """
    # Define namespaces for each memory strategy
    namespaces = [
        f"/summaries/{actor_id}",
        f"/preferences/{actor_id}",
        f"/facts/{actor_id}"
    ]
    
    all_records = []
    
    # Retrieve records from each namespace
    for namespace in namespaces:
        result = retrieve_memory_records_by_namespace(
            memory_id=memory_id,
            namespace=namespace,
            max_results=max_results,
            next_token=None  # Don't paginate individual namespaces for now
        )
        
        if result["success"]:
            # Add strategy type to each record
            strategy_type = namespace.split("/")[1]  # "summaries", "preferences", or "facts"
            for record in result["records"]:
                record["strategyType"] = strategy_type
            
            all_records.extend(result["records"])
    
    # Sort by createdAt (newest first)
    all_records.sort(
        key=lambda x: x.get("createdAt", ""),
        reverse=True
    )
    
    # Apply pagination limit
    paginated_records = all_records[:max_results]
    
    # Simple pagination: if we have more records, provide a next token
    # (In production, implement proper cursor-based pagination)
    has_more = len(all_records) > max_results
    
    return {
        "success": True,
        "records": paginated_records,
        "nextToken": "more" if has_more else None,
        "totalCount": len(all_records)
    }


def transform_memory_records(
    records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Transform AgentCore memory records to simplified frontend format.

    Args:
        records: Memory records from ListMemoryRecords

    Returns:
        List of transformed memory objects
    """
    memories = []
    
    # Transform long-term memory records
    for record in records:
        # Extract content text from content object
        content_obj = record.get("content", {})
        content_text = content_obj.get("text", "") if isinstance(content_obj, dict) else str(content_obj)
        
        # Get first namespace from namespaces array
        namespaces = record.get("namespaces", [])
        namespace = namespaces[0] if namespaces else ""
        
        # Extract userId from namespace (format: /strategy/userId/sessionId)
        user_id = ""
        if namespace and "/" in namespace:
            parts = namespace.split("/")
            if len(parts) >= 3:
                user_id = parts[2]
        
        # Extract sessionId from namespace if present
        session_id = None
        if namespace and "/" in namespace:
            parts = namespace.split("/")
            if len(parts) >= 4:
                session_id = parts[3]
        
        # Extract agent name from session ID prefix
        # Agents use session ID prefixing: colorado_{id}, coder_{id}, umich_{id}
        # Orchestrator uses base session ID without prefix
        agent_name = extract_agent_name_from_session_id(session_id)
        
        memory = {
            "id": record.get("memoryRecordId", ""),
            "type": convert_strategy_type_to_singular(record.get("strategyType", "unknown")),
            "content": content_text,
            "timestamp": str(record.get("createdAt", "")),
            "userId": user_id,
            "sessionId": session_id,
            "agentName": agent_name,
        }
        memories.append(memory)
    
    return memories



def filter_memories(
    memories: List[Dict[str, Any]],
    agent_name: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter memories by agent name and/or user ID.
    
    Agent name uses exact match.
    User ID uses partial match (case-insensitive contains) to support searching by partial IDs.

    Args:
        memories: List of memory objects
        agent_name: Filter by agent name (optional, exact match)
        user_id: Filter by user ID (optional, partial match)

    Returns:
        Filtered list of memories
    """
    filtered = memories
    
    logger.info(f"Starting filter with {len(memories)} total memories")
    
    if agent_name:
        # Log agent names before filtering for debugging
        agent_names_found = set(m.get("agentName") for m in filtered if m.get("agentName"))
        logger.info(f"Agent names in memories: {agent_names_found}")
        
        # Exact match for agent name
        filtered = [
            m for m in filtered
            if m.get("agentName") == agent_name
        ]
        logger.info(f"Filtered by agent name '{agent_name}': {len(filtered)} memories (from {len(memories)})")
    
    if user_id:
        before_count = len(filtered)
        # Partial match (case-insensitive contains) for user ID
        user_id_lower = user_id.lower()
        filtered = [
            m for m in filtered
            if user_id_lower in (m.get("userId") or "").lower()
        ]
        logger.info(f"Filtered by user ID '{user_id}' (partial match): {len(filtered)} memories (from {before_count})")
    
    return filtered

def sort_memories(
    memories: List[Dict[str, Any]],
    sort_order: str = "desc"
) -> List[Dict[str, Any]]:
    """
    Sort memories by timestamp.

    Args:
        memories: List of memory objects
        sort_order: "asc" or "desc" (default: "desc")

    Returns:
        Sorted list of memories
    """
    reverse = sort_order.lower() == "desc"
    
    return sorted(
        memories,
        key=lambda x: x.get("timestamp", ""),
        reverse=reverse
    )


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
    Lambda handler for memory API endpoint.

    Args:
        event: API Gateway event containing request details
        context: Lambda context object

    Returns:
        API Gateway response with memory list or error message
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
        # Get Memory ID from environment
        memory_id = os.environ.get("MEMORY_ID")
        if not memory_id:
            logger.error("MEMORY_ID environment variable not set")
            return {
                "statusCode": 500,
                "headers": cors_headers,
                "body": json.dumps(
                    {"error": "Internal server error", "message": "Configuration error"}
                ),
            }

        # Extract user ID from JWT token
        actor_id = extract_user_id_from_jwt(event)
        if not actor_id:
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
        user_id_filter = query_params.get("userId")
        sort_order = query_params.get("sortOrder", "desc")
        next_token = query_params.get("nextToken")
        limit = int(query_params.get("limit", "50"))

        logger.info(
            f"Query params - agentName: {agent_name_filter}, "
            f"userId: {user_id_filter}, sortOrder: {sort_order}, limit: {limit}"
        )

        # Retrieve memory records from all strategies
        records_result = retrieve_all_memory_records(
            memory_id=memory_id,
            actor_id=actor_id,
            max_results=limit,
            next_token=next_token
        )

        # Transform to frontend format
        memories = transform_memory_records(
            records=records_result.get("records", [])
        )

        # Apply filters
        memories = filter_memories(
            memories=memories,
            agent_name=agent_name_filter,
            user_id=user_id_filter
        )

        # Apply sorting
        memories = sort_memories(memories, sort_order)

        logger.info(f"Returning {len(memories)} memories")

        # Return success response
        return {
            "statusCode": 200,
            "headers": {**cors_headers, "Content-Type": "application/json"},
            "body": json.dumps({
                "memories": memories,
                "count": len(memories),
                "nextToken": records_result.get("nextToken")
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
