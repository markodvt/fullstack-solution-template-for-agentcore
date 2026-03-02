# Post-Deployment Scripts

This directory contains scripts that should be run after CDK deployment to perform additional setup and configuration tasks.

## Scripts

### get-cognito-token.py

Helper script that retrieves a JWT access token from AWS Cognito for authenticating with AgentCore Runtime APIs.

**Purpose:**
- Authenticates with Cognito using username and password
- Returns JWT IdToken for use with AgentCore Runtime
- Can be used standalone or called automatically by other scripts

**When to use:**
- When you need to authenticate with AgentCore Runtime APIs
- Automatically called by `generate-long-descriptions.py` if token is not set
- Can be used in shell scripts to export tokens

**Prerequisites:**
- CDK stack must be deployed with Cognito User Pool
- AWS credentials configured
- Python 3.8+ installed
- Valid Cognito user account

**Installation:**

```bash
# Install required packages
pip install -r infra-cdk/scripts/requirements.txt
```

**Usage:**

```bash
# Interactive (prompts for credentials)
python infra-cdk/scripts/get-cognito-token.py

# With command line arguments
python infra-cdk/scripts/get-cognito-token.py --username user@example.com --password mypassword

# With environment variables
export COGNITO_USERNAME=user@example.com
export COGNITO_PASSWORD=mypassword
python infra-cdk/scripts/get-cognito-token.py

# Use in scripts to export token
export AGENTCORE_ACCESS_TOKEN=$(python infra-cdk/scripts/get-cognito-token.py --username user@example.com --password mypassword)

# Enable debug logging
python infra-cdk/scripts/get-cognito-token.py --debug
```

**Environment Variables:**
- `AWS_DEFAULT_REGION`: AWS region (default: us-east-1)
- `AWS_PROFILE`: AWS profile to use (optional)
- `COGNITO_USERNAME`: Cognito username (optional, will prompt if not provided)
- `COGNITO_PASSWORD`: Cognito password (optional, will prompt if not provided)

**What it does:**

1. Reads Cognito configuration from SSM parameters:
   - `/{stack_name}/cognito/user-pool-id`
   - `/{stack_name}/cognito/client-id`
2. Gets credentials from command line, environment variables, or interactive prompt
3. Authenticates with Cognito using `USER_PASSWORD_AUTH` flow
4. Returns the JWT IdToken to stdout
5. Logs progress and errors to stderr

**Output:**

The script outputs the JWT token to stdout (so it can be captured) and logs to stderr:

```
2024-01-15 10:30:00 - INFO - Stack name: marodon-fast
2024-01-15 10:30:00 - INFO - AWS Region: us-east-1
2024-01-15 10:30:01 - INFO - Retrieved Cognito configuration from SSM
2024-01-15 10:30:01 - INFO - Authenticating user: user@example.com
2024-01-15 10:30:02 - INFO - ✓ Authentication successful
2024-01-15 10:30:02 - INFO - ✓ Token retrieved successfully
eyJraWQiOiJxxx...xxx (token output to stdout)
```

**Error Handling:**

The script provides user-friendly error messages for common issues:
- Incorrect username or password
- User not found
- User not confirmed (email verification required)
- Password reset required
- Missing Cognito configuration in SSM

**Security Notes:**

- Avoid passing passwords via command line arguments (visible in process list)
- Prefer environment variables or interactive prompts
- Tokens are sensitive - handle them securely
- Tokens expire after a period (typically 1 hour)

---

### generate-long-descriptions.py

Generates user-friendly long descriptions for each agent by invoking the default agent with the agent's docstring and system prompt.

**Purpose:**
- Creates 2-3 sentence descriptions that explain what each agent does
- Focuses on capabilities and personality
- Stores descriptions in SSM parameters for the frontend to display

**When to run:**
- After initial CDK deployment
- After adding new agents
- After updating agent docstrings or system prompts
- Can be run multiple times safely (idempotent)

**Prerequisites:**
- CDK stack must be deployed
- AWS credentials configured
- Python 3.8+ installed
- Required Python packages installed

**Installation:**

```bash
# Install required packages
pip install -r infra-cdk/scripts/requirements.txt
```

