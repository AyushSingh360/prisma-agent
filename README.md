# Coding Agent

A **multi-agent coding assistant** built with Python, LangGraph, and LangChain. A supervisor agent intelligently decomposes coding tasks and spawns specialized sub-agents that work **in parallel** to complete work faster.

---

## Features

- **Intelligent Decomposition** — The supervisor analyzes your request and creates a plan with parallel subtasks
- **Parallel Execution** — Up to 4 sub-agents run simultaneously via `ThreadPoolExecutor`
- **5 Specialized Sub-Agents** — Coder, Debugger, Searcher, Tester, and a Dynamic Spawner for novel tasks
- **7 Tool Primitives** — Read, Write, Edit, Shell, Grep, Glob, List — same capabilities as an AI coding agent
- **CLI Chat Interface** — Rich terminal UI with markdown rendering and conversation history
- **LangGraph Orchestration** — Stateful graph-based workflow with checkpointing support
- **Conversation Memory** — Full message history preserved across turns
- **NVIDIA API** — Uses `meta/llama-3.1-70b-instruct` via OpenAI-compatible endpoint

---

## Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI (main.py)                               │
│                  Typer + Rich Console Interface                      │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LangGraph StateGraph                              │
│                                                                      │
│   ┌──────────┐     ┌──────────────┐     ┌──────────────┐           │
│   │  START   │────▶│   analyze    │────▶│ execute_plan │           │
│   └──────────┘     └──────┬───────┘     └──────┬───────┘           │
│                           │                     │                   │
│                   ┌───────▼───────┐             │                   │
│                   │  direct reps. │             │                   │
│                   │   → END       │             │                   │
│                   └───────────────┘             │                   │
│                                                  ▼                  │
│                                          ┌──────────────┐           │
│                                          │  synthesize  │           │
│                                          └──────┬───────┘           │
│                                                 │                   │
│                                                 ▼                   │
│                                          ┌──────────────┐           │
│                                          │     END      │           │
│                                          └──────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Sub-Agent Pool (Parallel)                         │
│                                                                      │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│   │  Coder   │  │ Debugger │  │ Searcher │  │  Tester  │          │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│        │              │              │              │               │
│        └──────────────┴──────────────┴──────────────┘               │
│                           │                                         │
│                    ┌──────▼──────┐                                  │
│                    │   Spawner   │  (dynamic, on-demand)            │
│                    └─────────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Tool Layer                                      │
│                                                                      │
│  read_file │ write_file │ edit_file │ run_command                    │
│  grep_search │ glob_files │ list_directory                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow (Request to Response)

```
User Input
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. analyze (Supervisor LLM)                 │
│    - Reads conversation history             │
│    - Decides: direct response or plan?      │
│    - If plan: decomposes into subtasks      │
│    - Output: JSON plan or free text         │
└─────────────────────┬───────────────────────┘
                      │
            ┌─────────▼─────────┐
            │  Has subtasks?    │
            └─────┬──────┬──────┘
                  │      │
         YES      │      │  NO
                  │      │
                  ▼      ▼
┌─────────────────────┐  ┌─────────────────────┐
│ 2. execute_plan     │  │ Return direct       │
│    - Map subtasks   │  │ response → END      │
│    - ThreadPool     │  └─────────────────────┘
│    - Run in parallel│
│    - Collect results│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 3. synthesize       │
│    - Build summary  │
│    - LLM condenses  │
│    - Returns final  │
└─────────┬───────────┘
          │
          ▼
      Final Response
```

### Sub-Agent Execution Flow

```
                    ThreadPoolExecutor(max_workers=4)
                    ┌─────────────────────────────────┐
                    │                                 │
  subtask[0] ───────┤  ┌─────────────────────────┐   │
  (coder)           │  │ Agent: Coder             │   │
                    │  │  - read_file(...)        │   │
  subtask[1] ───────┤  │  - edit_file(...)        │   │
  (debugger)        │  │  - run_command(...)      │   │
                    │  └─────────┬───────────────┘   │
  subtask[2] ───────┤  ┌─────────▼───────────────┐   │
  (searcher)        │  │ Agent: Debugger          │   │
                    │  │  - read_file(...)        │   │
  subtask[3] ───────┤  │  - grep_search(...)      │   │
  (tester)          │  └─────────┬───────────────┘   │
                    │            │                    │
                    │  Each agent runs its own       │
                    │  LLM tool-calling loop          │
                    └────────────┬────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Results aggregated      │
                    │  into state.subtasks[]   │
                    └─────────────────────────┘
```

