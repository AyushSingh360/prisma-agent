<p align="center">
  <pre>
 ____  ____  ___ ____  __  __    _
|  _ \|  _ \|_ _/ ___||  \/  |  / \
| |_) | |_) || |\___ \| |\/| | / _ \  
|  __/|  _ < | | ___) | |  | |/ ___ \
|_|   |_| \_\___|____/|_|  |_/_/   \_\
  </pre>
</p>

<p align="center">
  <strong>Multi-agent coding assistant</strong><br>
  <em>Supervisor decomposes tasks into parallel sub-agents for faster code workflows</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/langgraph-1.x-purple" alt="LangGraph 1.x">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/status-active-brightgreen" alt="Active">
</p>

---

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#testing">Testing</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#development">Development</a>
</p>

---

## Overview

A **supervisor agent** receives natural language coding requests, intelligently decomposes them into subtasks, and spawns **specialized sub-agents** that execute in **parallel**. Results are synthesized into a clear response.

```
    Your request         Supervisor          Parallel sub-agents       Response
  ──────────────►   ┌───────────────┐      ┌──────────────────┐    ┌────────────┐
                    │ Analyze task  │      │ Coder  Debugger  │    │ Synthesize │
                    │ Create plan   │─────►│ Searcher Tester  │───►│ results    │
                    │ Route to      │      │ Spawner(if new)  │    │ Return     │
                    │ sub-agents    │      └──────────────────┘    └────────────┘
                    └───────────────┘
```

### Key capabilities

| | |
|---|---|
| **Parallel execution** | Up to 4 sub-agents run simultaneously via `ThreadPoolExecutor` |
| **5 sub-agent types** | Coder, Debugger, Searcher, Tester + dynamic Spawner for novel tasks |
| **7 primitive tools** | Read, Write, Edit, Shell, Grep, Glob, List |
| **Rich CLI** | Markdown rendering, conversation history, command palette |
| **Stateful graph** | LangGraph orchestrates the full workflow with checkpoint support |

---

## Architecture

### System design

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                            CLI LAYER                                   │
 │                         main.py + Rich                                 │
 └────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                        LANGGRAPH GRAPH                                 │
 │                                                                        │
 │    ┌─────────┐      ┌────────────┐      ┌───────────────┐              │
 │    │  START  │─────►│  analyze   │─────►│ execute_plan  │              │
 │    └─────────┘      └─────┬──────┘      └───────┬───────┘              │
 │                           │                     │                      │
 │                    ┌──────▼──────┐              │                      │
 │                    │  direct     │              │                      │
 │                    │  response   │              │                      │
 │                    │  → END      │              │                      │
 │                    └─────────────┘              │                      │
 │                                                 ▼                      │
 │                                           ┌──────────────┐             │
 │                                           │  synthesize  │             │
 │                                           └──────┬───────┘             │
 │                                                  │                     │
 │                                                  ▼                     │
 │                                           ┌──────────────┐             │
 │                                           │     END      │             │
 │                                           └──────────────┘             │
 └────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      SUB-AGENT POOL                                    │
 │                                                                        │
 │    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐        │
 │    │  Coder   │    │ Debugger │    │ Searcher │    │  Tester  │        │
 │    │ write    │    │ diagnose │    │  locate  │    │  verify  │        │
 │    │ modify   │    │  analyze │    │  search  │    │  assert  │        │
 │    └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘        │
 │         └───────────────┴───────────────┴────────────────┘             │
 │                                    │                                   │
 │                           ┌────────▼────────┐                          │
 │                           │    Spawner      │                          │ 
 │                           │  (on-demand)    │                          │ 
 │                           └─────────────────┘                          │
 └────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                          TOOL LAYER                                    │
 │                                                                        │
 │    read_file    write_file    edit_file    run_command                 │
 │    grep_search  glob_files    list_directory                           │
 └────────────────────────────────────────────────────────────────────────┘
