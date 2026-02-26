"""
Tools for orchestrator to invoke specialist agents.

This module provides functions that allow the orchestrator agent to invoke
specialist agents (Colorado, UMich, Coder) by making direct HTTP calls to
their AgentCore Runtime endpoints. Each specialist is invoked as a tool,
enabling the orchestrator to route queries to the most appropriate specialist.
"""

import json
import logging
import os
import sys
from typing import Dict, Any
from urllib.parse import quote

import boto3
import requests
from strands import tool

# Add patterns to path for shared utils
sys.path.append('/app/patterns')

from utils.ssm import get_ssm_parameter

logger = logging.getLogger(__name__)


def invoke_colorado(query: str, session_id: str, actor_id: str) -> str:
    """
    Invoke Colorado specialist agent.
    
    This function routes a query to the Colorado specialist agent, which is
    specialized for Colorado-specific queries and information.
    
    Args:
        query (str): The user's question or message to send to the Colorado agent.
        session_id (str): Session identifier for maintaining conversation context.
            The Colorado agent will apply its own session prefix.
        actor_id (str): User identifier for accessing long-term memory and
            maintaining consistent user identity across agents.
    
    Returns:
        str: The Colorado specialist agent's response as a string.
        
    Raises:
        ValueError: If required parameters are missing or invalid.
        RuntimeError: If the agent invocation fails due to service errors.
    """
    return _invoke_specialist(
        agent_name="colorado",
        query=query,
        session_id=session_id,
        actor_id=actor_id
    )


def invoke_umich(query: str, session_id: str, actor_id: str) -> str:
    """
    Invoke UMich specialist agent.
    
    This function routes a query to the University of Michigan specialist agent,
    which is specialized for UMich-specific queries and information.
    
    Args:
        query (str): The user's question or message to send to the UMich agent.
        session_id (str): Session identifier for maintaining conversation context.
            The UMich agent will apply its own session prefix.
        actor_id (str): User identifier for accessing long-term memory and
            maintaining consistent user identity across agents.
    
    Returns:
        str: The UMich specialist agent's response as a string.
        
    Raises:
        ValueError: If required parameters are missing or invalid.
        RuntimeError: If the agent invocation fails due to service errors.
    """
    return _invoke_specialist(
        agent_name="umich",
        query=query,
        session_id=session_id,
        actor_id=actor_id
    )


def invoke_coder(query: str, session_id: str, actor_id: str) -> str:
    """
    Invoke Coder specialist agent.
    
    This function routes a query to the Coder specialist agent, which is
    specialized for coding assistance and technical queries.
    
    Args:
        query (str): The user's question or message to send to the Coder agent.
        session_id (str): Session identifier for maintaining conversation context.
            The Coder agent will apply its own session prefix.
        actor_id (str): User identifier for accessing long-term memory and
            maintaining consistent user identity across agents.
    
    Returns:
        str: The Coder specialist agent's response as a string.
        
    Raises:
        ValueError: If required parameters are missing or invalid.
        RuntimeError: If the agent invocation fails due to service errors.
    """
    return _invoke_specialist(
        agent_name="coder",
        query=query,
        session_id=session_id,
        actor_id=actor_id
    )


