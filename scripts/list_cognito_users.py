#!/usr/bin/env python3
"""
List Cognito users in the user pool

This script lists all users in the Cognito user pool to help identify
existing test users.

Usage:
    python scripts/list_cognito_users.py
"""

import sys
from pathlib import Path

import boto3

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import get_ssm_params, get_stack_config, print_msg, print_section


def list_cognito_users() -> None:
    """List all users in the Cognito user pool."""
    print_section("Listing Cognito Users")

    # Get stack configuration
    print_msg("Fetching stack configuration...")
    config = get_stack_config()
    stack_name = config["stack_name"]

    # Get user pool ID from SSM
    print_msg("Fetching Cognito User Pool ID...")
    params = get_ssm_params(stack_name, "cognito-user-pool-id")
    user_pool_id = params["cognito-user-pool-id"]

    print_msg(f"User Pool ID: {user_pool_id}")

    # List users
    cognito = boto3.client("cognito-idp")

    try:
        print_msg("\nFetching users...")
        response = cognito.list_users(UserPoolId=user_pool_id)

        users = response.get("Users", [])

        if not users:
            print_msg("No users found in the user pool", "info")
            print_section("How to Create a User")
            print(
                """
You can create a user in one of two ways:

1. Via AWS Console:
   - Go to AWS Cognito Console
   - Select your user pool
   - Click "Users" tab
   - Click "Create user"
   - Fill in username, email, and temporary password
   - Mark email as verified

2. Via AWS CLI:
   aws cognito-idp admin-create-user \\
       --user-pool-id {user_pool_id} \\
       --username testuser \\
       --user-attributes Name=email,Value=test@example.com Name=email_verified,Value=true \\
       --temporary-password TempPassword123! \\
       --message-action SUPPRESS

   Then set a permanent password:
   aws cognito-idp admin-set-user-password \\
       --user-pool-id {user_pool_id} \\
       --username testuser \\
       --password MyPassword123! \\
       --permanent
""".format(
                    user_pool_id=user_pool_id
                )
            )
            return

        print_msg(f"Found {len(users)} user(s):", "success")
        print()

        for user in users:
            username = user.get("Username")
            status = user.get("UserStatus")
            enabled = user.get("Enabled", False)
            created = user.get("UserCreateDate")

            # Extract email from attributes
            email = None
            email_verified = False
            for attr in user.get("Attributes", []):
                if attr["Name"] == "email":
                    email = attr["Value"]
                elif attr["Name"] == "email_verified":
                    email_verified = attr["Value"].lower() == "true"

            print(f"Username: {username}")
            print(f"  Email: {email}")
            print(f"  Status: {status}")
            print(f"  Enabled: {enabled}")
            print(f"  Email Verified: {email_verified}")
            print(f"  Created: {created}")
            print()

        print_section("Testing the /api/agents Endpoint")
        print("To test the /api/agents endpoint with one of these users:")
        print()
        print("  python scripts/test_agents_endpoint.py <username> <password>")
        print()
        print("Example:")
        print("  python scripts/test_agents_endpoint.py testuser MyPassword123!")

    except Exception as e:
        print_msg(f"Error listing users: {e}", "error")
        sys.exit(1)


def main():
    """Main entry point."""
    list_cognito_users()


if __name__ == "__main__":
    main()
