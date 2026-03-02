"""
Agent Discovery Lambda Function

This Lambda function retrieves agent metadata from SSM Parameter Store
and returns a list of available agents for the frontend to discover.

Environment Variables:
    STACK_NAME_BASE: Base name of the CloudFormation stack
    CORS_ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins

Returns:
    JSON response with list of available agents and their metadata
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
ssm_client = boto3.client("ssm")
s3_client = boto3.client("s3")


def get_agent_metadata(
    stack_name_base: str, agent_name: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve metadata for a single agent from SSM Parameter Store.

    Args:
        stack_name_base: Base name of the CloudFormation stack
        agent_name: Name of the agent (e.g., "orchestrator", "umich")

    Returns:
        Dictionary containing agent metadata, or None if agent not found
    """
    base_path = f"/{stack_name_base}/agents/{agent_name}"

    try:
        # Get all parameters for this agent
        response = ssm_client.get_parameters_by_path(
            Path=base_path, Recursive=False, WithDecryption=False
        )

        if not response.get("Parameters"):
            logger.warning(f"No parameters found for agent: {agent_name}")
            return None

        # Parse parameters into metadata dictionary
        metadata = {"name": agent_name}

        for param in response["Parameters"]:
            param_name = param["Name"].split("/")[-1]  # Get last part of path
            param_value = param["Value"]

            # Map parameter names to metadata fields
            if param_name == "runtime-arn":
                metadata["runtimeArn"] = param_value
            elif param_name == "runtime-id":
                metadata["runtimeId"] = param_value
            elif param_name == "display-name":
                metadata["displayName"] = param_value
            elif param_name == "description":
                metadata["description"] = param_value
            elif param_name == "is-default":
                metadata["isDefault"] = param_value.lower() == "true"
            elif param_name == "status":
                metadata["status"] = param_value
            elif param_name == "error":
                metadata["error"] = param_value
            elif param_name == "pattern":
                metadata["pattern"] = param_value
            elif param_name == "tools":
                # Parse tools JSON array
                try:
                    metadata["tools"] = json.loads(param_value)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse tools JSON for {agent_name}")
                    metadata["tools"] = []
            elif param_name == "model":
                # Store model ID as string
                metadata["model"] = param_value
            elif param_name == "source-code-url":
                # Handle S3 source code URL
                try:
                    if param_value.startswith("s3://"):
                        # Parse S3 URL to extract bucket and key
                        s3_url_parts = param_value[5:].split("/", 1)
                        if len(s3_url_parts) == 2:
                            bucket, key = s3_url_parts
                            
                            # Generate presigned URL (1 hour expiry)
                            metadata["sourceCodeUrl"] = s3_client.generate_presigned_url(
                                'get_object',
                                Params={'Bucket': bucket, 'Key': key},
                                ExpiresIn=3600
                            )
                            
                            # Fetch source code from S3
                            try:
                                obj = s3_client.get_object(Bucket=bucket, Key=key)
                                # Decode source code from bytes to UTF-8 string
                                metadata["sourceCode"] = obj['Body'].read().decode('utf-8')
                            except ClientError as s3_error:
                                logger.warning(
                                    f"Failed to fetch source code from S3 for {agent_name}: {s3_error}"
                                )
                                metadata["sourceCode"] = None
                        else:
                            logger.warning(
                                f"Invalid S3 URL format for {agent_name}: {param_value}"
                            )
                    else:
                        logger.warning(
                            f"Source code URL is not an S3 URL for {agent_name}: {param_value}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to process source code URL for {agent_name}: {e}"
                    )
                    metadata["sourceCode"] = None
            elif param_name == "system-prompt":
                # Store system prompt as string
                metadata["systemPrompt"] = param_value
            elif param_name == "long-description":
                # Store long description as string
                metadata["longDescription"] = param_value

        # Validate required fields
        required_fields = ["displayName", "status"]
        for field in required_fields:
            if field not in metadata:
                logger.warning(
                    f"Missing required field '{field}' for agent: {agent_name}"
                )
                return None

        return metadata

    except ClientError as e:
        logger.error(f"Error retrieving metadata for agent {agent_name}: {str(e)}")
        return None


def discover_agents(stack_name_base: str) -> List[Dict[str, Any]]:
    """
    Discover all agents by querying SSM Parameter Store.

    Args:
        stack_name_base: Base name of the CloudFormation stack

    Returns:
        List of agent metadata dictionaries
    """
    agents_base_path = f"/{stack_name_base}/agents"

    try:
        # Get all parameters under the agents path (with pagination)
        all_parameters = []
        next_token = None

        while True:
            if next_token:
                response = ssm_client.get_parameters_by_path(
                    Path=agents_base_path,
                    Recursive=True,
                    WithDecryption=False,
                    NextToken=next_token,
                )
            else:
                response = ssm_client.get_parameters_by_path(
                    Path=agents_base_path, Recursive=True, WithDecryption=False
                )

            all_parameters.extend(response.get("Parameters", []))

            next_token = response.get("NextToken")
            if not next_token:
                break

        if not all_parameters:
            logger.warning("No agent parameters found in SSM")
            return []

        # Extract unique agent names from parameter paths
        agent_names = set()
        for param in all_parameters:
            # Path format: /{stack_name_base}/agents/{agent_name}/{param_name}
            path_parts = param["Name"].split("/")
            if len(path_parts) >= 4:
                agent_name = path_parts[3]
                agent_names.add(agent_name)

        logger.info(f"Found {len(agent_names)} agents: {agent_names}")

        # Retrieve full metadata for each agent
        agents = []
        for agent_name in agent_names:
            metadata = get_agent_metadata(stack_name_base, agent_name)
            if metadata:
                agents.append(metadata)

        # Sort agents: default first, then alphabetically
        agents.sort(key=lambda x: (not x.get("isDefault", False), x.get("name", "")))

        return agents

    except ClientError as e:
        logger.error(f"Error discovering agents: {str(e)}")
        raise


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
    Lambda handler for agent discovery endpoint.

    Args:
        event: API Gateway event containing request details
        context: Lambda context object

    Returns:
        API Gateway response with agent list or error message
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # Get origin for CORS
    origin = event.get("headers", {}).get("origin") or event.get("headers", {}).get(
        "Origin"
    )
    cors_headers = get_cors_headers(origin)

    try:
        # Get stack name from environment
        stack_name_base = os.environ.get("STACK_NAME_BASE")
        if not stack_name_base:
            logger.error("STACK_NAME_BASE environment variable not set")
            return {
                "statusCode": 500,
                "headers": cors_headers,
                "body": json.dumps(
                    {"error": "Internal server error", "message": "Configuration error"}
                ),
            }

        # Discover agents
        agents = discover_agents(stack_name_base)

        logger.info(f"Successfully discovered {len(agents)} agents")

        # Return success response
        return {
            "statusCode": 200,
            "headers": {**cors_headers, "Content-Type": "application/json"},
            "body": json.dumps({"agents": agents, "count": len(agents)}),
        }

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": "Internal server error", "message": str(e)}),
        }
