"""
Coder Agent - A code validation expert with Python execution capabilities.

This agent validates all answers through code execution using AgentCore Code Interpreter.
Code Interpreter provides an isolated, secure coding sandbox (micro-VM and container)
with 230+ pre-installed libraries for data science, machine learning, and visualization.

Built with Strands SDK and integrated with AWS Bedrock AgentCore for memory,
authentication, and runtime deployment.

This is part of the multi-agent orchestration pattern where multiple specialist
agents share backend resources (Memory, Gateway, Code Interpreter, Cognito) but
maintain separate conversation histories using session prefixes.
"""

import json
import os
import sys
import traceback

# Add patterns to path for shared utilities
sys.path.append("/app/patterns")

from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)
from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext
from bedrock_agentcore.tools.code_interpreter_client import code_session
from strands import Agent, tool
from strands.models import BedrockModel

# Import shared utilities from patterns/utils
from utils.auth import extract_user_id_from_context

# Import shared tools from pattern-specific tools directory
sys.path.append("/app")

app = BedrockAgentCoreApp()


@tool
def execute_python(code: str, description: str = "") -> str:
    """
    Execute Python code using AgentCore Code Interpreter.
    
    This tool runs Python code in an isolated, secure sandbox environment with
    230+ pre-installed libraries. The sandbox maintains state between executions
    within the same session, allowing you to build on previous results.
    
    Args:
        code (str): The Python code to execute
        description (str): Optional description of what the code does (for logging)
        
    Returns:
        str: The output from code execution (stdout) or error message if execution failed
        
    Raises:
        RuntimeError: If Code Interpreter invocation fails
    """
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    
    if description:
        code = f"# {description}\n{code}"
    
    print(f"[CODE INTERPRETER] Executing code:\n{code}")
    
    try:
        # Call Code Interpreter and execute the generated code
        # code_session manages the lifecycle of the Code Interpreter session
        with code_session(region) as code_client:
            response = code_client.invoke(
                "executeCode",
                {
                    "code": code,
                    "language": "python",
                    "clearContext": False,  # Maintain state between executions
                },
            )
            
            # Process the event stream to extract results
            results = []
            errors = []
            
            for event in response["stream"]:
                if "result" in event:
                    result = event["result"]
                    
                    # Check for errors first
                    if result.get("isError", False):
                        errors.append("Code execution failed")
                    
                    # Extract content (output text)
                    if "content" in result and result["content"]:
                        for content_item in result["content"]:
                            if content_item.get("type") == "text":
                                results.append(content_item["text"])
                    
                    # Extract structured content (stdout/stderr)
                    if "structuredContent" in result and result["structuredContent"]:
                        structured = result["structuredContent"]
                        if "stdout" in structured and structured["stdout"]:
                            results.append(structured["stdout"])
                        if "stderr" in structured and structured["stderr"]:
                            errors.append(structured["stderr"])
            
            # Return results or errors
            if errors:
                error_msg = "\n".join(errors)
                print(f"[CODE INTERPRETER] Error: {error_msg}")
                return f"Error: {error_msg}"
            elif results:
                output = "\n".join(results)
                print(f"[CODE INTERPRETER] Output:\n{output}")
                return f"Output:\n{output}"
            else:
                print("[CODE INTERPRETER] Code executed successfully (no output)")
                return "Code executed successfully (no output)"
                
    except Exception as e:
        error_msg = f"Failed to execute code: {str(e)}"
        print(f"[CODE INTERPRETER] {error_msg}")
        return error_msg


