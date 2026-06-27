# Architecture

## Project Structure

```
prisma-agent/
├── main.py              # Entry point and main loop
├── config.py            # Environment variables and provider routing
├── requirements.txt
├── agent/
│   ├── state.py         # Shared LangGraph state schema
│   ├── supervisor.py    # LangGraph graph: analyze → execute → synthesize
│   ├── tools.py         # 8 LangChain tools available to agents
│   └── sub_agents/
│       ├── base.py      # Shared agent factory
│       ├── coder.py
│       ├── debugger.py
│       ├── searcher.py
│       ├── tester.py
│       └── spawner.py
├── utils/
│   ├── theme.py         # All design tokens (colors, styles, icons)
│   ├── renderers.py     # Rich UI renderables
│   ├── layout.py        # PrismaLayout utility for structured terminal UI management
│   ├── animations.py    # Spinner and live display
│   ├── input.py         # prompt_toolkit input session and mode state
│   ├── commands.py      # Slash command dispatch and tab-completion
│   └── display.py       # Backward-compat shim
└── tests/
    ├── test_tools.py
    ├── test_state.py
    ├── test_sub_agents.py
    ├── test_cli_ux.py
    └── test_integration.py
```

## Data Flow (per turn)

```
User input (prompt_toolkit)
  │
  ├─ Slash command? → handle_command() → output / state change
  │
  └─ Normal request →
       LiveManager.run_with_spinner()
         │
         └─ graph.invoke()
              │
              ├─ analyze node
              │    └─ Supervisor LLM
              │         ├─ Plain text → AIMessage → END
              │         └─ JSON plan → SubTask list
              │                         │
              │              ┌──────────┴──────────┐
              │         [plan mode]           [build mode]
              │              │                      │
              │             END             execute_plan node
              │                            (ThreadPoolExecutor, max 4)
              │                                     │
              │                            synthesize node
              │                            (Supervisor LLM again)
              │                                     │
              │                                    END
              │
       render result (Rich panels)
```

## State Schema (`agent/state.py`)

```python
class SubTask(TypedDict):
    agent_type: str          # "coder" | "debugger" | "searcher" | "tester" | "spawn"
    description: str         # Detailed instruction for the agent
    status: str              # "pending" | "completed" | "failed"
    result: Optional[str]    # Agent output after execution
    relevant_files: list[str]

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # Full conversation history
    subtasks: list[SubTask]   # Current turn's subtask queue
    mode: str                 # "build" | "plan"
```

`messages` uses LangGraph's `add_messages` reducer — new messages are appended, not replaced.

## LangGraph Graph

```
START → analyze → [conditional] → execute_plan → synthesize → END
                        └──────────────────────────────────────→ END
```

Routing condition (`route_after_analyze`):
- If `subtasks` populated AND `mode == "build"` → `execute_plan`
- Otherwise → `END`