### State Schema

```
AgentState (TypedDict)
├── messages: list[BaseMessage]    <- Conversation history (add_messages reducer)
└── subtasks: list[SubTask]        <- Current plan being executed
    ├── agent_type: str            <- coder | debugger | searcher | tester | spawn
    ├── description: str           <- Task description for sub-agent
    ├── status: str                <- pending | completed | failed
    ├── result: Optional[str]      <- Sub-agent output
    └── relevant_files: list[str]  <- File paths for context
```

---

## Sub-Agent System

### Agent Registry

| Agent | Type | Tools | Purpose |
|-------|------|-------|---------|
| **Coder** | Persistent | read, write, edit, bash, grep, glob, ls | Write and modify code files |
| **Debugger** | Persistent | read, bash, grep, glob, ls | Diagnose bugs and errors |
| **Searcher** | Persistent | read, grep, glob, ls | Find files and code patterns |
| **Tester** | Persistent | read, write, edit, bash, grep, glob, ls | Write and run tests |
| **Spawner** | Dynamic | read, write, edit, bash, grep, glob, ls | Handle novel tasks |

### Agent Creation (base.py)

```python
from langchain.agents import create_agent

def create_sub_agent(model, api_key, base_url, system_prompt, tools):
    llm = ChatNVIDIA(model=model, api_key=api_key, base_url=base_url)
    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)
```

Each sub-agent is a `CompiledStateGraph` created via LangChain's `create_agent`, which runs a tool-calling loop until the LLM produces a final response without tool calls. The agent is invoked as:

```python
result = agent.invoke({"messages": [HumanMessage(content=task_description)]})
response = result["messages"][-1].content
```

### How the Supervisor Plans

When you send a request, the supervisor LLM is prompted to output **either**:
1. **A JSON plan** (when sub-agents are needed):
   ```json
   {
     "plan": "Add error handling to API client and write tests",
     "subtasks": [
       {"agent_type": "searcher", "description": "Find api_client.py", "relevant_files": []},
       {"agent_type": "coder", "description": "Add try/except blocks", "relevant_files": ["api_client.py"]},
       {"agent_type": "tester", "description": "Write tests for error handling", "relevant_files": ["api_client.py"]}
     ]
   }
   ```
2. **A plain text response** (when no sub-agents are needed):
   ```
   I can help with that. Here is what you need to know...
   ```

---

## Tool Layer

All 7 tools are implemented as LangChain `@tool` decorated functions.

### Tool Reference

| Tool | Signature | Description |
|------|-----------|-------------|
| `read_file` | `(path: str) -> str` | Read up to 50K chars from a file |
| `write_file` | `(path: str, content: str) -> str` | Write content, auto-creates parent dirs |
| `edit_file` | `(path, old_string, new_string) -> str` | Replace first occurrence of text |
| `run_command` | `(command: str) -> str` | Execute PowerShell command (60s timeout) |
| `grep_search` | `(pattern, include=None) -> str` | Regex search across files (skips node_modules/.git) |
| `glob_files` | `(pattern: str) -> str` | Recursive glob pattern matching |
| `list_directory` | `(path: str = ".") -> str` | List directory contents (hides dotfiles) |

### Directory Skip List

The search tools automatically exclude these directories:
```
node_modules, .git, __pycache__, .venv, venv, .env, .idea, .vscode
```

### Tool Implementation Pattern

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

- **Python 3.11+**
- **NVIDIA API Key** (from build.nvidia.com)
- **pip** (Python package manager)

### Steps

```bash
# 1. Navigate to the project
cd C:\Users\spide\Downloads\Projects\Agent

# 2. Create virtual environment (recommended)
python -m venv .venv
.\.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
echo NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx > .env
```

### Dependencies

