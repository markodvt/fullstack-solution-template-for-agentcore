# Challenge with the current approach
## We are in the process of adding multi agents:

1. I brought some agents into this repo by placing their prior codebase in agents/

2. Kiro attempted to conform to this repo by creating new sub directories for each, in patterns/

3. Changes to config.yaml and config-manager.ts (both in infra-cdk/) are meant to be backward compatible with the prior repo structure - when each `pattern/` subdirectory specified the agent(s). The new structure (proposed by Kiro but not yet deployed) would support a config-manager.ts that can also deploy multiple agents/ that are not within a single pattern/

## I question this approach, want to discuss

Looking at the initial repo, it is divided into clear modules:

infra-cdk/ 
    - Specifies all AWS resources to deploy uses nested CFN stacks for frontend (react UI on Amplify), backend (AgentCore Runtime, AgentCore Memory, etc. as well as Secrets Manager) and Cognito pool (for auth)
    - infra-cdk/config.yaml specifies the stack name base, admin_user email, backend, and deployment type (Docker or zip). Edit this config file 
    - Infra-cdk/lib/ includes utils/ (config-manager and agentcore-role) and includes the actual (nested) CDK stacks (which render as CFN stacks): frontend, cognito, backend)
    - Edit this directory as new AWS resources or new configurations are needed

frontend/ 
    - Stand alone react UI deployable to AWS Amplify, leveraging auth via Cognito, making calls to agents.
    - Edit this directory to change functionality in the UI

gateway/
    - Specifies a collection of tools/ that each are defined with a lambda.py and tool_spec.json. At deployment, each tool's lambda is deployed and each json is registered with AgentCore Gateway
    - The gateway/tools/ are deployed to lambda and gateway as part of the `backend` stack
    - Edit (add new tools/) to expose new lambda based tools via AgentCore Gateway. Note: agents also can access inline tools included within their own agent code (e.g. in strands, decorating any python function with @tool exposes it's docstring to the agent if its name is included in the agent's tools list.

patterns/
    - Specifies alternative agent patterns including a single strands agent or single LangChain agent.
    - The deployment selects one pattern, as specified in infra-cdk/config, and ignores the others.
    - What's not in patterns:
        ○ Cognito pool is independent, deploys via its own CDK/CFN stack. The Cognito pool is used for auth into the UI. It also can be used for inbound auth of agents (specified in patterns/) to allow them access to tools via the AgentCore Gateway specified in gateway/.
        ○ frontend/ is independent, deploys via its own CDK/CFN stack as a react UI via Amplify that uses a Cognito pool for auth. In reality, the frontend will call agents (specified in a pattern/) so the frontend needs to discover the URLs of those agents (which are stored in Secrets Manager or SSM Param)?
        ○ gateway/ is independently coded but deploys as part of the same backend stack. It deploys tools (each tool is specified as a lambda function and a tool_config.yaml). These tools are discoverable via the gateway. Access can be specified so that different agents in the selected pattern/ can have access to all gateway/ tools or a subset?
 
    
### What is in patterns:
Single strands agent/ pattern includes:
- Agent code.py that looks up the gateway url for the stack as an ssm parameter to create a gateway client; defines the agent (system prompt, model, memory id and config, session manager, gets gateway access token (using utils/ to call the stack's Cognito. I don't understand two things: a/ The Cognito pool we deployed includes an app client called marodon-fast-client … I assume that's how it returns tokens to accesses the gatway? (It also includes a second app client marond-fast-machine-client. What's the difference?) My second question: If the pattern were expanded to multiple agents, would each agent retrieve its own access token from Cognito? The utils/auth.py code defines a get_gateway_access_token() -> str that doesn't specify which agent. I think that's expected, assuming all agents should access the AgentCore Gateway and access to specific tools in the Gateway are managed by the Gateway (so the course grained control is Gateway access via the token, and fine grained access to specific tools is at the Gateway itself.

- Docker file (to deploy the agent)
- requirements.txt for the agent
- strands_code_interpreter.py as a strands wrapper around AgentCore Code Interpreter
- tools/ that could be shared among multiple agents. In this case, just a execute_python tool that calls strands.tool for code interpreter, which in turn calls AgentCore Code interpretor. This tools/ directory is a bit confusing since the agent also has access to the AgentCore Gateway for whatever tools are specified in gateway/ … whereas this tools/ within the pattern/ is just a way to declare a @tool for python code interp. In fact I see `def execute_python_securely(self, code: str) -> str:` in three parts of the code base and think some are duplicative.   

So the initial repo assumes that `patterns/` contains alternative agent deployments.

But the current repo revisions (not yet deployed) move into an alternative approach where instead of patterns/ we are asking config-manager to loop over multiple agents almost as if each agent is a pattern. I don't like that. I think if we want to deploy a "pattern" that includes several different agents (possibly these are sub-agents / skills agents orchestrated by an orchestrator agent, or maybe they are all peers and the UI can expose each, or maybe they form an agentic workflow with clear handoffs of tasks, or maybe they are agents that will be exposed via Amazon Connect … whatever the pattern, I think all the agents with all the tools (shared or not) below in a single pattern/ subdirectory so the infra-cdk config.yaml can point to the pattern and know all the agents to be deployed.

### Other considerations
1. If Gateway and Code Interpreter and later additions like AgentCore Observability, AgentCore Identity, AgentCore Policy, etc. are slow changing but the agents are faster changing (with updated system prompts, tools, orchestration patterns) should the agents be in their own CDK/CFN stack separate from these other backend services? Or does the CDK/CFN diff functionality address that concern because only the backend services that change are impacted? For instance, we might update a single agent's system prompt repreatedly while leaving the rest of the backend static.

2. Not every pattern will make sense with a single UI. But perhaps for the time being we can leave the UI as a static part of the repo, and keep the backend `pattern` as the only variable in the infra-cdk/config.yaml?

3. Same quesiton for the other elements.