```

### Request lifecycle

```
 User input
    │
    ├──► [analyze node] Supervisor LLM reads context
    │       │
    │       ├── "I need a plan" → JSON with subtasks → execute_plan
    │       │
    │       └── "I can answer" → direct response → END
    │
    ├──► [execute_plan node] ThreadPoolExecutor(max_workers=4)
    │       │
    │       ├── subtask[0] ──► Coder ──► AgentExecutor ──► result
    │       ├── subtask[1] ──► Debugger ──► AgentExecutor ──► result
    │       ├── subtask[2] ──► Searcher ──► AgentExecutor ──► result
    │       └── subtask[3] ──► Tester ──► AgentExecutor ──► result
    │
    └──► [synthesize node] LLM summarizes all results
            │
            └──► Final response presented in CLI
```

### State schema

```
AgentState (TypedDict)
│
├── messages: list[BaseMessage]       Conversation history
│   (reducer: add_messages)           Preserved across turns
│
└── subtasks: list[SubTask]
    │
    ├── agent_type: str               coder | debugger | searcher | tester | spawn
    ├── description: str              Task instruction for the sub-agent
    ├── status: str                   pending | completed | failed
    ├── result: Optional[str]         Full output from sub-agent
    └── relevant_files: list[str]     File paths for context
```

---

## Sub-agent system

### Registry

| Agent | Type | Tools | Responsibility |
|-------|------|-------|----------------|
| **Coder** | Persistent | read, write, edit, bash, grep, glob, ls | Write and modify source code |
| **Debugger** | Persistent | read, bash, grep, glob, ls | Diagnose bugs, trace errors |
| **Searcher** | Persistent | read, grep, glob, ls | Locate files and code patterns |
| **Tester** | Persistent | read, write, edit, bash, grep, glob, ls | Author and execute test suites |
| **Spawner** | Dynamic | read, write, edit, bash, grep, glob, ls | Handle tasks outside standard roles |

### Agent factory

Each sub-agent is a `CompiledStateGraph` created via LangChain's `create_agent`:

```python
from langchain.agents import create_agent

def create_sub_agent(model, api_key, base_url, system_prompt, tools):
    llm = ChatNVIDIA(model=model, api_key=api_key, base_url=base_url)
    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)
```

Invocation:

```python
result = agent.invoke({"messages": [HumanMessage(content=task)]})
response = result["messages"][-1].content
```

### Supervisor planning

The supervisor outputs one of two response types:

---
**When sub-agents are needed** -- a structured JSON plan:

```json
{
  "plan": "Add error handling to API client and write tests",
  "subtasks": [
    {"agent_type": "searcher", "description": "Locate api_client.py and its network calls", "relevant_files": []},
    {"agent_type": "coder", "description": "Wrap all HTTP calls in try/except blocks", "relevant_files": ["api_client.py"]},
    {"agent_type": "tester", "description": "Write tests covering timeout, HTTP errors, connection failures", "relevant_files": ["api_client.py"]}
  ]
}
```

**For simple questions** -- a direct text response:

```
The `run_command` tool executes PowerShell commands with a 60-second timeout
and captures both stdout and stderr. Exit codes are reported on failure.
```

---

## Tools

Seven primitives expose the filesystem and shell to sub-agents.

### Reference

| Tool | Signature | Behaviour |
|------|-----------|-----------|
| `read_file` | `(path) -> str` | Returns up to 50,000 characters |
| `write_file` | `(path, content) -> str` | Creates parent directories automatically |
| `edit_file` | `(path, old, new) -> str` | Replaces first occurrence only |
| `run_command` | `(command) -> str` | PowerShell, 60-second timeout |
| `grep_search` | `(pattern, include?) -> str` | Recursive regex, up to 30 matches |
| `glob_files` | `(pattern) -> str` | Recursive glob, up to 100 results |
| `list_directory` | `(path?) -> str` | Defaults to current directory |

### Excluded directories

```
node_modules    .git          __pycache__    .venv
venv            .env          .idea          .vscode
```

### Implementation pattern

```python
from langchain_core.tools import tool