class CoderSpecialistAgent:
    """
    Coder specialist agent for handling code validation queries.

    This agent validates answers through code execution. It shares long-term
    memory with other agents but maintains its own conversation history using
    the 'coder_' session prefix.
    """

    def __init__(self, user_id: str, base_session_id: str):
        """
        Initialize the Coder specialist agent.

        Args:
            user_id (str): The unique identifier for the user (actor_id in memory).
                          Extracted from the validated JWT token for security.
            base_session_id (str): The base session identifier that will be prefixed
                                  with 'coder_' for this agent's conversation history.
        """
        self.agent_name = "coder"
        self.user_id = user_id
        self.base_session_id = base_session_id

        # Apply inline session prefixing as specified in the design
        self.session_id = f"{self.agent_name}_{base_session_id}"

        # System prompt defines the agent's personality and behavior
        self.system_prompt = """You are a helpful AI assistant that validates all answers through code execution.

VALIDATION PRINCIPLES:
1. When making claims about code, algorithms, or calculations - write code to verify them
2. Use execute_python to test mathematical calculations, algorithms, and logic
3. Create test scripts to validate your understanding before giving answers
4. Always show your work with actual code execution
5. If uncertain, explicitly state limitations and validate what you can

APPROACH:
- If asked about a programming concept, implement it in code to demonstrate
- If asked for calculations, compute them programmatically AND show the code
- If implementing algorithms, include test cases to prove correctness
- Document your validation process for transparency
- The state is maintained between executions, so you can refer to previous results

TOOL AVAILABLE:
- execute_python: Run Python code and see output

RESPONSE FORMAT: The execute_python tool returns output or error messages.
Check the response to see if execution was successful.

You have access to:
- Short-term memory: Recent conversation history within this session
- Long-term memory: User preferences, important facts, and session summaries across all conversations
- Code Interpreter: Isolated Python sandbox with 230+ pre-installed libraries

When responding:
- Reference relevant information from past conversations when appropriate
- Learn and remember user preferences
- Build on previous context to provide personalized assistance
- Always validate your answers with code when possible

Be thorough, accurate, and always validate your answers when possible."""

        # Configure the Bedrock model
        # Using Claude Sonnet 4.5 for best performance and consistency across agents
        self.bedrock_model = BedrockModel(
            model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        )

        # Get memory ID from environment (set by CDK deployment)
        self.memory_id = os.environ.get("MEMORY_ID")
        if not self.memory_id:
            raise ValueError("MEMORY_ID environment variable is required")

        # Configure AgentCore Memory with long-term memory retrieval
        # This agent shares memory with other agents but has its own conversation history
        # The session_id is prefixed with 'coder_' to distinguish this agent's sessions
        self.agentcore_memory_config = AgentCoreMemoryConfig(
            memory_id=self.memory_id,
            session_id=self.session_id,  # Prefixed session ID
            actor_id=user_id,  # Same user across all agents
            retrieval_config={
                # Retrieve user preferences with high relevance threshold
                "/preferences/{actorId}": RetrievalConfig(top_k=5, relevance_score=0.7),
                # Retrieve facts with lower threshold for broader context
                "/facts/{actorId}": RetrievalConfig(top_k=10, relevance_score=0.3),
                # Retrieve session summaries for context from previous conversations
                "/summaries/{actorId}/{sessionId}": RetrievalConfig(
                    top_k=3, relevance_score=0.5
                ),
            },
        )

        # Create session manager for memory integration
        self.session_manager = AgentCoreMemorySessionManager(
            agentcore_memory_config=self.agentcore_memory_config,
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        )

        print(
            f"[CODER AGENT] Initializing agent for user: {user_id}, session: {self.session_id}"
        )

        # Create the agent with code execution tool, model, and memory
        self.agent = Agent(
            name="CoderAgent",
            system_prompt=self.system_prompt,
            tools=[execute_python],  # Code Interpreter tool
            model=self.bedrock_model,
            session_manager=self.session_manager,
            trace_attributes={
                "user.id": user_id,
                "session.id": self.session_id,
                "agent.type": "coder",
            },
        )

        print("[CODER AGENT] Agent created successfully")

    async def handle_request(self, user_query: str):
        """
        Process incoming request and stream response.

        Args:
            user_query (str): The user's query/message to process.

        Yields:
            dict: Streaming response events from the agent, including:
                  - status: Event status
                  - data: Response text chunks
                  - tool_use: Tool invocation events (code execution)
                  - error: Error message if something fails
        """
        print(f"[CODER AGENT] Processing query: {user_query}")

        try:
            # Stream the agent's response token-by-token for better UX
            # The agent will access memory, execute code as needed, and generate responses
            async for event in self.agent.stream_async(user_query):
                # Convert event to JSON-serializable format and yield
                yield json.loads(json.dumps(dict(event), default=str))

        except Exception as e:
            # Log the error with full traceback for debugging
            print(f"[CODER AGENT ERROR] Error processing request: {e}")
            traceback.print_exc()

            # Return error to client
            # Following the "fail loudly" principle - don't hide errors
            yield {"status": "error", "error": str(e)}


@app.entrypoint
async def agent_stream(payload: dict, context: RequestContext):
    """
    Main entrypoint for the Coder agent using streaming.

    This function is called by AgentCore Runtime when the agent receives a request.
    It extracts the user's query from the payload, securely obtains the user ID from
    the validated JWT token in the request context, creates the Coder agent with
    memory integration and Code Interpreter tool, and streams the response back token-by-token.

    The user ID is extracted from the JWT token (via RequestContext) rather than
    trusting the payload body, which could be manipulated by clients.

    Args:
        payload (dict): Input payload containing:
                       - prompt: The user's query/message
                       - runtimeSessionId: The session identifier
        context (RequestContext): RequestContext containing the validated JWT token
                                 with user identity

    Yields:
        dict: Streaming response events from the agent, including:
              - status: Event status
              - data: Response text chunks
              - tool_use: Tool invocation events (code execution)
              - error: Error message if something fails

    Example payload:
        {
            "prompt": "Calculate the factorial of 10",
            "runtimeSessionId": "session-123"
        }
    """
    # Extract required fields from payload
    user_query = payload.get("prompt")
    base_session_id = payload.get("runtimeSessionId")

    # Validate required fields
    if not all([user_query, base_session_id]):
        yield {
            "status": "error",
            "error": "Missing required fields: prompt or runtimeSessionId",
        }
        return

    try:
        # Extract user ID securely from the validated JWT token
        # This ensures we use the authenticated user's identity, not a potentially
        # manipulated value from the request body
        user_id = extract_user_id_from_context(context)

        print(
            f"[CODER STREAM] Starting streaming invocation for user: {user_id}, "
            f"base_session: {base_session_id}"
        )
        print(f"[CODER STREAM] Query: {user_query}")

        # Create the Coder specialist agent with memory, Code Interpreter, and personality
        coder_agent = CoderSpecialistAgent(
            user_id=user_id, base_session_id=base_session_id
        )

        # Stream the agent's response
        async for event in coder_agent.handle_request(user_query):
            yield event

    except Exception as e:
        # Log the error with full traceback for debugging
        print(f"[CODER STREAM ERROR] Error in agent_stream: {e}")
        traceback.print_exc()

        # Return error to client
        # Following the "fail loudly" principle - don't hide errors
        yield {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # Run the AgentCore app when executed directly
    # This is used by AgentCore Runtime to start the agent service
    app.run()
