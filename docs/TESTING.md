# Testing

## Running Tests

```bash
PRISMA_TEST_MODE=1 python -m pytest tests/ -v
```

`PRISMA_TEST_MODE=1` bypasses the filesystem sandbox so tools can write to temporary directories during tests.

## Test Files

| File | Tests | What it covers |
|---|---|---|
| `tests/test_tools.py` | 28 | All 8 tool functions — file I/O, command execution, grep/glob, web search |
| `tests/test_state.py` | 6 | TypedDict schema validation for `SubTask` and `AgentState` |
| `tests/test_sub_agents.py` | 9 | Sub-agent factory functions, tool assignments, THINKING flag |
| `tests/test_cli_ux.py` | 3 | Command dispatch, mode toggle, pending request queue |
| `tests/test_integration.py` | 11 | Full LangGraph supervisor: analyze, execute, synthesize, plan vs build routing |

**Total:** 57 tests

## Key Test Patterns

**Web search tests** use `monkeypatch` to set API keys and `@patch` to mock `requests.post`/`requests.get`.

**Sub-agent tests** patch `agent.sub_agents.base.ChatOpenAI` and `create_sub_agent` to avoid real LLM calls.

**Integration tests** patch `agent.supervisor.ChatOpenAI` to return canned responses, then call `graph.invoke()` and assert on the returned state.

## Running Specific Tests

```bash
# Single test file
PRISMA_TEST_MODE=1 python -m pytest tests/test_tools.py -v

# Specific test
PRISMA_TEST_MODE=1 python -m pytest tests/test_tools.py::test_read_file -v

# With coverage
PRISMA_TEST_MODE=1 python -m pytest tests/ --cov=agent --cov=utils -v
```
