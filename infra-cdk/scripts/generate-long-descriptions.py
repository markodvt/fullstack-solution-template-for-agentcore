#!/usr/bin/env python3
"""
Post-Deployment Script: Generate Long Descriptions for Agents

This script runs after CDK deployment to generate user-friendly long descriptions
for each agent by invoking the default agent with the agent's docstring and system prompt.

The script:
1. Reads stack configuration from config.yaml
2. Lists all agents from SSM parameters
3. For each agent:
   - Fetches source code from S3
   - Extracts docstring and system prompt
   - Invokes the default agent via HTTP to generate a 2-3 sentence description
   - Stores the description in SSM parameter: /{stack}/agents/{agent_name}/long-description

Usage:
    python infra-cdk/scripts/generate-long-descriptions.py

Environment Variables:
    AWS_DEFAULT_REGION: AWS region (default: us-east-1)
    AWS_PROFILE: AWS profile to use (optional)
    AGENTCORE_ACCESS_TOKEN: JWT access token for AgentCore Runtime authentication (required)

Requirements:
    - boto3
    - pyyaml
    - requests
    - AWS credentials configured
    - CDK stack must be deployed
    - Valid JWT token for AgentCore Runtime authentication
"""

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import quote

import boto3
import requests
import yaml
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config() -> Dict:
    """
    Load configuration from config.yaml.

    Returns:
        Dictionary containing stack configuration

    Raises:
        FileNotFoundError: If config.yaml is not found
        yaml.YAMLError: If config.yaml is malformed
    """
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if not config or 'stack_name_base' not in config:
        raise ValueError("config.yaml must contain 'stack_name_base'")
    
    return config


def extract_docstring(source_code: str) -> str:
    """
    Extract the module-level docstring from Python source code.

    Args:
        source_code: Python source code as string

    Returns:
        Extracted docstring or empty string if not found
    """
    # Match triple-quoted strings at the start of the file (after optional comments)
    # Try double quotes first
    pattern = r'^\s*(?:#.*\n)*\s*"""(.*?)"""'
    match = re.search(pattern, source_code, re.DOTALL | re.MULTILINE)
    
    if match:
        return match.group(1).strip()
    
    # Try single quotes
    pattern = r"^\s*(?:#.*\n)*\s*'''(.*?)'''"
    match = re.search(pattern, source_code, re.DOTALL | re.MULTILINE)
    
    if match:
        return match.group(1).strip()
    
    return ""


