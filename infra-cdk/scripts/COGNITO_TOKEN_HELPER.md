# Cognito Token Helper Script

## Overview

The `get-cognito-token.py` helper script automates JWT token retrieval from AWS Cognito for authenticating with AgentCore Runtime APIs. This eliminates the need to manually obtain and export tokens.

## Implementation Details

### Files Created/Modified

1. **`infra-cdk/scripts/get-cognito-token.py`** (NEW)
   - Standalone helper script to retrieve Cognito JWT tokens
   - Reads Cognito configuration from SSM parameters
   - Supports multiple credential input methods (CLI args, env vars, interactive)
   - Outputs token to stdout for easy script integration
   - Comprehensive error handling with user-friendly messages

2. **`infra-cdk/scripts/generate-long-descriptions.py`** (MODIFIED)
   - Updated `get_jwt_token()` function to automatically call helper script
   - Falls back to automatic token retrieval if `AGENTCORE_ACCESS_TOKEN` not set
   - Maintains backward compatibility with manual token setting

3. **`infra-cdk/scripts/README.md`** (UPDATED)
   - Added comprehensive documentation for `get-cognito-token.py`
   - Updated `generate-long-descriptions.py` documentation with new token retrieval behavior
   - Added usage examples for both scripts

4. **`infra-cdk/scripts/test_get_cognito_token.py`** (NEW)
   - Unit tests for the helper script
   - Tests all core functions with mocked AWS clients
   - Validates error handling and edge cases

### Key Features

#### Automatic Token Retrieval
The `generate-long-descriptions.py` script now automatically retrieves tokens:

```python
def get_jwt_token() -> str:
    # Check environment variable first
    token = os.environ.get('AGENTCORE_ACCESS_TOKEN')
    if token:
        return token
    
    # Auto-retrieve from Cognito using helper script
    result = subprocess.run([sys.executable, "get-cognito-token.py"], ...)
    return result.stdout.strip()
```

#### Multiple Credential Input Methods
Priority order:
1. Command line arguments (`--username`, `--password`)
2. Environment variables (`COGNITO_USERNAME`, `COGNITO_PASSWORD`)
3. Interactive prompt (secure password input)

#### SSM-Based Configuration
Reads Cognito configuration from SSM parameters:
- `/{stack_name}/cognito/user-pool-id`
- `/{stack_name}/cognito/client-id`

This ensures the script always uses the correct Cognito configuration for the deployed stack.

#### Script-Friendly Output
- Token output to stdout (can be captured)
- Logs and errors to stderr (don't interfere with token capture)
- Exit codes indicate success/failure

### Usage Examples

#### Standalone Usage

```bash
# Interactive (prompts for credentials)
python infra-cdk/scripts/get-cognito-token.py

# With command line arguments
python infra-cdk/scripts/get-cognito-token.py --username user@example.com --password mypass

# With environment variables
export COGNITO_USERNAME=user@example.com
export COGNITO_PASSWORD=mypassword
python infra-cdk/scripts/get-cognito-token.py

# Export token for use in other scripts
export AGENTCORE_ACCESS_TOKEN=$(python infra-cdk/scripts/get-cognito-token.py)
```

#### Automatic Integration

```bash
# generate-long-descriptions.py now auto-retrieves token if not set
python infra-cdk/scripts/generate-long-descriptions.py

# Or provide credentials via environment
export COGNITO_USERNAME=user@example.com
export COGNITO_PASSWORD=mypassword
python infra-cdk/scripts/generate-long-descriptions.py

# Or manually set token (backward compatible)
export AGENTCORE_ACCESS_TOKEN=$(python infra-cdk/scripts/get-cognito-token.py)
python infra-cdk/scripts/generate-long-descriptions.py
```

### Error Handling

The script provides user-friendly error messages for common scenarios:

- **Incorrect credentials**: "Authentication failed: Incorrect username or password"
- **User not found**: "Authentication failed: User 'user@example.com' not found"
- **User not confirmed**: "User is not confirmed. Please verify your email."
- **Password reset required**: "Password reset required for user"
- **Missing SSM parameters**: "Cognito configuration not found in SSM"

### Security Considerations

1. **Password Visibility**: Avoid passing passwords via command line arguments (visible in process list). Prefer environment variables or interactive prompts.

2. **Token Handling**: JWT tokens are sensitive credentials. Handle them securely:
   - Don't log tokens
   - Don't commit tokens to version control
   - Tokens expire (typically 1 hour)

3. **Credential Storage**: The script does not store credentials. They must be provided each time or set in environment variables.

### Testing

Unit tests verify all core functionality:

```bash
cd infra-cdk/scripts
python3 test_get_cognito_token.py -v
```

All 9 tests pass:
- Configuration loading
- SSM parameter retrieval
- Credential input methods
- Authentication flow
- Error handling

### Coding Standards Compliance

The implementation follows project coding conventions:

1. **Docstrings**: Every function has comprehensive docstrings explaining:
   - Purpose
   - Input parameters with types
   - Return values with types
   - Exceptions raised

2. **Type Hints**: Explicit type annotations in function signatures:
   ```python
   def get_cognito_config(ssm_client, stack_name: str) -> tuple[str, str]:
   ```

3. **Error Handling**: No silent failures - all errors raise exceptions with clear messages

4. **Logging**: Comprehensive logging to stderr for debugging

5. **Comments**: Non-obvious code is thoroughly commented

### Integration with Existing Workflow

The helper script integrates seamlessly with the existing post-deployment workflow:

**Before:**
```bash
# Manual token retrieval required
export AGENTCORE_ACCESS_TOKEN="<manually obtained token>"
python infra-cdk/scripts/generate-long-descriptions.py
```

**After:**
```bash
# Automatic token retrieval
export COGNITO_USERNAME=user@example.com
export COGNITO_PASSWORD=mypassword
python infra-cdk/scripts/generate-long-descriptions.py
```

Or even simpler (interactive):
```bash
# Script prompts for credentials automatically
python infra-cdk/scripts/generate-long-descriptions.py
```

### Future Enhancements

Potential improvements for future iterations:

1. **Token Caching**: Cache tokens until expiration to avoid repeated authentication
2. **MFA Support**: Handle multi-factor authentication challenges
3. **Service Account**: Support for service account credentials (non-interactive)
4. **Token Refresh**: Automatically refresh expired tokens using refresh token
5. **Multiple Profiles**: Support for multiple Cognito user profiles

## Conclusion

The Cognito token helper script significantly improves the developer experience by:
- Eliminating manual token retrieval steps
- Providing flexible credential input methods
- Offering clear error messages for troubleshooting
- Maintaining backward compatibility with existing workflows
- Following project coding standards and best practices

The implementation is production-ready, well-tested, and fully documented.
