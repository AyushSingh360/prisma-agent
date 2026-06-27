# Prisma — Complete Wiki & Documentation

**A terminal-based multi-agent coding assistant that coordinates specialized sub-agents to handle complex development tasks.**

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Configuration](#configuration)
5. [Execution Modes](#execution-modes)
6. [Sub-Agents](#sub-agents)
7. [Tools](#tools)
8. [Commands](#commands)
9. [Terminal UI](#terminal-ui)
10. [Testing](#testing)

---

## Overview

Prisma is a stateful, parallel multi-agent coding assistant built on LangGraph and LangChain. It runs as an interactive terminal application where you describe tasks and Prisma plans, delegates to specialized agents, executes in parallel, and synthesizes results.

### How It Works

1. **You type a request** in the interactive terminal prompt
2. **Supervisor agent analyzes** it and either answers directly or decomposes into subtasks
3. **Specialized sub-agents run in parallel** (coder, debugger, searcher, tester, spawn)
4. **Supervisor synthesizes results** into a single clean response

---

## Quick Start

### Installation

```bash
git clone https://github.com/<your-username>/prisma-agent
cd prisma-agent
pip install -r requirements.txt
```

### Configuration

Copy `.env` and add an API key:

```env
# Choose ONE provider

# Option 1: Groq (free tier available)
GROQ_API_KEY=gsk_...

# Option 2: OpenRouter (supports many models)
OPENROUTER_API_KEY=sk-or-...

# Option 3: NVIDIA AI Endpoints
NVIDIA_API_KEY=nvapi-...

# Optional: Web search (default: tavily)
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-...
```

### Run

```bash
python main.py
```

You'll see an interactive prompt. Type a request or press `/help` to see all commands.

---

## Architecture

### Project Structure

```
prisma-agent/
├── main.py                    # Entry point, main loop
├── config.py                  # Environment variables, provider routing
├── requirements.txt
├── agent/
│   ├── state.py              # Shared LangGraph state schema
│   ├── supervisor.py         # LangGraph graph definition
│   ├── tools.py              # 8 LangChain tools
│   └── sub_agents/
│       ├── base.py           # Shared agent factory
│       ├── coder.py
│       ├── debugger.py
│       ├── searcher.py
│       ├── tester.py
│       └── spawner.py
├── utils/
│   ├── theme.py              # Design tokens, colors, icons
│   ├── renderers.py          # Rich UI renderables
│   ├── layout.py             # Terminal layout manager
│   ├── animations.py         # Spinner, live display
│   ├── input.py              # prompt_toolkit input session
│   ├── commands.py           # Slash command dispatch
│   └── display.py            # Backward-compat shim
└── tests/
    ├── test_tools.py
    ├── test_state.py
    ├── test_sub_agents.py
    ├── test_cli_ux.py
    └── test_integration.py
```

### Data Flow Per Turn

```
User Input (prompt_toolkit)
  │
  ├─ Slash command? 
  │   └─ handle_command() → output or state change → continue
  │
  └─ Normal request
      └─ LiveManager.run_with_spinner()
          └─ graph.invoke()
              ├─ analyze node
              │   └─ Supervisor LLM reads request
              │       ├─ Plain text → AIMessage → END
              │       └─ JSON plan → SubTask list → route
              │           │
              │     ┌─────┴──────┐
              │   PLAN mode    BUILD mode
              │     │              │
              │    END         execute_plan node
              │                  (4 parallel workers)
              │                     │
              │                synthesize node
              │                (Supervisor LLM again)
              │                     │
              │                    END
              │
          └─ render results (Rich panels)
```

### State Schema

```python
class SubTask(TypedDict):
    agent_type: str          # "coder" | "debugger" | "searcher" | "tester" | "spawn"
    description: str         # Detailed instruction
    status: str              # "pending" | "completed" | "failed"
    result: Optional[str]    # Agent output
    relevant_files: list[str]

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # Full history
    subtasks: list[SubTask]  # Current turn's tasks
    mode: str                # "build" | "plan"
```

### LangGraph

```
START → analyze → [conditional] → execute_plan → synthesize → END
                        └──────────────────────────────────────→ END
```

**Routing condition:** If `subtasks` populated AND `mode == "build"` → `execute_plan`; else → `END`

---

## Configuration

### API Keys

| Variable | Provider | Notes |
|---|---|---|
| `GROQ_API_KEY` | [Groq](https://console.groq.com) | Must start with `gsk_` |
| `OPENROUTER_API_KEY` | [OpenRouter](https://openrouter.ai) | Prefix `sk-or-` |
| `NVIDIA_API_KEY` | [NVIDIA NIM](https://integrate.api.nvidia.com) | Prefix `nvapi-` |

Only one is required. Prisma auto-detects which is available.

### Provider Routing

Based on the model name:

| Model contains | Provider | Base URL |
|---|---|---|
| `gemini` or `google/` | OpenRouter | `https://openrouter.ai/api/v1` |
| `minimax` or `nvidia` | NVIDIA NIM | `https://integrate.api.nvidia.com/v1` |
| `llama`, `mixtral`, `gemma` | Groq | `https://api.groq.com/openai/v1` |
| anything else | OpenRouter | `https://openrouter.ai/api/v1` |

### Default Models

| If available | Default model |
|---|---|
| `NVIDIA_API_KEY` | `minimaxai/minimax-m3` |
| `OPENROUTER_API_KEY` | `google/gemini-2.5-flash` |
| `GROQ_API_KEY` | `llama-3.3-70b-versatile` |

### Model Overrides

```env
SUPERVISOR_MODEL=google/gemini-2.5-flash
SUB_AGENT_MODEL=llama-3.3-70b-versatile
```

Use different models for supervisor (planning) and sub-agents (execution).

### Base URL Overrides

```env
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
GROQ_BASE_URL=https://api.groq.com/openai/v1
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

### LLM Hyperparameters

| Parameter | Value | Can override? |
|---|---|---|
| `TEMPERATURE` | `1.0` | No (hardcoded) |
| `TOP_P` | `0.95` | No (hardcoded) |
| `MAX_TOKENS` | `16384` | No (hardcoded) |
| `THINKING` | `False` | Yes (`/think` command) |

### Search Configuration

```env
SEARCH_PROVIDER=tavily        # "tavily" | "brave" | "google"
TAVILY_API_KEY=tvly-...
BRAVE_API_KEY=BSA...
GOOGLE_API_KEY=AIza...
GOOGLE_CSE_ID=...
```

---

## Execution Modes

### Build Mode (default)

Supervisor plans **and immediately executes**.

```
analyze → subtasks populated → execute_plan → synthesize → END
```

**Use when:** You want results immediately.

### Plan Mode

Supervisor produces a plan but **does not execute**.

```
analyze → subtasks populated → END (render plan card, queue request)
```

**Use when:** You want to review the plan before execution.

### Switching Modes

- Press `Tab` to toggle between modes
- Status bar shows current mode: `BUILD` or `PLAN`
- Switching PLAN → BUILD with a queued request **auto-executes** it
- Pending requests shown in status: `· queued`

### The Pending Request Queue

1. In PLAN mode, after seeing a plan, the original request is stored
2. Status bar shows `· queued`
3. Press `Tab` to switch to BUILD — stored request runs immediately
4. Pending request is cleared after execution or with `/clear`

---

## Sub-Agents

Each agent is specialized for a role. Supervisor decomposes tasks into subtasks and assigns to appropriate agents. Agents run in parallel (max 4 concurrent).

### Coder

**Role:** Write, read, and modify code files.

**Tools:** All 8 (read, write, edit, run, grep, glob, list, search)

**Instructions:**
- Follow existing code style
- Read files before modifying
- Make minimal, focused changes
- Verify changes by re-reading

### Debugger

**Role:** Diagnose bugs. Does not write code.

**Tools:** `read_file`, `run_command`, `grep_search`, `glob_files`, `list_directory`

**Instructions:**
- Understand full error context
- Reproduce if possible
- Identify root cause with exact file paths and line numbers
- Suggest fix but do not apply it

### Searcher

**Role:** Find files, code patterns, and information.

**Tools:** `read_file`, `grep_search`, `glob_files`, `list_directory`, `search_web`

**Instructions:**
- Use multiple search strategies
- Provide complete file paths and code snippets for local results
- Cite source URLs for web results

### Tester

**Role:** Write and run tests. Fixes failing tests.

**Tools:** All 8 (read, write, edit, run, grep, glob, list, search)

**Instructions:**
- Read and understand code being tested first
- Use existing test framework (pytest)
- Cover normal, edge, and error cases
- Run tests after writing to verify they pass

### Spawn (dynamic)

**Role:** Handle anything else — config, docs, setup, analysis.

**Tools:** All 8

Used as fallback when supervisor assigns an unknown `agent_type`.

### Tool Access Matrix

| Tool | Coder | Debugger | Searcher | Tester | Spawn |
|---|:---:|:---:|:---:|:---:|:---:|
| `read_file` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `write_file` | ✓ | | | ✓ | ✓ |
| `edit_file` | ✓ | | | ✓ | ✓ |
| `run_command` | ✓ | ✓ | | ✓ | ✓ |
| `grep_search` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `glob_files` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `list_directory` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `search_web` | | | ✓ | | ✓ |

---

## Tools

All tools are LangChain `@tool`-decorated functions available to sub-agents.

### Security Model

- **File tools** (`read_file`, `write_file`, `edit_file`) are sandboxed to repo root via path resolution
- **Command execution** is whitelist-restricted to safe commands only
- **Recursive search** skips: `node_modules`, `.git`, `__pycache__`, `.venv`, `venv`, `.env`, `.idea`, `.vscode`

### File Tools

#### `read_file(path: str) -> str`

Read file contents. Returns up to 50,000 characters.

- Returns `"(binary file, cannot read as text)"` for binary files
- Returns `"Error: file not found at {path}"` if missing
- Sandboxed to repo root

#### `write_file(path: str, content: str) -> str`

Write content to a file. Creates parent directories automatically.

- Returns `"Wrote {N} bytes to {path}"` on success
- Overwrites existing files

#### `edit_file(path: str, old_string: str, new_string: str) -> str`

Replace the **first occurrence** of `old_string` with `new_string`.

- Returns `"Error: string not found in {path}"` if not found
- Returns `"Edited {path}"` on success

### Command Execution

#### `run_command(command: str) -> str`

Run a PowerShell command. Returns combined stdout + stderr.

- **Whitelist-restricted** to safe commands only
- 60-second timeout
- Stdout capped at 8,000 chars; stderr capped at 2,000 chars
- Non-zero exit codes appended to output

**Allowed commands:** `pytest`, `python`, `pip`, `git`, `dir`, `ls`, `echo`, `Get-ChildItem`, `Set-Content`, `Remove-Item`

### Search Tools

#### `grep_search(pattern: str, include: str = None) -> str`

Search file contents using regex pattern.

- Optional `include` to filter by file type (e.g., `"*.py"`)
- Returns up to 30 matches in format `path:line_number: content`
- Returns `"Invalid regex pattern"` for bad regex

#### `glob_files(pattern: str) -> str`

Find files matching a glob pattern (e.g., `**/*.py`, `src/**/*.ts`).

- Returns up to 100 matching relative paths
- If no matches, automatically retries with `**/{pattern}`

#### `list_directory(path: str = ".") -> str`

List files and directories at a path. Skips dotfiles.

- Appends `/` to directory names
- Returns entries sorted alphabetically

### Web Search

#### `search_web(query: str, max_results: int = 5) -> str`

Search the web. Provider selected by `SEARCH_PROVIDER` in `.env`.

| Provider | API key needed | Endpoint |
|---|---|---|
| `tavily` (default) | `TAVILY_API_KEY` | `api.tavily.com/search` |
| `brave` | `BRAVE_API_KEY` | `api.search.brave.com` |
| `google` | `GOOGLE_API_KEY` + `GOOGLE_CSE_ID` | `googleapis.com/customsearch/v1` |

All providers return title, URL, and snippet per result. Tavily also returns a direct answer. All have 30-second timeout.

---

## Commands

All commands are prefixed with `/`. Type `/` then start typing for tab completion.

### Basic Commands

| Command | Description |
|---|---|
| `/help` | Show all available commands with descriptions |
| `/clear` | Clear conversation history and subtask queue |
| `/quit` or `/exit` | Exit Prisma |

### Info Commands

| Command | Description |
|---|---|
| `/model` | Show active supervisor model, sub-agent model, and provider URL |
| `/agents` | List all available sub-agents with role descriptions |
| `/status` | Show current session stats (message count, subtask count) |
| `/config` | Show full configuration: models, provider, temperature, top_p, max_tokens, thinking flag |

### Advanced Commands

| Command | Description |
|---|---|
| `/think` | Toggle reasoning/thinking mode on/off and rebuild the agent graph |
| `/retry` | Pop the last exchange and re-run the most recent human message |
| `/export` | Save the full conversation as a Markdown file (`prisma-export-YYYYMMDD-HHMMSS.md`) |

---

## Terminal UI

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Enter` | Send message |
| `Tab` | Toggle between BUILD and PLAN mode |
| `Ctrl+J` | Insert a newline (multi-line input) |
| `Ctrl+L` | Clear the terminal screen |
| `Ctrl+C` | Exit Prisma |
| `↑` / `↓` | Navigate command history |

### Status Bar

Shown above the input prompt every turn:

```
◆ Prisma · llama-3.3-70b-versatile · BUILD · queued          ~25 tokens · Turn 3 · 2.1s
```

**Fields:**
- Mode indicator: `BUILD` or `PLAN`
- Pending request indicator: `· queued`
- Token estimate: `~N tokens` (rough context size)
- Turn count: `Turn N` (number of completed exchanges)
- Latency: `N.Ns` (last response time)

### Message Panels

| Panel | When shown |
|---|---|
| **Plan card** | PLAN mode — shows agent assignments with descriptions |
| **Execution group** | BUILD mode — shows each subtask result status |
| **Assistant message** | Every response — final synthesized reply with Markdown rendering |
| **Error panel** | On exceptions — shows error message in red |
| **Notification** | Mode switches, retries, exports — inline status toasts |

### Color Theme

Dark blue/cyan palette defined in `utils/theme.py`.

| Color role | Hex |
|---|---|
| Primary (cyan-blue) | `#6EC6FF` |
| Accent (bright) | `#A0DCFF` |
| Success (green) | `#10B981` |
| Warning (amber) | `#F59E0B` |
| Error (red) | `#EF4444` |
| Background | `#0B1220` |
| Surface | `#111827` |

**Agent colors:**

| Agent | Color |
|---|---|
| coder | Blue `#3B82F6` |
| debugger | Purple `#A855F7` |
| searcher | Cyan `#06B6D4` |
| tester | Green `#10B981` |
| spawn | Amber `#F59E0B` |

---

## Testing

### Running Tests

```bash
PRISMA_TEST_MODE=1 python -m pytest tests/ -v
```

`PRISMA_TEST_MODE=1` bypasses filesystem sandbox so tools can write to temporary test directories.

### Test Files

| File | Tests | Coverage |
|---|---|---|
| `test_tools.py` | 28 | All 8 tool functions (file I/O, command execution, search, web) |
| `test_state.py` | 6 | TypedDict schema validation for `SubTask` and `AgentState` |
| `test_sub_agents.py` | 9 | Sub-agent factories, tool assignments, THINKING flag |
| `test_cli_ux.py` | 3 | Command dispatch, mode toggle, pending request queue |
| `test_integration.py` | 11 | Full LangGraph: analyze, execute, synthesize, routing |

**Total:** 57 tests

### Test Patterns

- **Web search tests** use `monkeypatch` for API keys and `@patch` for mocking HTTP calls
- **Sub-agent tests** patch `ChatOpenAI` to avoid real LLM calls
- **Integration tests** patch supervisor LLM and verify state flow through graph

### Running Specific Tests

```bash
# Single test file
PRISMA_TEST_MODE=1 python -m pytest tests/test_tools.py -v

# Specific test
PRISMA_TEST_MODE=1 python -m pytest tests/test_tools.py::test_read_file -v

# With coverage
PRISMA_TEST_MODE=1 python -m pytest tests/ --cov=agent --cov=utils -v
```

---

## Example Usage

### Example 1: Write a feature

```
prisma [build] ❯ write a python function that parses JSON from a file
```

→ Supervisor decomposes into subtasks:
1. **coder**: Write the function
2. **tester**: Write tests for it
3. **searcher**: Look up JSON parsing best practices

→ All agents run in parallel
→ Results synthesized into a response

### Example 2: Debug an error

```
prisma [build] ❯ i'm getting "AttributeError: 'NoneType' object has no attribute 'name'" on line 42
```

→ Supervisor sends to **debugger**:
1. Read the file around line 42
2. Identify root cause
3. Suggest fix (doesn't apply it)

→ Response shows exact issue and proposed solution

### Example 3: Review before execution

```
prisma [plan] ❯ refactor the utils module to use dataclasses instead of TypedDicts
```

→ BUILD mode off; supervisor creates a plan
→ Plan is displayed without executing
→ Press `Tab` to switch to BUILD and execute
→ Or press `Tab` again to stay in PLAN and keep reviewing

---

## Troubleshooting

### "API key not set"

Make sure your `.env` has one of:
- `GROQ_API_KEY=gsk_...`
- `OPENROUTER_API_KEY=sk-or-...`
- `NVIDIA_API_KEY=nvapi-...`

### "Command not allowed"

Only whitelisted commands can be run. Use tools like `grep_search`, `glob_files`, `read_file` instead, or request that the coder agent run the command.

### "Search timed out"

Web search has a 30-second timeout. Check your internet connection or try a simpler query.

### Tests failing outside of test mode

Make sure to set `PRISMA_TEST_MODE=1` when running tests, or they'll fail on filesystem sandbox checks.

---

## Requirements

- Python 3.11+
- At least one API key (Groq / OpenRouter / NVIDIA)
- Optional: Web search API key (Tavily / Brave / Google)

---

## Dependencies

See `requirements.txt`:

```
langgraph>=0.2.0          # LangGraph state orchestration
langchain-core>=0.3.0     # BaseMessage, tools
langchain-openai>=0.3.0   # ChatOpenAI (all 3 providers via base_url)
langchain-nvidia-ai-endpoints>=0.4.0
rich>=13.0.0              # Terminal UI
python-dotenv>=1.0.0      # .env loading
requests>=2.31.0          # HTTP calls
prompt_toolkit>=3.0.0     # Interactive input
typer>=0.12.0             # CLI framework
langchain>=1.3.0          # Agent factory
```

---

**Last updated:** 2026-06-27  
**Version:** 1.0.0