def extract_system_prompt(source_code: str) -> str:
    """
    Extract the system_prompt variable from Python source code.

    Looks for system_prompt variable assignments with triple-quoted strings.

    Args:
        source_code: Python source code as string

    Returns:
        Extracted system prompt or empty string if not found
    """
    # Match system_prompt = """..."""
    pattern = r'system_prompt\s*=\s*"""(.*?)"""'
    match = re.search(pattern, source_code, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # Try single quotes: system_prompt = '''...'''
    pattern = r"system_prompt\s*=\s*'''(.*?)'''"
    match = re.search(pattern, source_code, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    return ""


def fetch_source_code_from_s3(
    s3_client,
    bucket: str,
    key: str
) -> Optional[str]:
    """
    Fetch agent source code from S3.

    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        Source code as string, or None if fetch fails
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        source_code = response['Body'].read().decode('utf-8')
        return source_code
    except ClientError as e:
        logger.warning(f"Failed to fetch source code from s3://{bucket}/{key}: {e}")
        return None


def get_agent_source_code(
    ssm_client,
    s3_client,
    stack_name: str,
    agent_name: str
) -> Optional[str]:
    """
    Get agent source code by fetching S3 URL from SSM and downloading from S3.

    Args:
        ssm_client: Boto3 SSM client
        s3_client: Boto3 S3 client
        stack_name: Stack name base
        agent_name: Agent name

    Returns:
        Source code as string, or None if not found
    """
    param_name = f"/{stack_name}/agents/{agent_name}/source-code-url"
    
    try:
        response = ssm_client.get_parameter(Name=param_name)
        s3_url = response['Parameter']['Value']
        
        # Parse S3 URL: s3://bucket/key
        if not s3_url.startswith('s3://'):
            logger.warning(f"Invalid S3 URL format for {agent_name}: {s3_url}")
            return None
        
        s3_path = s3_url[5:]  # Remove 's3://'
        parts = s3_path.split('/', 1)
        
        if len(parts) != 2:
            logger.warning(f"Invalid S3 URL format for {agent_name}: {s3_url}")
            return None
        
        bucket, key = parts
        return fetch_source_code_from_s3(s3_client, bucket, key)
        
    except ClientError as e:
        logger.warning(f"Failed to get source code URL for {agent_name}: {e}")
        return None


def get_default_agent_runtime_arn(
    ssm_client,
    stack_name: str
) -> Optional[str]:
    """
    Get the Runtime ARN of the default agent.

    Args:
        ssm_client: Boto3 SSM client
        stack_name: Stack name base

    Returns:
        Runtime ARN of default agent, or None if not found
    """
    # List all agents and find the default one
    agents_path = f"/{stack_name}/agents"
    
    try:
        # Get all parameters under agents path
        paginator = ssm_client.get_paginator('get_parameters_by_path')
        page_iterator = paginator.paginate(
            Path=agents_path,
            Recursive=True,
            WithDecryption=False
        )
        
        # Find agent with is-default=true
        for page in page_iterator:
            for param in page['Parameters']:
                if param['Name'].endswith('/is-default') and param['Value'].lower() == 'true':
                    # Extract agent name from parameter path
                    # Format: /{stack}/agents/{agent_name}/is-default
                    path_parts = param['Name'].split('/')
                    if len(path_parts) >= 4:
                        agent_name = path_parts[3]
                        
                        # Get runtime ARN for this agent
                        runtime_arn_param = f"/{stack_name}/agents/{agent_name}/runtime-arn"
                        runtime_response = ssm_client.get_parameter(Name=runtime_arn_param)
                        return runtime_response['Parameter']['Value']
        
        logger.error("No default agent found in SSM parameters")
        return None
        
    except ClientError as e:
        logger.error(f"Failed to find default agent: {e}")
        return None


def get_jwt_token() -> str:
    """
    Get JWT access token for authenticating with AgentCore Runtime.

    First checks if AGENTCORE_ACCESS_TOKEN environment variable is set.
    If not, automatically calls the get-cognito-token.py helper script to retrieve
    a token from Cognito using credentials from environment variables or interactive prompt.

    Returns:
        JWT access token

    Raises:
        RuntimeError: If token retrieval fails
    """
    # Check if token is already provided via environment variable
    token = os.environ.get('AGENTCORE_ACCESS_TOKEN')
    if token:
        logger.info("Using AGENTCORE_ACCESS_TOKEN from environment variable")
        return token
    
    # Token not set, try to get it automatically using the helper script
    logger.info("AGENTCORE_ACCESS_TOKEN not set, attempting to retrieve token from Cognito...")
    
    try:
        # Get path to the helper script
        script_dir = Path(__file__).parent
        helper_script = script_dir / "get-cognito-token.py"
        
        if not helper_script.exists():
            raise RuntimeError(
                f"Helper script not found: {helper_script}\n"
                "Please ensure get-cognito-token.py exists in the scripts directory."
            )
        
        # Call the helper script to get the token
        # The script will use environment variables or prompt for credentials
        result = subprocess.run(
            [sys.executable, str(helper_script)],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            # Helper script failed, show its error output
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(
                f"Failed to retrieve Cognito token:\n{error_msg}\n\n"
                "You can also manually set the AGENTCORE_ACCESS_TOKEN environment variable."
            )
        
        # Extract token from stdout
        token = result.stdout.strip()
        
        if not token:
            raise RuntimeError(
                "Helper script returned empty token.\n"
                "Please check your Cognito credentials and try again."
            )
        
        logger.info("✓ Successfully retrieved token from Cognito")
        return token
        
    except subprocess.SubprocessError as e:
        raise RuntimeError(
            f"Failed to execute get-cognito-token.py helper script: {e}\n"
            "You can manually set the AGENTCORE_ACCESS_TOKEN environment variable instead."
        )
    except Exception as e:
        raise RuntimeError(
            f"Unexpected error retrieving Cognito token: {e}\n"
            "You can manually set the AGENTCORE_ACCESS_TOKEN environment variable instead."
        )


def invoke_agent_for_description(
    region: str,
    runtime_arn: str,
    docstring: str,
    system_prompt: str,
    agent_name: str
) -> Optional[str]:
    """
    Invoke the default agent to generate a long description via HTTP request.

    Args:
        region: AWS region
        runtime_arn: Runtime ARN of the default agent
        docstring: Agent's docstring
        system_prompt: Agent's system prompt
        agent_name: Name of the agent (for context)

    Returns:
        Generated description, or None if invocation fails
    """
    # Construct prompt for the agent
    prompt = f"""Based on this agent's docstring and system prompt, generate a 2-3 sentence user-friendly description that explains what this agent does and what makes it unique. Focus on capabilities and personality.

Agent Name: {agent_name}

Docstring:
{docstring}

System Prompt:
{system_prompt}

Generate a concise, user-friendly description (2-3 sentences):"""

    try:
        # Get JWT access token
        access_token = get_jwt_token()
        
        # Construct AgentCore Runtime API endpoint
        endpoint = f"https://bedrock-agentcore.{region}.amazonaws.com"
        
        # URL-encode the runtime ARN for safe inclusion in the URL path
        escaped_arn = quote(runtime_arn, safe="")
        url = f"{endpoint}/runtimes/{escaped_arn}/invocations?qualifier=DEFAULT"
        
        # Generate session ID for this invocation
        session_id = f"description-gen-{agent_name}"
        
        # Prepare request headers with JWT Bearer authentication
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
        }
        
        # Prepare request payload
        payload = {
            "prompt": prompt,
            "runtimeSessionId": session_id,
            "actorId": "system",  # Use system as actor for script invocations
        }
        
        logger.debug(f"Invoking agent at URL: {url}")
        
        # Make HTTP POST request to AgentCore Runtime API
        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
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
            return None
        
        # Parse the streaming response (SSE format)
        # Each line starts with "data: " followed by JSON
        description_parts = []
        
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
                    # Common formats: {"data": "text"} or {"chunk": "text"} or {"text": "text"}
                    if isinstance(event.get("data"), str):
                        description_parts.append(event["data"])
                    elif isinstance(event.get("chunk"), str):
                        description_parts.append(event["chunk"])
                    elif isinstance(event.get("text"), str):
                        description_parts.append(event["text"])
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse SSE event JSON: {line_str} - Error: {e}")
                    continue
        
        description = ''.join(description_parts).strip()
        
        if not description:
            logger.warning(f"Agent returned empty description for {agent_name}")
            return None
        
        return description
        
    except RuntimeError as e:
        logger.error(f"Authentication error: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed for {agent_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error invoking agent for {agent_name}: {e}")
        return None


def store_long_description(
    ssm_client,
    stack_name: str,
    agent_name: str,
    description: str
) -> bool:
    """
    Store the generated long description in SSM parameter.

    Args:
        ssm_client: Boto3 SSM client
        stack_name: Stack name base
        agent_name: Agent name
        description: Generated description

    Returns:
        True if successful, False otherwise
    """
    param_name = f"/{stack_name}/agents/{agent_name}/long-description"
    
    try:
        ssm_client.put_parameter(
            Name=param_name,
            Value=description,
            Type='String',
            Overwrite=True,
            Description=f"Generated long description for {agent_name}"
        )
        logger.info(f"✓ Stored long description for {agent_name}")
        return True
        
    except ClientError as e:
        logger.error(f"Failed to store long description for {agent_name}: {e}")
        return False


def list_agents(ssm_client, stack_name: str) -> list:
    """
    List all agent names from SSM parameters.

    Args:
        ssm_client: Boto3 SSM client
        stack_name: Stack name base

    Returns:
        List of agent names
    """
    agents_path = f"/{stack_name}/agents"
    agent_names = set()
    
    try:
        paginator = ssm_client.get_paginator('get_parameters_by_path')
        page_iterator = paginator.paginate(
            Path=agents_path,
            Recursive=True,
            WithDecryption=False
        )
        
        for page in page_iterator:
            for param in page['Parameters']:
                # Extract agent name from parameter path
                # Format: /{stack}/agents/{agent_name}/{param_name}
                path_parts = param['Name'].split('/')
                if len(path_parts) >= 4:
                    agent_name = path_parts[3]
                    agent_names.add(agent_name)
        
        return sorted(list(agent_names))
        
    except ClientError as e:
        logger.error(f"Failed to list agents: {e}")
        return []


def main():
    """
    Main execution function.
    """
    logger.info("Starting long description generation...")
    
    # Load configuration
    try:
        config = load_config()
        stack_name = config['stack_name_base']
        logger.info(f"Stack name: {stack_name}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Initialize AWS clients
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    logger.info(f"AWS Region: {region}")
    
    ssm_client = boto3.client('ssm', region_name=region)
    s3_client = boto3.client('s3', region_name=region)
    
    # Get default agent Runtime ARN
    logger.info("Finding default agent...")
    default_runtime_arn = get_default_agent_runtime_arn(ssm_client, stack_name)
    
    if not default_runtime_arn:
        logger.error("Could not find default agent. Exiting.")
        sys.exit(1)
    
    logger.info(f"Default agent Runtime ARN: {default_runtime_arn}")
    
    # List all agents
    logger.info("Listing agents...")
    agents = list_agents(ssm_client, stack_name)
    
    if not agents:
        logger.warning("No agents found. Nothing to do.")
        sys.exit(0)
    
    logger.info(f"Found {len(agents)} agents: {', '.join(agents)}")
    
    # Process each agent
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for agent_name in agents:
        logger.info(f"\nProcessing agent: {agent_name}")
        
        # Fetch source code
        source_code = get_agent_source_code(ssm_client, s3_client, stack_name, agent_name)
        
        if not source_code:
            logger.warning(f"⚠ Skipping {agent_name}: Could not fetch source code")
            skip_count += 1
            continue
        
        # Extract docstring and system prompt
        docstring = extract_docstring(source_code)
        system_prompt = extract_system_prompt(source_code)
        
        if not docstring and not system_prompt:
            logger.warning(f"⚠ Skipping {agent_name}: No docstring or system prompt found")
            skip_count += 1
            continue
        
        logger.info(f"  Extracted docstring: {len(docstring)} chars")
        logger.info(f"  Extracted system prompt: {len(system_prompt)} chars")
        
        # Invoke agent to generate description
        logger.info(f"  Invoking default agent to generate description...")
        description = invoke_agent_for_description(
            region,
            default_runtime_arn,
            docstring,
            system_prompt,
            agent_name
        )
        
        if not description:
            logger.error(f"✗ Failed to generate description for {agent_name}")
            error_count += 1
            continue
        
        logger.info(f"  Generated description: {description[:100]}...")
        
        # Store description in SSM
        if store_long_description(ssm_client, stack_name, agent_name, description):
            success_count += 1
        else:
            error_count += 1
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total agents: {len(agents)}")
    logger.info(f"✓ Successfully generated: {success_count}")
    logger.info(f"⚠ Skipped: {skip_count}")
    logger.info(f"✗ Errors: {error_count}")
    logger.info("="*60)
    
    if error_count > 0:
        sys.exit(1)
    else:
        logger.info("\n✓ Long description generation complete!")
        sys.exit(0)


if __name__ == "__main__":
    main()
