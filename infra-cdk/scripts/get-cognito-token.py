#!/usr/bin/env python3
"""
Helper Script: Get Cognito JWT Access Token

This script retrieves a JWT access token from AWS Cognito for authenticating
with AgentCore Runtime APIs.

The script:
1. Reads Cognito configuration from SSM parameters (User Pool ID, Client ID)
2. Prompts for username/password or reads from environment variables
3. Authenticates with Cognito using boto3 cognito-idp client
4. Returns the AccessToken (JWT access token)
5. Handles errors gracefully with clear messages

Usage:
    # Interactive (prompts for credentials)
    python infra-cdk/scripts/get-cognito-token.py

    # With command line arguments
    python infra-cdk/scripts/get-cognito-token.py --username user@example.com --password mypassword

    # With environment variables
    export COGNITO_USERNAME=user@example.com
    export COGNITO_PASSWORD=mypassword
    python infra-cdk/scripts/get-cognito-token.py

    # Use in scripts
    export AGENTCORE_ACCESS_TOKEN=$(python infra-cdk/scripts/get-cognito-token.py --username user@example.com --password mypassword)

Environment Variables:
    AWS_DEFAULT_REGION: AWS region (default: us-east-1)
    AWS_PROFILE: AWS profile to use (optional)
    COGNITO_USERNAME: Cognito username (optional, will prompt if not provided)
    COGNITO_PASSWORD: Cognito password (optional, will prompt if not provided)

Requirements:
    - boto3
    - pyyaml
    - AWS credentials configured
    - CDK stack must be deployed with Cognito User Pool
"""

import argparse
import getpass
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import boto3
import yaml
from botocore.exceptions import ClientError

# Configure logging to stderr so stdout only contains the token
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
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


def get_cognito_config(ssm_client, stack_name: str) -> tuple[str, str]:
    """
    Retrieve Cognito User Pool ID and Client ID from SSM parameters.

    Args:
        ssm_client: Boto3 SSM client
        stack_name: Stack name base

    Returns:
        Tuple of (user_pool_id, client_id)

    Raises:
        ClientError: If SSM parameters cannot be retrieved
        ValueError: If parameters are not found
    """
    user_pool_param = f"/{stack_name}/cognito-user-pool-id"
    client_id_param = f"/{stack_name}/cognito-user-pool-client-id"
    
    try:
        # Get both parameters in a single call
        response = ssm_client.get_parameters(
            Names=[user_pool_param, client_id_param],
            WithDecryption=False
        )
        
        if len(response['Parameters']) != 2:
            missing = []
            found_params = {p['Name'] for p in response['Parameters']}
            if user_pool_param not in found_params:
                missing.append(user_pool_param)
            if client_id_param not in found_params:
                missing.append(client_id_param)
            
            raise ValueError(
                f"Cognito configuration not found in SSM. Missing parameters: {', '.join(missing)}\n"
                f"Make sure the CDK stack is deployed and Cognito is configured."
            )
        
        # Extract values
        params = {p['Name']: p['Value'] for p in response['Parameters']}
        user_pool_id = params[user_pool_param]
        client_id = params[client_id_param]
        
        logger.info(f"Retrieved Cognito configuration from SSM")
        logger.debug(f"User Pool ID: {user_pool_id}")
        logger.debug(f"Client ID: {client_id}")
        
        return user_pool_id, client_id
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        
        raise ClientError(
            {
                'Error': {
                    'Code': error_code,
                    'Message': f"Failed to retrieve Cognito configuration from SSM: {error_msg}"
                }
            },
            'GetParameters'
        )


def get_credentials(username: Optional[str], password: Optional[str]) -> tuple[str, str]:
    """
    Get username and password from arguments, environment variables, or user input.

    Priority:
    1. Command line arguments
    2. Environment variables
    3. Interactive prompt

    Args:
        username: Username from command line (optional)
        password: Password from command line (optional)

    Returns:
        Tuple of (username, password)
    """
    # Get username
    if username:
        final_username = username
    elif os.environ.get('COGNITO_USERNAME'):
        final_username = os.environ['COGNITO_USERNAME']
        logger.info("Using username from COGNITO_USERNAME environment variable")
    else:
        final_username = input("Cognito Username: ")
    
    # Get password
    if password:
        final_password = password
    elif os.environ.get('COGNITO_PASSWORD'):
        final_password = os.environ['COGNITO_PASSWORD']
        logger.info("Using password from COGNITO_PASSWORD environment variable")
    else:
        final_password = getpass.getpass("Cognito Password: ")
    
    return final_username, final_password