@tool
def read_file(path: str) -> str:
    """Read the contents of a file. Returns up to 50000 characters."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(50000)
    except FileNotFoundError:
        return f"Error: file not found at {path}"
    except Exception as e:
        return f"Error reading file: {e}"
```

---

## Installation

### Prerequisites

- Python 3.11+
- NVIDIA API key ([build.nvidia.com](https://build.nvidia.com))
- pip

### Setup

```bash
# 1. Navigate to the project
cd C:\Users\spide\Downloads\Projects\Agent

# 2. Create virtual environment (recommended)
python -m venv .venv

# 3. Activate it
.\.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure API key
echo NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx > .env
```

### Dependencies

```
Package                          Version          Purpose
───────                          ───────          ───────
langchain                        >=1.3.0          Agent framework
langchain-core                   >=0.3.0          Core abstractions
langchain-nvidia-ai-endpoints    >=0.3.0          NVIDIA API integration
langgraph                        >=0.2.0          Stateful graph orchestration
rich                             >=13.0.0         Terminal UI
python-dotenv                    >=1.0.0          Environment variables
```

---

## Usage

### Starting

```bash
python main.py
```

```
╭────────────────────────────────────────────────╮
│                   Welcome                      │
│                                                │
│             Prisma Agent                       │
│                                                │
│   Coordinates specialized sub-agents to        │
│   help complete tasks faster.                  │
│                                                │
│   Type your coding request below.              │
│   Use /help for commands.                      │ 
╰────────────────────────────────────────────────╯
```

### Commands

| Input | Action |
|-------|--------|
| `your coding request` | Delegate a task to the agent |
| `/help` | Display available commands |
| `/clear` | Reset conversation history |
| `/quit` | Exit the agent |

### Examples

```
You > What does the run_command tool do?
```

```
Prisma
┌────────────────────────────────────────────────┐
│ The run_command tool executes PowerShell       │
│ commands on Windows with a 60-second timeout   │
│ and returns stdout + stderr output. Exit       │
│ codes are reported on failure.                 │
└────────────────────────────────────────────────┘
```

```
You > Add error handling to the API client and write tests
```

```
Prisma
┌────────────────────────────────────────────────┐
│ Results                                        │
│                                                │
│  1. Found api_client.py at src/client/         │
│  2. Added try/except wrappers around all 6     │
│     network calls                              │
│  3. Wrote 8 test cases covering:               │
│     - Timeout errors                           │
│     - HTTP 4xx / 5xx responses                 │
│     - Connection failures                      │
│  4. All tests pass                             │
└────────────────────────────────────────────────┘
```

---

## Testing

### Running

```bash
# Full suite
pytest tests/ -v

# Single file
pytest tests/test_tools.py -v

# With coverage
pytest tests/ --cov=agent --cov-report=term-missing
```

### Test structure

```
tests/
├── test_tools.py          Unit tests for all 7 tools
├── test_state.py          TypedDict schema validation
├── test_sub_agents.py     Agent factory and creation
└── test_integration.py    End-to-end graph flow
```

### Examples

```python
def test_write_and_read_file(tmp_path):
    path = tmp_path / "test.txt"
    write_result = write_file.invoke({"path": str(path), "content": "hello"})
    assert "Wrote" in write_result

    read_result = read_file.invoke({"path": str(path)})
    assert read_result == "hello"


def test_edit_file(tmp_path):
    path = tmp_path / "edit.txt"
    path.write_text("foo bar baz")
    result = edit_file.invoke({"path": str(path), "old_string": "bar", "new_string": "qux"})
    assert "Edited" in result
    assert path.read_text() == "foo qux baz"


def test_grep_search(tmp_path):
    py_file = tmp_path / "example.py"
    py_file.write_text("def hello():\n    pass\n")
    result = grep_search.invoke({"pattern": "def hello", "include": "*.py"})
    assert "example.py" in result
```

---

## Configuration

### config.py

| Parameter | Default | Description |
|-----------|---------|-------------|
| `NVIDIA_API_KEY` | *(from .env)* | NVIDIA inference API key |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | API endpoint |
| `SUPERVISOR_MODEL` | `meta/llama-3.1-70b-instruct` | LLM for supervisor node |
| `SUB_AGENT_MODEL` | `meta/llama-3.1-70b-instruct` | LLM for sub-agent nodes |

### Environment

```env
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Override at runtime:

```bash
set NVIDIA_API_KEY=nvapi-yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
set SUPERVISOR_MODEL=meta/llama-3.1-405b-instruct
python main.py
```

---

## LangGraph internals

### Graph nodes

```
analyze
  Input:  messages (conversation history)
  Output: subtasks[]  |  messages[] (direct)
  Logic:  LLM routes to plan or direct response

execute_plan
  Input:  subtasks[]
  Output: subtasks[] with results
  Logic:  ThreadPoolExecutor -> parallel sub-agents

synthesize
  Input:  subtasks[] (populated)
  Output: messages[] (final AI response)
  Logic:  LLM condenses all results
```

### Edge routing

```python
def route_after_analyze(state):
    if state.get("subtasks"):
        return "execute_plan"
    return END
```

### Graph compilation

```python
workflow = StateGraph(AgentState)
workflow.add_node("analyze", analyze)
workflow.add_node("execute_plan", execute_plan)
workflow.add_node("synthesize", synthesize)
workflow.add_edge(START, "analyze")
workflow.add_conditional_edges("analyze", route_after_analyze)
workflow.add_edge("execute_plan", "synthesize")
workflow.add_edge("synthesize", END)

graph = workflow.compile()
```

---

## Performance

### Parallel speedup

| Strategy | Behaviour | Total time |
|----------|-----------|------------|
| Sequential | Sub-agents run one after another | sum of all agent times |
| **Parallel** | Up to 4 sub-agents concurrently | **max** of all agent times |

*Estimated 2-4x speedup for tasks with 3+ independent subtasks.*

### Known limitations

| Constraint | Effect | Workaround |
|------------|--------|------------|
| API rate limits | Degraded throughput at high concurrency | Reduce `max_workers` in `supervisor.py` |
| LLM context window | Large files may overflow token budget | Use `read_file` with offsets |
| Windows PowerShell | Some shell syntax differs from POSIX | Tool signatures stay agnostic |
| No web search | Agent cannot browse documentation | Planned feature |

---

## Development

### Project tree

```
Agent/
├── main.py                       CLI entry point
├── config.py                     Configuration
├── requirements.txt              Dependencies
├── .env                          API key (gitignored)
├── .gitignore
├── README.md
│
├── agent/
│   ├── __init__.py
│   ├── state.py                  TypedDict schemas
│   ├── tools.py                  7 tool implementations
│   ├── supervisor.py             LangGraph graph definition
│   │
│   └── sub_agents/
│       ├── __init__.py
│       ├── base.py               Agent factory (create_agent)
│       ├── coder.py              Code writing prompt + factory
│       ├── debugger.py           Bug diagnosis prompt + factory
│       ├── searcher.py           Code search prompt + factory
│       ├── tester.py             Test writing prompt + factory
│       └── spawner.py            Dynamic agent factory
│
└── utils/
    ├── __init__.py
    └── display.py                Rich console utilities
```

### Adding a sub-agent

```python
# agent/sub_agents/refactorer.py
from .base import create_sub_agent
from ..tools import TOOLS

REFACTORER_PROMPT = """You are a code refactoring expert..."""

def create_refactorer(model, api_key, base_url):
    return create_sub_agent(
        model=model, api_key=api_key, base_url=base_url,
        system_prompt=REFACTORER_PROMPT,
        tools=TOOLS,
    )
```

Register in `agent/supervisor.py`:

```python
from .sub_agents.refactorer import create_refactorer

AGENT_FACTORY["refactorer"] = lambda: create_refactorer(...)
```

Then add the agent to the supervisor prompt so the LLM knows it exists.

### Adding a tool

```python
# agent/tools.py
@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # implementation
```

Append to the export list:

```python
TOOLS = [read_file, write_file, edit_file, run_command, grep_search, glob_files, list_directory, search_web]
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `NVIDIA_API_KEY not set` | Missing or default key | Set in `.env` or environment |
| `No module named 'langchain'` | Missing dependency | `pip install -r requirements.txt` |
| Sub-agents run sequentially | API rate limiting | Reduce `max_workers` to 2 |
| `Command timed out` | Shell command exceeded 60s | Increase timeout in `tools.py` |
| `string not found in file` | Ambiguous `old_string` | Include surrounding context for uniqueness |

---

<p align="center">
  <sub>Built with Python, LangGraph, and LangChain</sub><br>
  <sub>License: MIT</sub>
</p>
