# Agent Instructions

## Memory (Recallant)

- If Recallant is configured and consent allows agent-authored memory, you must use Recallant by
  default inside the allowed boundary. Configuration proves access; proof proves memory;
  capture-active proves Recallant is doing its job.
- At session start: call `memory_start_session`. If it reports `previous_session_recovery` or
  `previous_unclosed_session`, treat that as recovery context for this project, not an alarm and
  not a fresh instruction. Review checkpoint/captured events before asking the owner to repeat
  context.
- Before non-trivial work after session start: call `memory_get_context_pack` with the current task hint.
- Use `memory_search` for raw evidence/chunks only when the context pack says more evidence is needed or the task changes.
- Use specific queries in `memory_search`, not broad ones. One call per session start is usually enough.
- Automatic inside consent: session start, context read, concise decisions, actions, tests,
  checkpoints, closeout, and one synthetic proof marker when running diagnostics.
- After meaningful progress: write concise agent-authored events/memories through
  `memory_append_event` or `memory_create_agent_memory`, then call
  `memory_set_checkpoint`; Recallant syncs the compact `PROJECT_LOG.md` fallback when it exists.
- On clear pause/exit/closeout intent, or when meaningful work is complete: call
  `memory_closeout`; rely on its repo-sync result instead of editing `PROJECT_LOG.md` by hand.
- To reuse a pattern from another project: search explicitly for source-linked examples, adapt the pattern locally, and create current-project memory with source refs after applying it.
- Approval required: attach/import/onboard existing project history, bulk file summaries, raw logs,
  customer data, or artifacts. Do not import or summarize project files without owner approval.
- Forbidden: secrets, `.env`, private keys, raw credentials, database URLs, provider tokens,
  customer data, raw artifacts, backups, and private deployment notes. Never paste them into memory
  tools.
- If direct MCP use is unavailable, use the CLI capture fallback: `recallant agent-start`,
  `recallant agent-event`, `recallant agent-checkpoint`, and `recallant agent-closeout`.
  If the server is unavailable, the CLI writes local spool for later `recallant sync-spool`.