def authenticate_with_cognito(
    cognito_client,
    client_id: str,
    username: str,
    password: str
) -> str:
    """
    Authenticate with Cognito and retrieve JWT access token.

    Uses the USER_PASSWORD_AUTH flow to authenticate with username and password.

    Args:
        cognito_client: Boto3 Cognito Identity Provider client
        client_id: Cognito User Pool Client ID
        username: Cognito username
        password: Cognito password

    Returns:
        JWT AccessToken (access token)

    Raises:
        ClientError: If authentication fails
        ValueError: If token is not returned
    """
    try:
        logger.info(f"Authenticating user: {username}")
        
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        # Check if authentication was successful
        if 'AuthenticationResult' not in response:
            raise ValueError(
                "Authentication failed: No AuthenticationResult in response. "
                "This may indicate that additional challenges are required (MFA, password change, etc.)"
            )
        
        auth_result = response['AuthenticationResult']
        
        # Get AccessToken (this is the JWT access token for AgentCore)
        # Try AccessToken first, fall back to IdToken if not available
        if 'AccessToken' in auth_result:
            access_token = auth_result['AccessToken']
        elif 'IdToken' in auth_result:
            access_token = auth_result['IdToken']
            logger.warning("Using IdToken as AccessToken not available")
        else:
            raise ValueError("Authentication failed: No AccessToken or IdToken in response")
        
        logger.info("✓ Authentication successful")
        
        return access_token
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        
        # Provide user-friendly error messages
        if error_code == 'NotAuthorizedException':
            raise ClientError(
                {
                    'Error': {
                        'Code': error_code,
                        'Message': "Authentication failed: Incorrect username or password"
                    }
                },
                'InitiateAuth'
            )
        elif error_code == 'UserNotFoundException':
            raise ClientError(
                {
                    'Error': {
                        'Code': error_code,
                        'Message': f"Authentication failed: User '{username}' not found"
                    }
                },
                'InitiateAuth'
            )
        elif error_code == 'UserNotConfirmedException':
            raise ClientError(
                {
                    'Error': {
                        'Code': error_code,
                        'Message': f"Authentication failed: User '{username}' is not confirmed. Please verify your email."
                    }
                },
                'InitiateAuth'
            )
        elif error_code == 'PasswordResetRequiredException':
            raise ClientError(
                {
                    'Error': {
                        'Code': error_code,
                        'Message': f"Authentication failed: Password reset required for user '{username}'"
                    }
                },
                'InitiateAuth'
            )
        else:
            raise ClientError(
                {
                    'Error': {
                        'Code': error_code,
                        'Message': f"Authentication failed: {error_msg}"
                    }
                },
                'InitiateAuth'
            )


def main():
    """
    Main execution function.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Get Cognito JWT access token for AgentCore Runtime authentication'
    )
    parser.add_argument(
        '--username',
        type=str,
        help='Cognito username (optional, will prompt if not provided)'
    )
    parser.add_argument(
        '--password',
        type=str,
        help='Cognito password (optional, will prompt if not provided)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Load configuration
        config = load_config()
        stack_name = config['stack_name_base']
        logger.info(f"Stack name: {stack_name}")
        
        # Initialize AWS clients
        region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        logger.info(f"AWS Region: {region}")
        
        ssm_client = boto3.client('ssm', region_name=region)
        cognito_client = boto3.client('cognito-idp', region_name=region)
        
        # Get Cognito configuration from SSM
        user_pool_id, client_id = get_cognito_config(ssm_client, stack_name)
        
        # Get credentials
        username, password = get_credentials(args.username, args.password)
        
        # Authenticate and get token
        token = authenticate_with_cognito(cognito_client, client_id, username, password)
        
        # Output token to stdout (so it can be captured by scripts)
        print(token)
        
        logger.info("✓ Token retrieved successfully")
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except ClientError as e:
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"AWS error: {error_msg}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
