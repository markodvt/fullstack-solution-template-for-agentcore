# Amazon Connect Integration
*Integrate this FAST Agent Gallery with Amazon Connect to support voice and chat interactions for 'users','administrators', DevOps, Security, and other personas.*

## Status
Spec not started; README in early concept stage

## Concept

**FAST Agent Gallery** allows users to discover and interact with agents (individually or within a multi-agent flow). It supports multiple users, each authenticated via **Cognito** - and collects memories and metrics on the interactions of each user with the agents. Users also can provide feedback on the agent interactions. Agents have access to tools and data. 

Taken together, the Agents, Users, Tools, Data, and Interactions, and Feedback represent a rich collection of capabilities and interaction data.

**Amazon Connect** in an omni-channel platform support voice and chat interactions. Integrate FAST and Connect to support **Voice** and **Chat** interface between multiple user personas and FAST Agent Gallery:

### Admin:
As a FAST Agent Gallery *Admin* I can engage an Admin Agent (and sub agents) to perform admin tasks and troubleshoot FAST, including:
- list cognito users (leverage `scripts/list_cognito_users.py`)
- add new users to the cognito pool - invite them to sign-in
- review metrics about the platform (number of users, user activity volume, number of agents, agent activity like token usage, memory stats, tools stats, etc.)
- Ask the agent to generate metrics and dashboards (pre designed or on the fly)
- TBD on actions to take

### Dev:
As a FAST Agent Gallery *Dev* I can:
- Examine the code base (via its GitHub repo)
- Review .kiro/ including steering/, specs/, dev-history/ to understand how the codebase was developed
- Suggest new features, discuss them, ask kiro (or a similar (sub)agent to document the proposed feature and generate draft spec/ docs
- Troubleshoot issues - prompting the agent(s) to investigate, disucss, and produce code review artifacts for further review.
- TBD on taking actions related to the codebase

### User:
As a FAST Agent Gallery *User* I can perform a range of tasks similar to using the FAST UI. Connect becomes an alternative channel exposing the same capabilities in a different user experience (or an expanded user experience). This includes the current UI capabilities and some more introspection of the platform (which we may add to the UI as well)
- Login
- Chat with the agents
- Examine my memories
- Discuss my usage of the platform


## Channels
Interact across voice, chat, email. For instance:
- Admin can call Connect to initiate the dialog. Then ask agent to text them so the user can enter a new user's mobile or email. The agent should be able to access that new user info and (using voice) confirm the input with the admin and ask "should I go ahead and set up this new user?". An affirmative voice response from the admin should trigger the agent to proceed by setting up the user and sending the new user an invitation to login. 
- For interactions that result in new artifacts, the interaction may be over voice but the new artifact can be shared via chat, text, email, or in the webapp, while the voice conversation continues.
- Voice interactions should be captured as transcripts (Connect supports that out of the box). The transcript already is persisted within Connect (I think) - how should it also be captured in our FAST app? How does our FAST app - itself a UI plus persisted data on user interactions with AI agents - integrate with Connect given that Connect also is a user engagement platform? There is some overlap.
- Connect Contact Lens features supports sentiment analysis and other derived information about interactions. While FAST supports long term memories derived from FAST interactions. Again there is some useful overlap between FAST and Connect - how best to capture these insights using existing capabilities of the two platforms, enrich them, and share them - make them available to the FAST agents and via the FAST UI experience and also through Connect?

## Amazon Connect AI and Flows
Connect includes no code/low code creation of AI agents (some pre-built) and Flows. This spec/ and/or future specs should illustrate the use of those capabilities.

## Extensions
- **Agent Kiro Power**: Build new conversational agents with relevant tools: FAST Agent Gallery can be extended by adding new agents or modifying existing agents. Can this Connect integration enable an Admin to engage in a live voice conversation about designing a new agent, review its purpose (how it will assist users or other personas), its other requirements (cost, latency, accuracy ... criticality ... sensitivity of data ... required data ... guardrails ... ) - this could become a **Kiro Power** that elicits a checklist of requirements (functional and non) from the agent dev in order to agree on an **agent spec** and then generate the agent's .py file, deploy to FAST Agent Gallery, and test. The Kiro Power can be used via Connect as a conversational channel or in the IDE, etc.
- **Agent Patterns**: A scoped-down version of the above ... the current FAST Agent Gallery includes agents modelled on a few patterns that define a strands agent's purpose, background, and capabilities. To demonstrate how new agents can be created, write a Kiro Power that can be called (using Kiro or a similar (custom) agent, to write new agent .py files and deploy to the FAST Gallery - via a Connect voice conversation. The Connect agent could ask the user for a brief bio on their desired agent ... to include some or all of the items like university (current or past), current city, interests, expertise, ... and then consider tools. After eliciting these details, the agent can review and then propose an agent definition for review and then can deploy the new agent so the user can converse with it -- similar to some of our existing agents:
    - *umich_agent*: A strands agent that LOVES the University of Michigan, sports (especially tennis), math, and computer science - with internet access via `https_request` and 1-2 other tools
    - *colorado_agent*: A strands agent that recently moved to Denver with her cat, Napleon; just began a new job teaching 2nd grade in a Denver school; etc
    - *coder_agent*: A strands agent with access to AgentCore Code Interpreter to write and securely execute python code to solve problems
The first follows a pattern: `{university, personal interests (sports), professional or academic interests (math and comp sci), and tools}`. The second is more focused on `{city, career, family/pets, interests}`. The third is more practical, with a purpose and some tools.
