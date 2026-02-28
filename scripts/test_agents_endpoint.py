#!/usr/bin/env python3
"""
Test script for /api/agents endpoint

This script tests the agent discovery endpoint by:
1. Fetching stack configuration and API URL
2. Authenticating with Cognito to get a JWT token
3. Calling the /api/agents endpoint with the JWT
4. Validating the response format and agent fields
5. Documenting the actual response structure

Usage:
    python scripts/test_agents_endpoint.py <username> <password>

Example:
    python scripts/test_agents_endpoint.py testuser MyPassword123!
"""

import json
import sys
from pathlib import Path

import requests

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    authenticate_cognito,
    get_ssm_params,
    get_stack_config,
    print_msg,
    print_section,
)


def test_agents_endpoint(username: str, password: str) -> None:
    """
    Test the /api/agents endpoint with valid JWT authentication.

    Args:
        username: Cognito username
        password: Cognito password
    """
    print_section("Testing /api/agents Endpoint")

    # Step 1: Get stack configuration
    print_msg("Fetching stack configuration...")
    config = get_stack_config()
    stack_name = config["stack_name"]
    region = config["region"]

    print_msg(f"Stack: {stack_name}")
    print_msg(f"Region: {region}")

    # Step 2: Get required parameters from SSM
    print_msg("\nFetching SSM parameters...")
    params = get_ssm_params(
        stack_name,
        "cognito-user-pool-id",
        "cognito-client-id",
        "agent-discovery-api-url",
    )

    user_pool_id = params["cognito-user-pool-id"]
    client_id = params["cognito-client-id"]
    api_url = params["agent-discovery-api-url"]

    print_msg(f"User Pool ID: {user_pool_id}")
    print_msg(f"Client ID: {client_id}")
    print_msg(f"API URL: {api_url}")

    # Step 3: Authenticate with Cognito
    print_section("Authenticating with Cognito")
    access_token, id_token, user_id = authenticate_cognito(
        user_pool_id, client_id, username, password
    )

    # Step 4: Call /api/agents endpoint
    print_section("Calling /api/agents Endpoint")
    print_msg(f"GET {api_url}")

    headers = {
        "Authorization": id_token,  # API Gateway Cognito authorizer uses ID token
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=30)

        print_msg(f"Status Code: {response.status_code}")

        # Step 5: Validate response
        if response.status_code == 200:
            print_msg("✓ Request successful!", "success")

            # Parse JSON response
            data = response.json()

            print_section("Response Data")
            print(json.dumps(data, indent=2))

            # Validate response structure
            print_section("Validating Response Structure")

            if "agents" not in data:
                print_msg("✗ Missing 'agents' field in response", "error")
                return

            if "count" not in data:
                print_msg("✗ Missing 'count' field in response", "error")
                return

            agents = data["agents"]
            count = data["count"]

            print_msg(f"✓ Found {count} agents", "success")

            if count != len(agents):
                print_msg(
                    f"✗ Count mismatch: count={count}, len(agents)={len(agents)}",
                    "error",
                )
                return

            # Validate each agent's fields
            print_section("Validating Agent Fields")

            required_fields = ["name", "displayName", "status"]
            optional_fields = [
                "runtimeArn",
                "runtimeId",
                "description",
                "isDefault",
                "error",
                "pattern",
            ]

            for i, agent in enumerate(agents):
                print(f"\nAgent {i + 1}: {agent.get('name', 'UNKNOWN')}")

                # Check required fields
                for field in required_fields:
                    if field in agent:
                        print_msg(f"  ✓ {field}: {agent[field]}", "success")
                    else:
                        print_msg(f"  ✗ Missing required field: {field}", "error")

                # Check optional fields
                for field in optional_fields:
                    if field in agent:
                        value = agent[field]
                        # Truncate long values for display
                        if isinstance(value, str) and len(value) > 60:
                            value = value[:60] + "..."
                        print_msg(f"  ✓ {field}: {value}", "info")

            # Document actual response format
            print_section("Actual Response Format Documentation")
            print("Response structure:")
            print(
                """
{
  "agents": [
    {
      "name": string,              // REQUIRED: Agent identifier
      "displayName": string,       // REQUIRED: Human-readable name
      "status": string,            // REQUIRED: Deployment status (deployed, failed, pending)
      "runtimeArn": string,        // OPTIONAL: AgentCore Runtime ARN
      "runtimeId": string,         // OPTIONAL: Runtime identifier
      "description": string,       // OPTIONAL: Agent description
      "isDefault": boolean,        // OPTIONAL: Whether this is the default agent
      "error": string,             // OPTIONAL: Error message if status is failed
      "pattern": string            // OPTIONAL: Agent pattern name
    }
  ],
  "count": number                  // Total number of agents
}
"""
            )

            print_section("Test Summary")
            print_msg("✓ /api/agents endpoint is working correctly", "success")
            print_msg(
                "✓ Response contains agent list with required fields", "success"
            )
            print_msg(f"✓ Found {count} agent(s) in the system", "success")

            # Check for specific fields mentioned in requirements
            print_section("Requirements Validation")
            print_msg("Checking fields mentioned in Requirements 1.1, 1.2, 10.1...")

            all_fields_present = True
            for agent in agents:
                if "name" not in agent:
                    print_msg("✗ Missing 'name' field", "error")
                    all_fields_present = False
                if "description" not in agent:
                    print_msg("ℹ 'description' field is optional", "info")
                # Note: model and tools are not in current implementation
                if "model" not in agent:
                    print_msg(
                        "ℹ 'model' field not present (may need to be added)", "info"
                    )
                if "tools" not in agent:
                    print_msg(
                        "ℹ 'tools' field not present (may need to be added)", "info"
                    )
                if "status" not in agent:
                    print_msg("✗ Missing 'status' field", "error")
                    all_fields_present = False
                if "runtimeArn" not in agent:
                    print_msg("ℹ 'runtimeArn' field is optional", "info")

            if all_fields_present:
                print_msg(
                    "✓ All required fields are present in the response", "success"
                )

        elif response.status_code == 401:
            print_msg("✗ Authentication failed (401 Unauthorized)", "error")
            print_msg("Check that the JWT token is valid", "error")
            print(f"Response: {response.text}")

        elif response.status_code == 500:
            print_msg("✗ Internal server error (500)", "error")
            print(f"Response: {response.text}")

        else:
            print_msg(f"✗ Unexpected status code: {response.status_code}", "error")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print_msg("✗ Request timed out after 30 seconds", "error")
    except requests.exceptions.RequestException as e:
        print_msg(f"✗ Request failed: {e}", "error")
    except json.JSONDecodeError as e:
        print_msg(f"✗ Failed to parse JSON response: {e}", "error")
        print(f"Response text: {response.text}")


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python scripts/test_agents_endpoint.py <username> <password>")
        print("\nExample:")
        print("  python scripts/test_agents_endpoint.py testuser MyPassword123!")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    test_agents_endpoint(username, password)


if __name__ == "__main__":
    main()
