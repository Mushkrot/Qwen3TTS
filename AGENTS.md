# Agent Instructions

## Memory (Recallant)

- At session start: call `memory_start_session`; if it reports an unclosed previous session, recover from checkpoint/captured events before asking the owner to repeat context.
- Before non-trivial work after session start: call `memory_get_context_pack` with the current task hint.
- Use `memory_search` for raw evidence/chunks only when the context pack says more evidence is needed or the task changes.
- Use specific queries in `memory_search`, not broad ones. One call per session start is usually enough.
- After meaningful progress: write meaningful events/memories through `memory_append_event` or `memory_create_agent_memory`, then call `memory_set_checkpoint`; Recallant syncs the compact `PROJECT_LOG.md` fallback when it exists.
- On clear pause/exit/closeout intent: call `memory_closeout`; rely on its repo-sync result instead of editing `PROJECT_LOG.md` by hand.
- To reuse a pattern from another project: search explicitly for source-linked examples, adapt the pattern locally, and create current-project memory with source refs after applying it.
- Never paste secrets into memory tools.
- If direct MCP use is unavailable, use the CLI capture fallback: `recallant agent-start`,
  `recallant agent-event`, `recallant agent-checkpoint`, and `recallant agent-closeout`.
  If the server is unavailable, the CLI writes local spool for later `recallant sync-spool`.