def _invoke_specialist(
    agent_name: str,
    query: str,
    session_id: str,
    actor_id: str
) -> str:
    """
    Internal method to invoke a specialist agent's runtime endpoint.
    
    This function makes a direct HTTP call to the specialist agent's AgentCore
    Runtime endpoint. It retrieves the runtime ARN from SSM Parameter Store,
    constructs the appropriate API request, and handles the streaming response.
    
    The specialist agent will:
    - Apply its own session prefix (e.g., "colorado_", "umich_", "coder_")
    - Use the provided actor_id to access the user's long-term memory
    - Return its response which the orchestrator can include in its own response
    
    Args:
        agent_name (str): Name of specialist agent (colorado, umich, or coder).
        query (str): User query to process.
        session_id (str): Session identifier (will be prefixed by specialist).
        actor_id (str): User identifier for memory access.
        
    Returns:
        str: Specialist agent's response as a string.
        
    Raises:
        ValueError: If parameters are invalid or SSM parameter not found.
        RuntimeError: If the runtime invocation fails or returns an error.
    """
    # Validate input parameters
    if not agent_name or not isinstance(agent_name, str):
        raise ValueError("agent_name must be a non-empty string")
    
    if not query or not isinstance(query, str):
        raise ValueError("query must be a non-empty string")
    
    if not session_id or not isinstance(session_id, str):
        raise ValueError("session_id must be a non-empty string")
    
    if not actor_id or not isinstance(actor_id, str):
        raise ValueError("actor_id must be a non-empty string")
    
    # Validate agent_name is one of the known specialists
    valid_agents = ["colorado", "umich", "coder"]
    if agent_name not in valid_agents:
        raise ValueError(
            f"Invalid agent_name '{agent_name}'. Must be one of: {valid_agents}"
        )
    
    logger.info(
        "Invoking specialist agent '%s' for session '%s'",
        agent_name,
        session_id
    )
    logger.debug("Query: %s", query[:100] + "..." if len(query) > 100 else query)
    
    try:
        # Get stack name from environment
        stack_name = os.environ.get("STACK_NAME")
        if not stack_name:
            raise ValueError(
                "STACK_NAME environment variable not set. "
                "Cannot retrieve agent runtime ARN from SSM."
            )
        
        # Get AWS region from environment
        region = os.environ.get(
            "AWS_REGION",
            os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        )
        
        # Retrieve specialist runtime ARN from SSM Parameter Store
        # The CDK stack stores runtime ARNs in SSM during deployment
        ssm_parameter_name = f"/{stack_name}/agents/{agent_name}/runtime-arn"
        
        logger.info("Retrieving runtime ARN from SSM: %s", ssm_parameter_name)
        runtime_arn = get_ssm_parameter(parameter_name=ssm_parameter_name)
        
        if not runtime_arn:
            raise ValueError(
                f"Runtime ARN not found in SSM parameter: {ssm_parameter_name}"
            )
        
        logger.info("Retrieved runtime ARN: %s", runtime_arn)
        
        # Construct AgentCore Runtime API endpoint
        # Format: https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{arn}/invocations
        endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com"
        
        # URL-encode the runtime ARN for safe inclusion in the URL path
        escaped_arn = quote(runtime_arn, safe="")
        url = f"{endpoint}/runtimes/{escaped_arn}/invocations?qualifier=DEFAULT"
        
        logger.info("Invoking runtime at URL: %s", url)
        
        # Get AWS credentials for signing the request
        # The agent's IAM role must have bedrock-agentcore:InvokeRuntime permission
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if not credentials:
            raise RuntimeError(
                "Unable to retrieve AWS credentials. "
                "Ensure the agent's IAM role is properly configured."
            )
        
        # Prepare request headers
        # AgentCore Runtime expects:
        # - Authorization with AWS Signature V4
        # - Content-Type: application/json
        # - X-Amzn-Bedrock-AgentCore-Runtime-Session-Id for session tracking
        headers = {
            "Content-Type": "application/json",
            "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
        }
        
        # Prepare request payload
        # The specialist agent will receive this payload and process the query
        payload = {
            "prompt": query,
            "runtimeSessionId": session_id,
            "actorId": actor_id,
        }
        
        logger.debug("Request payload: %s", json.dumps(payload, indent=2))
        
        # Make HTTP POST request to AgentCore Runtime API
        # Use AWS SigV4 signing for authentication
        from botocore.auth import SigV4Auth
        from botocore.awsrequest import AWSRequest
        
        # Create AWS request for signing
        request = AWSRequest(
            method="POST",
            url=url,
            data=json.dumps(payload),
            headers=headers
        )
        
        # Sign the request with AWS Signature V4
        SigV4Auth(credentials, "bedrock-agentcore", region).add_auth(request)
        
        # Execute the signed request
        response = requests.post(
            url=url,
            headers=dict(request.headers),
            data=request.body,
            timeout=300,  # 5 minute timeout for long-running agent responses
            stream=True  # Enable streaming to handle SSE responses
        )
        
        # Check for HTTP errors
        if response.status_code != 200:
            error_message = f"Agent invocation failed: HTTP {response.status_code}"
            try:
                error_body = response.json()
                error_message += f" - {json.dumps(error_body)}"
            except Exception:
                error_message += f" - {response.text}"
            
            logger.error(error_message)
            raise RuntimeError(error_message)
        
        # Parse the streaming response
        # AgentCore Runtime returns Server-Sent Events (SSE) format
        # Each line starts with "data: " followed by JSON
        response_text = ""
        
        for line in response.iter_lines():
            if not line:
                continue
            
            # Decode bytes to string
            line_str = line.decode('utf-8').strip()
            
            # SSE format: "data: {json}"
            if line_str.startswith('data: '):
                try:
                    # Extract JSON after "data: " prefix
                    event_json = line_str[6:]  # Skip "data: " prefix
                    event = json.loads(event_json)
                    
                    # Extract text from the event
                    # The format may vary depending on the agent framework
                    # Common formats: {"data": "text"} or {"chunk": "text"}
                    if isinstance(event.get("data"), str):
                        response_text += event["data"]
                    elif isinstance(event.get("chunk"), str):
                        response_text += event["chunk"]
                    elif isinstance(event.get("text"), str):
                        response_text += event["text"]
                    
                except json.JSONDecodeError as e:
                    logger.warning(
                        "Failed to parse SSE event JSON: %s - Error: %s",
                        line_str,
                        str(e)
                    )
                    continue
        
        if not response_text:
            logger.warning(
                "No response text received from specialist agent '%s'",
                agent_name
            )
            return f"Specialist agent '{agent_name}' returned an empty response."
        
        logger.info(
            "Successfully received response from specialist agent '%s' "
            "(%d characters)",
            agent_name,
            len(response_text)
        )
        
        return response_text
        
    except ValueError as e:
        # Re-raise ValueError for parameter validation errors
        logger.error("Parameter validation error: %s", str(e))
        raise
    
    except Exception as e:
        # Catch all other exceptions and wrap in RuntimeError
        error_message = (
            f"Failed to invoke specialist agent '{agent_name}': {str(e)}"
        )
        logger.error(error_message, exc_info=True)
        raise RuntimeError(error_message) from e


