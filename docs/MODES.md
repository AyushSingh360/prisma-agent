# Plan Mode vs Build Mode

Prisma has two execution modes, switchable at any time with `Tab`.

## Build Mode (default)

The supervisor plans and immediately executes.

1. Supervisor analyzes the request and produces a JSON plan
2. Sub-agents run immediately in parallel
3. Results are synthesized into a final response
4. Tool execution summary + final message are shown

**Use Build mode when** you want results immediately.

## Plan Mode

The supervisor produces a plan but does not execute it.

1. Supervisor analyzes the request and produces a JSON plan
2. **Execution stops here** — no sub-agents are run
3. The plan is displayed as a structured card showing agent assignments
4. The original request is queued as a pending request

**Use Plan mode when** you want to review what Prisma intends to do before running it.

## Switching Modes

- Press `Tab` to toggle between modes
- The current mode is shown in the status bar: `BUILD` or `PLAN`
- Switching from PLAN → BUILD while a pending request exists will **automatically execute** the queued request

## Execution Flow

```
PLAN mode:
  analyze → subtasks populated → route to END → render plan card → queue request

BUILD mode:
  analyze → subtasks populated → execute_plan → synthesize → render results
```

## The Pending Request Queue

When in PLAN mode and a plan is shown:
- The original request is stored in memory
- The status bar shows `· queued`
- Press `Tab` to switch to BUILD — the queued request executes immediately
- The pending request is cleared after execution or when `/clear` is used