```
langchain>=1.3.0            Agent framework
langchain-core>=0.3.0       Core LangChain abstractions
langchain-nvidia-ai-endpoints  NVIDIA API integration
langgraph>=0.2.0            Stateful graph orchestration
rich>=13.0.0                Terminal UI formatting
python-dotenv>=1.0.0        Environment variable loading
```

---

## Usage

### Starting the Agent

```bash
python main.py
```

The welcome screen will appear:

```
╭──────────────────────────────────────────────╮
│  Welcome                                      │
│                                               │
│  Coding Agent                                 │
│  Coordinates specialized sub-agents to       │
│  help complete tasks faster.                 │
╰──────────────────────────────────────────────╯
```

### Commands

| Command | Description |
|---------|-------------|
| `your request...` | Send a coding task to the agent |
| `/help` | Show available commands |
| `/clear` | Reset conversation history |
| `/quit` or `exit` | Exit the agent |

### Example Sessions

**Simple question** (direct response, no sub-agents):
```
You > What does the `run_command` tool do?

Agent
┌──────────────────────────────────────────────┐
│ The `run_command` tool executes PowerShell   │
│ commands on Windows with a 60-second timeout │
│ and returns stdout + stderr output.          │
└──────────────────────────────────────────────┘
```

**Complex task** (parallel sub-agents):
```
You > Add error handling to the API client and write tests

Agent
┌──────────────────────────────────────────────┐
│ Results:                                      │
│                                               │
│ 1. Found api_client.py at src/client/         │
│ 2. Added try/except wrappers around all      │
│    6 network calls                            │
│ 3. Wrote 8 test cases covering:              │
│    - Timeout errors                           │
│    - HTTP 4xx/5xx responses                   │
│    - Connection failures                      │
│ 4. All tests pass                             │
└──────────────────────────────────────────────┘
```

---

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_tools.py -v

# Run with coverage
python -m pytest tests/ --cov=agent --cov-report=term-missing
```

### Test Structure

```
tests/
├── test_tools.py          # Unit tests for all 7 tools
├── test_state.py          # State schema validation
├── test_sub_agents.py     # Sub-agent factory tests
└── test_integration.py    # End-to-end graph flow tests
```

### Test Examples

```python
# test_tools.py
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

### Test Fixtures

```python
# conftest.py
import pytest
from agent.tools import read_file, write_file, edit_file

@pytest.fixture
def temp_workspace(tmp_path):
    """Provides a temporary workspace for tool tests."""
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(old_cwd)
```

---

## Configuration

### config.py

| Setting | Default | Description |
|---------|---------|-------------|
| `NVIDIA_API_KEY` | -- | Your NVIDIA API key (from .env) |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | API endpoint |
| `SUPERVISOR_MODEL` | `meta/llama-3.1-70b-instruct` | Model for supervisor LLM |
| `SUB_AGENT_MODEL` | `meta/llama-3.1-70b-instruct` | Model for sub-agent LLMs |

### Environment Variables (.env)

```env
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

You can also override config via environment variables:

```bash
set NVIDIA_API_KEY=nvapi-yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
set SUPERVISOR_MODEL=meta/llama-3.1-405b-instruct
python main.py
```

---

## How the Graph Works (LangGraph Detail)

### Node Definitions

```
Node: analyze
  Input:  state.messages (conversation history)
  Output: state.subtasks[] OR state.messages[] (direct response)
  Logic:  LLM decides plan vs. direct response

Node: execute_plan
  Input:  state.subtasks[]
  Output: state.subtasks[] with results populated
  Logic:  ThreadPoolExecutor -> parallel sub-agent invocation

Node: synthesize
  Input:  state.subtasks[] (with results)
  Output: state.messages[] (final AI message)
  Logic:  LLM summarizes sub-agent results
```

### Edge Routing

```python
def route_after_analyze(state):
    if state.get("subtasks"):    # Plan mode
        return "execute_plan"
    return END                    # Direct response mode
```

### Graph Compilation

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

## Performance Characteristics

### Parallel Speedup

```
Task: "Find all API routes, add logging, write tests"
Sequential:  Sub-agents run one at a time
             Total time ~ sum(all agent times)

