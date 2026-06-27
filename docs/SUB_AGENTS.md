# Sub-Agents

The supervisor decomposes tasks into subtasks and assigns each to the appropriate agent. Agents run in parallel (up to 4 concurrent workers).

## Available Agents

### Coder
**Role:** Writes, reads, and modifies code files.

Has access to all 8 tools. Instructions:
- Follow existing code style
- Read files before modifying
- Make minimal, focused changes
- Verify changes by re-reading

### Debugger
**Role:** Finds and diagnoses bugs in code.

Tools: `read_file`, `run_command`, `grep_search`, `glob_files`, `list_directory`

Instructions:
- Understand the full error context
- Try to reproduce the issue
- Identify the root cause with exact file paths and line numbers
- Suggest the fix but do not apply it

### Searcher
**Role:** Finds files, code patterns, and information in the project AND searches the web for documentation, APIs, and solutions.

Tools: `read_file`, `grep_search`, `glob_files`, `list_directory`, `search_web`

Instructions:
- Use multiple search strategies
- Provide complete file paths and code snippets for local results
- Cite source URLs for web results

### Tester
**Role:** Writes and runs tests.

Has access to all 8 tools. Instructions:
- Read and understand the code being tested first
- Use the existing test framework (pytest)
- Cover normal cases, edge cases, and error paths
- Run tests after writing to verify they pass

### Spawn (dynamic agent)
**Role:** For tasks that don't fit the above roles (e.g., configuration, docs, setup, etc.)

Has access to all 8 tools. Used as fallback when the supervisor assigns an `agent_type` not in `["coder", "debugger", "searcher", "tester"]`.

## Tool Access Matrix

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

## How Agents are Invoked

Each agent receives a single `HumanMessage` with the subtask description. It runs a ReAct-style tool loop internally until it produces a final response. The supervisor extracts the last AI message as the result.

All agents share the same LLM hyperparameters: `temperature=1.0`, `top_p=0.95`, `max_tokens=16384`.
