# UAT in the brower: 

1. Add nav bar (same as other pages) so user can return from observability back to chat, etc.

2. Observability history seems to begin just now. I saw zero sessions (whether filtered on 1hr or 30days) so initiated a chat and now it shows 2 agent invocations. If no history prior to this deployment is expected (prior invocations weren't captured) that's fine. But if the old metrics and logs exist then we should include them.

3. Detailed metrics by agent: Agent Name is 'unknown' when in fact it was the umich agent that just had 2 invocations.

4. Token count says 7.6K (7.4K in / 214 out) ... what's that math? Is it counting output tokens higher because the cost of output tokens is a multiple of the cost of input tokens ... if so, that could be a good approach - we may need a little (info) icon the user can hover on to see that explaination)

5. 'Auto-refresh On' has a spinning wheel that's distracting. The same spinner for Refresh button is good - it spins while that runs and then stops. But we need a different way to see Auto-refresh is active (maybe a little green dot that's lit when active) and not a continuous spinning animation.

6. Sessions sub-tab isn't working. No Sessions Found

No sessions match the current filters. Try adjusting the time range or agent filter. ... and the input for agents is free text when it should instead reuse the drop down used to filter on agents in the memory page - that populates with the available agents. Observability also could benefit from the user ID filter (also on that memory page) even if the backend or front end filtering isn't implemented yet. 