Parallel:    Up to 4 sub-agents at once
             Total time ~ max(longest agent time)

Estimated speedup: 2-4x for tasks with 3+ independent subtasks
```

### Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| NVIDIA API rate limits | Slower with many concurrent agents | Reduce `max_workers` in supervisor.py |
| LLM context window | Large files may exceed token limit | Use `read_file` with offset/limit |
| PowerShell on Windows | Some commands differ from Linux | Tool handles translation |
| No web search | Cannot fetch external docs | Future enhancement |

---

## Development

### Adding a New Sub-Agent

1. Create the agent file in `agent/sub_agents/`:
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

2. Register it in `agent/supervisor.py`:
```python
from .sub_agents.refactorer import create_refactorer

AGENT_FACTORY = {
    # ... existing agents
    "refactorer": lambda: create_refactorer(SUB_AGENT_MODEL, NVIDIA_API_KEY, NVIDIA_BASE_URL),
}
```

3. Add it to the supervisor prompt so the LLM knows about it.

### Adding a New Tool

1. Add the tool function in `agent/tools.py`:
```python
@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Implementation
```

2. Add it to the `TOOLS` list at the bottom of `tools.py`:
```python
TOOLS = [read_file, write_file, edit_file, run_command, grep_search, glob_files, list_directory, search_web]
```

3. Write tests in `tests/test_tools.py`.

### Project Tree

```
Agent/
├── main.py                      CLI entry point
├── config.py                    Configuration
├── requirements.txt             Dependencies
├── .env                         API key (gitignored)
├── .gitignore
├── README.md                    This file
├── agent/
│   ├── __init__.py
│   ├── state.py                 TypedDict state schemas
│   ├── tools.py                 Tool implementations
│   ├── supervisor.py            LangGraph orchestration
│   └── sub_agents/
│       ├── __init__.py
│       ├── base.py              Agent factory
│       ├── coder.py             Code writing agent
│       ├── debugger.py          Bug diagnosis agent
│       ├── searcher.py          Code search agent
│       ├── tester.py            Test writing agent
│       └── spawner.py           Dynamic agent factory
└── utils/
    ├── __init__.py
    └── display.py               Rich console utilities
```

---

## Troubleshooting

### "NVIDIA_API_KEY not set"

Create a `.env` file in the project root with:
```
NVIDIA_API_KEY=nvapi-your-actual-key
```
Or set it as an environment variable:
```bash
set NVIDIA_API_KEY=nvapi-your-actual-key
python main.py
```

### "ModuleNotFoundError: No module named 'langchain'"

```bash
pip install -r requirements.txt
```

### Sub-agents not running in parallel

Check the `max_workers` parameter in `agent/supervisor.py:execute_plan`:
```python
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
```

Reduce to `2` if hitting API rate limits.

### "Command timed out"

The `run_command` tool has a 60-second timeout. For long-running commands, either:
- Modify the timeout in `agent/tools.py`
- Break the command into smaller steps

### "string not found in file" from edit_file

The `edit_file` tool replaces the **first occurrence** only. If the string appears multiple times, include more surrounding context in `old_string` to make it unique.

---

## Future Enhancements

- **Web search tool** -- Let sub-agents fetch documentation
- **Checkpoint persistence** -- Resume conversations across sessions
- **Streaming output** -- See sub-agent progress in real-time
- **Token usage tracking** -- Monitor API costs per session
- **Multi-model support** -- Use different models for different sub-agents
- **Git integration** -- Auto-commit, branch creation, PR generation
- **Docker/container support** -- Run commands in isolated environments

---

## Technical Stack

| Component | Technology |
|-----------|-----------|
| **Orchestration** | LangGraph 1.x `StateGraph` |
| **Agent Framework** | LangChain 1.x `create_agent` |
| **LLM API** | NVIDIA Inference (OpenAI-compatible) |
| **CLI** | Python `input()` + Rich |
| **Concurrency** | `concurrent.futures.ThreadPoolExecutor` |
| **State Management** | TypedDict + `add_messages` reducer |
| **Model** | `meta/llama-3.1-70b-instruct` |

---

## License

MIT
