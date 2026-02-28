AgentCore Memory - Used by: also used by each agent to personalize chat interactions (existing capability built into agents' code). Location: No, already specified/configured - I believe in backend-stack.ts - and deployed. The agents already are calling it. Now the UI (via a lambda) also will call it.



AgentCore Gateway - Used by: NO that is a gross misunderstanding. Gateway is a tools and MCP gateway, not an agent gateway. AgentCore Runtime is the "agent gateway" - its API supports listing agents and invoking them. 'Gateway' API supports listing tools (including lambdas, other agents, and MCP servers - I believe), running RAG semantic search on tools, and the Gateway manages inbound auth (can the specific agent on behalf of a specific user be granted access to the Gateway and to a specific tool?) and outbound auth (if the tool call requires an auth token, Gateway attaches the token into a request header - so the agent/LLM selects a tools and forms the tool input, but Gateway programatically handles the auth tokens as a separation of concerns/duties - Gateway is deterministic vs the agents are untrusted entities. I don't recall if there is an integration with SSM params (maybe).



Code Interpreter should be called AgentCore Code Interpreter. Purpose: Called as a tool by agents that need to execute python code in sandboxed env. Location: double check if already in backend-stack.ts or just imported/called via agent code. 



AgentCore Identity: Move to future Components. Seems like unique session id and capture of user and agent are handled by Runtime itself, while Identity service is focused on agent inbound auth (can user access agent) and agent outbound auth (can agent on behalf of user access a/ AWS resources (services and runtime agents using IAM) or b/ external resources (Google Drive etc using API Keys or OAuth) or c/ Gateway targets behind AgentCore Gateway (via Gateway inbound auth). Identity handles that logic and retreives API keys etc. without exposing them directly to the agent/LLM. We aren't using these features yet. 



The Component Integration Map needs some updates to conform to the above clarification. And the design doc plus a steering doc must clarify these product descriptions to avoid future confusion. 



Observability Integration: Session and trace queries must support user filtering (and agent filtering)



Gateway Integration: Maintain existing SSM-based discovery pattern ... again, that's not what Gateway is for. There is a good question: is SSM discovery needed when AgentCore Runtime could be queried instead? Maybe make a note that the current architecture uses SSM (maybe to store additional configuration details, maybe in case some agents are run locally (not hosted on Runtime) but still must integrate with AgentCore Memory, etc. AND for now we will leverage SSM but may shift some agent discovery back to Runtime later?



Agent Gallery Page Flow: I'm not a React expert so am curious on best practies and trade offs. In the current plan, I beleive the agent gallery page might be the default (it's visually appealing and shows all the agents). Regardless, all the pages require the list of available agents (gallery displays tiles, details page zooms into metadata on one, memory page and observability dashboard too) so should the react app pull in the agent list and metadata once and persist it? I don't think lambdas should re-hydrate that info on each click or each navigation to the UI's pages. Do we need a healthcheck or periodic refresh or polling, or would that happen anyway? 



Backend Components: 

Memory - the AgentCore Memory supports a few different 'long term memory strategies' that generate memory records, each with their own json schema and stored using a specific segmentation. e.g. 'preference memories' are stored using a partition that might include '/preferences/user_id/timestamp/' (the agent is learning about a specfic user) while eposodic memories might not be partitioned by user_id (the agent is learning how to solve a problem, its repeatable across user interactions). The memory strategies are part of the AgentCore Memory configuration (set at CDK deployemnt of backend.ts) so the schemas and partitioning is known/fixed until a new deployment. The Response Format will be different depending on the memory type/schema. 



2. Observability Sessions API Lambda: I don't think so ... the observability logs are emited by Runtime (and other components like Gateway, maybe Memory, etc) and are collected by the AgentCore Observability service. They're made available in Cloudwatch as log groups (I believe) - some config may be needed to "enable" them or adjust the granularity or whether only a 1% sample are collected. I want them all collected. They are structured in OTEL (open telemetry) format so they can be displayed in CloudWatch or elsewhere (like our UI). Must verify that they should be retrieved via an AgentCore API or via a CloudWatch API. But not Runtime.  And IAM Permissions Req: ssm:GetParameter for runtime ARN lookup ... this is back to my question on whether agent discover can/should be done once and cached or stored as state. Response Format: is that based on AgentCore docs, or just a guess? does it need validation as part of a task?



Similar questions on 4. Obervability Metrics API Lambda



And same questions on data models - do these proposed data models conform to an AgentCore or strands spec, or are they plausible models based specific to this proposed UI? If there is a spec used by AgentCore, I'd prefer to leverage it directly unless there's a strong reason against that approach. 



Overall, I have a ton of questions and want to take a ballanced approach - address the ones we can now, highlight ones needing further validation along the way. And I believe this 'Enhanced Agent UI' spec is really an Epic that might be divided into Features (with their own specs/) or else it's a Feature (one spec/) with multiple phases, and git commits per phase. Pros/cons to both - either keeping all the design and tasks together during execution, or using this as the parent and generating more detailed design and tasks when imlementing memory page, observability page, etc. but then needing to update this doc as things change in the features docs. ?



