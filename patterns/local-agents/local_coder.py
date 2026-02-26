"""Strands agent armed with AgentCore Code Interpreter - to write, run, and debug python code. Try some math, or anything requiring a calculation.

Code Interpreter spins up an isolated, secure coding sandbox (micro-VM and container) on demand for use by the agent. You can configure access to S3 (e.g. to pull in files up to 5 GB for processing) or forbid such data access. The python runtime environment is pre-installed with 230+ libraries popular for data science, machine learning, processing files, and building data visualizations or user interfaces.

AgentCore is modular: Code Interpreter can be called by local agents (great for dev), agents hosted on AgentCore Runtime (great for dev/test/prod), or any other platform. Whether called locally or via Runtime, each Code Interpreter session is visible in the AgentCore console, AgentCore Observability dashboard in CloudWatch, and exportable via OpenTelemetry.

AgentCore prioritizes security: For an agent to access Code Interpreter as a tool, the application invoking the agent must be permissioned in AWS IAM (e.g. authorized to assume a role with Code Interpreter permissions) specific to the given AWS account and region.

This agent's code started from https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-building-agents.html plus some improved error handling and streaming req/response processing by Kiro.
"""

import json
import sys
import os
import asyncio

# Add the AgentCore package path
sys.path.append('/opt/anaconda3/lib/python3.12/site-packages')

from strands import Agent, tool
from bedrock_agentcore.tools.code_interpreter_client import code_session

# Better to get region from ~/.aws/config
REGION = 'us-east-1'

# Detailed system prompt for the assistant
SYSTEM_PROMPT = """You are a helpful AI assistant that validates all answers through code execution.

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

RESPONSE FORMAT: The execute_python tool returns a JSON response with:
- sessionId: The code interpreter session ID
- id: Request ID
- isError: Boolean indicating if there was an error
- content: Array of content objects with type and text/data
- structuredContent: For code execution, includes stdout, stderr, exitCode, executionTime

For successful code execution, the output will be in content[0].text and also in structuredContent.stdout.
Check isError field to see if there was an error.

Be thorough, accurate, and always validate your answers when possible."""

# Define and configure the code interpreter tool 
@tool
def execute_python(code: str, description: str = "", verbose=True) -> str:
    """Execute Python code using AgentCore Code Interpreter"""

    if description:
        code = f"# {description}\n{code}"
    
    if verbose:
        print(f"#### 🔧 Code to execute: ####\n{code}")
    else:
        print(f"\n#### 🔧 Executing code. ####")
    
    try: 
        # Call the Invoke method and execute the generated code
        with code_session(REGION) as code_client:
            response = code_client.invoke("executeCode", {
                "code": code,
                "language": "python",
                "clearContext": False
            })
            
            # Process the event stream to extract results
            results = []
            errors = []
            
            for event in response["stream"]:
                if "result" in event:
                    result = event["result"]
                    
                    # Check for errors first
                    if result.get("isError", False):
                        errors.append("Code execution failed")
                    
                    # Extract content
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
            
            # Return results
            if errors:
                error_msg = "\n".join(errors)
                # print(f"❌ Error: {error_msg}")
                return f"Error: {error_msg}"
            elif results:
                output = "\n".join(results)
                # print(f"✅ Output:\n{output}")
                return f"Output:\n{output}"
            else:
                # print("✅ Code executed successfully (no output)")
                return "Code executed successfully (no output)"
                
    except Exception as e:
        error_msg = f"Failed to execute code: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg


# Configure the strands agent including the tool(s)
coder_agent=Agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[execute_python],
        callback_handler=None)

# query="Can all the planets in the solar system fit between the earth and moon?"

async def invoke_agent(query):
    """Async function to invoke the agent and collect response."""
    response_text = ""
    async for event in coder_agent.stream_async(query):
        if "data" in event:
            # Stream text response
            chunk = event["data"]
            response_text += chunk
            print(chunk, end="", flush=True)  # Print as it streams
    return response_text

# Invoke the agent asynchronously and stream the response
async def main():
    print("\n\n" + "=" * 70)
    print("🚀 Coder Agent Ready! (Type 'quit', 'exit', 'q', or 'bye' to exit)")
    print("=" * 70)
    
    while True:
        query = input("\n\nUser > ")
        if query.lower() in ['quit', 'exit', 'q', 'bye']:
            print("Goodbye! 👋")
            break
            
        print("\nAgent > ", end="", flush=True)
        response_text = await invoke_agent(query)  # Need 'await' here!
        print()  # New line after streaming response
    

if __name__ == '__main__':
    asyncio.run(main())
