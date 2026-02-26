"""
Shared tool for secure Python code execution via Code Interpreter.

This is a pattern-specific wrapper around the canonical code interpreter
implementation located at tools/code_interpreter/. It provides a simplified
interface for agents in the multi-agent orchestration pattern.
"""

import json
import logging
import os
import sys
from typing import Dict, Any

# Add patterns to path for shared utils
sys.path.append('/app/patterns')

from utils.auth import get_gateway_access_token
from utils.ssm import get_ssm_parameter

logger = logging.getLogger(__name__)


def execute_python_securely(code: str, session_id: str) -> Dict[str, Any]:
    """
    Execute Python code securely using AgentCore Code Interpreter.
    
    This function delegates to the canonical code interpreter implementation
    at tools/code_interpreter/ and provides a simplified interface for agents.
    It handles authentication and configuration retrieval automatically.
    
    Args:
        code (str): Python code to execute in the secure sandbox.
        session_id (str): Session identifier for context and tracking.
        
    Returns:
        Dict[str, Any]: Dictionary containing execution results or error information.
            Success format: {"results": [...], "session_id": "..."}
            Error format: {"error": "error message", "session_id": "..."}
            
    Raises:
        ValueError: If required parameters are missing or invalid.
        RuntimeError: If code execution fails due to service errors.
    """
    if not code or not isinstance(code, str):
        logger.error("Invalid code parameter: must be a non-empty string")
        return {
            "error": "Invalid code parameter: must be a non-empty string",
            "session_id": session_id
        }
    
    if not session_id or not isinstance(session_id, str):
        logger.error("Invalid session_id parameter: must be a non-empty string")
        return {
            "error": "Invalid session_id parameter: must be a non-empty string",
            "session_id": session_id or "unknown"
        }
    
    logger.info("Executing Python code for session: %s", session_id)
    logger.debug("Code to execute: %s", code[:100] + "..." if len(code) > 100 else code)
    
    try:
        # Get AWS region from environment
        region = os.environ.get(
            "AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        )
        
        # Import and use the canonical code interpreter implementation
        # This is the root-level implementation that all patterns delegate to
        sys.path.insert(0, '/app')
        from tools.code_interpreter.code_interpreter_tools import CodeInterpreterTools
        
        # Initialize the code interpreter with the region
        code_interpreter = CodeInterpreterTools(region=region)
        
        # Execute the code using the canonical implementation
        result_json = code_interpreter.execute_python_securely(code=code)
        
        # Parse the JSON result
        result = json.loads(result_json)
        
        # Clean up the code interpreter session
        code_interpreter.cleanup()
        
        # Add session_id to the result for tracking
        result["session_id"] = session_id
        
        logger.info("Code execution completed successfully for session: %s", session_id)
        return result
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse code execution result: %s", str(e))
        return {
            "error": f"Failed to parse execution result: {str(e)}",
            "session_id": session_id
        }
    except ImportError as e:
        logger.error("Failed to import canonical code interpreter: %s", str(e))
        return {
            "error": f"Code interpreter service unavailable: {str(e)}",
            "session_id": session_id
        }
    except Exception as e:
        logger.error("Code execution failed for session %s: %s", session_id, str(e))
        return {
            "error": f"Code execution failed: {str(e)}",
            "session_id": session_id
        }