class SpecialistInvocationTools:
    """
    Wrapper class for specialist invocation tools.
    
    This class provides @tool decorated methods that can invoke specialist agents.
    The session_id and actor_id are bound at initialization, so the LLM only needs
    to provide the query parameter.
    """
    
    def __init__(self, session_id: str, actor_id: str):
        """
        Initialize specialist invocation tools with context parameters.
        
        Args:
            session_id (str): Session identifier for maintaining conversation context.
            actor_id (str): User identifier for accessing long-term memory.
        """
        self.session_id = session_id
        self.actor_id = actor_id
    
    @tool
    def invoke_colorado(self, query: str) -> str:
        """
        Invoke Colorado specialist agent.
        
        This function routes a query to the Colorado specialist agent, which is
        specialized for Colorado-specific queries and information.
        
        Args:
            query (str): The user's question or message to send to the Colorado agent.
        
        Returns:
            str: The Colorado specialist agent's response as a string.
        """
        return _invoke_specialist(
            agent_name="colorado",
            query=query,
            session_id=self.session_id,
            actor_id=self.actor_id
        )
    
    @tool
    def invoke_umich(self, query: str) -> str:
        """
        Invoke UMich specialist agent.
        
        This function routes a query to the University of Michigan specialist agent,
        which is specialized for UMich-specific queries and information.
        
        Args:
            query (str): The user's question or message to send to the UMich agent.
        
        Returns:
            str: The UMich specialist agent's response as a string.
        """
        return _invoke_specialist(
            agent_name="umich",
            query=query,
            session_id=self.session_id,
            actor_id=self.actor_id
        )
    
    @tool
    def invoke_coder(self, query: str) -> str:
        """
        Invoke Coder specialist agent.
        
        This function routes a query to the Coder specialist agent, which is
        specialized for coding assistance and technical queries.
        
        Args:
            query (str): The user's question or message to send to the Coder agent.
        
        Returns:
            str: The Coder specialist agent's response as a string.
        """
        return _invoke_specialist(
            agent_name="coder",
            query=query,
            session_id=self.session_id,
            actor_id=self.actor_id
        )