**Usage:**

```bash
# Run from repository root (will auto-retrieve Cognito token if needed)
python infra-cdk/scripts/generate-long-descriptions.py

# Or with manually set token
export AGENTCORE_ACCESS_TOKEN=$(python infra-cdk/scripts/get-cognito-token.py)
python infra-cdk/scripts/generate-long-descriptions.py

# Or with Cognito credentials in environment
export COGNITO_USERNAME=user@example.com
export COGNITO_PASSWORD=mypassword
python infra-cdk/scripts/generate-long-descriptions.py

# Or with specific AWS profile
AWS_PROFILE=myprofile python infra-cdk/scripts/generate-long-descriptions.py

# Or with specific region
AWS_DEFAULT_REGION=us-west-2 python infra-cdk/scripts/generate-long-descriptions.py
```

**Environment Variables:**
- `AWS_DEFAULT_REGION`: AWS region (default: us-east-1)
- `AWS_PROFILE`: AWS profile to use (optional)
- `AGENTCORE_ACCESS_TOKEN`: JWT access token (optional, will auto-retrieve from Cognito if not set)
- `COGNITO_USERNAME`: Cognito username (used for auto-token retrieval)
- `COGNITO_PASSWORD`: Cognito password (used for auto-token retrieval)

**What it does:**

1. Reads stack configuration from `config.yaml`
2. Retrieves JWT access token (from environment or auto-retrieves from Cognito)
3. Lists all agents from SSM parameters
4. For each agent:
   - Fetches source code from S3
   - Extracts docstring and system prompt
   - Invokes the default agent to generate a description
   - Stores the description in SSM: `/{stack}/agents/{agent_name}/long-description`

**Output:**

The script provides detailed logging:
- Agent discovery progress
- Source code extraction status
- Description generation progress
- Final summary with success/skip/error counts

**Error Handling:**

The script handles errors gracefully:
- Skips agents with missing source code (logs warning)
- Skips agents with no docstring or system prompt (logs warning)
- Continues processing other agents if one fails
- Exits with code 1 if any errors occurred

**Example Output:**

```
2024-01-15 10:30:00 - INFO - Starting long description generation...
2024-01-15 10:30:00 - INFO - Stack name: marodon-fast
2024-01-15 10:30:00 - INFO - AWS Region: us-east-1
2024-01-15 10:30:01 - INFO - Finding default agent...
2024-01-15 10:30:02 - INFO - Default agent Runtime ARN: arn:aws:bedrock-agentcore:...
2024-01-15 10:30:02 - INFO - Listing agents...
2024-01-15 10:30:03 - INFO - Found 4 agents: orchestrator, umich, weather, calculator

2024-01-15 10:30:03 - INFO - Processing agent: orchestrator
2024-01-15 10:30:04 - INFO -   Extracted docstring: 245 chars
2024-01-15 10:30:04 - INFO -   Extracted system prompt: 512 chars
2024-01-15 10:30:04 - INFO -   Invoking default agent to generate description...
2024-01-15 10:30:08 - INFO -   Generated description: The Orchestrator Agent is a sophisticated...
2024-01-15 10:30:09 - INFO - ✓ Stored long description for orchestrator

...

============================================================
SUMMARY
============================================================
Total agents: 4
✓ Successfully generated: 4
⚠ Skipped: 0
✗ Errors: 0
============================================================

✓ Long description generation complete!
```

## Adding New Scripts

When adding new post-deployment scripts:

1. Create the script in this directory
2. Make it executable: `chmod +x script-name.py`
3. Add a shebang: `#!/usr/bin/env python3`
4. Include comprehensive docstring explaining purpose and usage
5. Add error handling and logging
6. Make it idempotent (safe to run multiple times)
7. Update this README with documentation
8. Add any new dependencies to `requirements.txt`

## Best Practices

- **Idempotency**: Scripts should be safe to run multiple times
- **Error Handling**: Handle AWS API errors gracefully
- **Logging**: Provide clear progress and error messages
- **Configuration**: Read from `config.yaml` for consistency
- **Documentation**: Include usage examples and prerequisites
- **Testing**: Test scripts in development environment first
