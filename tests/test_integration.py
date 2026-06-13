"""Integration tests for the supervisor graph."""

import json
from unittest.mock import patch, MagicMock

from agent.supervisor import (
    build_supervisor_graph,
    _extract_json,
    SUPERVISOR_PROMPT_TEMPLATE,
    AGENT_FACTORY,
)


def test_extract_json_plain():
    assert _extract_json('{"a": 1}') == '{"a": 1}'


def test_extract_json_with_code_fence():
    text = '```json\n{"plan": "test", "subtasks": []}\n```'
    assert json.loads(_extract_json(text)) == {"plan": "test", "subtasks": []}


def test_extract_json_with_fence_and_lang():
    text = '```\n{"key": "value"}\n```'
    assert json.loads(_extract_json(text)) == {"key": "value"}


def test_extract_json_strips_whitespace():
    assert _extract_json('  {"x": 1}  ') == '{"x": 1}'


def test_agent_factory_keys():
    assert "coder" in AGENT_FACTORY
    assert "debugger" in AGENT_FACTORY
    assert "searcher" in AGENT_FACTORY
    assert "tester" in AGENT_FACTORY


def test_supervisor_prompt_contains_agents():
    prompt = SUPERVISOR_PROMPT_TEMPLATE.format(mode="build")
    assert "coder" in prompt
    assert "debugger" in prompt
    assert "searcher" in prompt
    assert "tester" in prompt
    assert "spawn" in prompt


def test_supervisor_prompt_mode_injection():
    build_prompt = SUPERVISOR_PROMPT_TEMPLATE.format(mode="build")
    plan_prompt = SUPERVISOR_PROMPT_TEMPLATE.format(mode="plan")
    assert "MODE: build" in build_prompt
    assert "MODE: plan" in plan_prompt


@patch("agent.supervisor.ChatNVIDIA")
def test_analyze_direct_response(mock_chat):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Hello! I can help with that."
    mock_llm.invoke.return_value = mock_response
    mock_chat.return_value = mock_llm

    graph = build_supervisor_graph()
    result = graph.invoke({
        "messages": [],
        "subtasks": [],
        "mode": "build",
    })

    assert "messages" in result
    assert len(result["messages"]) >= 1
    assert "Hello" in result["messages"][-1].content


@patch("agent.supervisor.ChatNVIDIA")
def test_analyze_returns_plan(mock_chat):
    mock_llm = MagicMock()
    plan_json = json.dumps({
        "plan": "Fix the bug and write tests",
        "subtasks": [
            {
                "agent_type": "searcher",
                "description": "Find the relevant code",
                "relevant_files": [],
            },
            {
                "agent_type": "coder",
                "description": "Fix the bug",
                "relevant_files": ["main.py"],
            },
        ],
    })
    mock_response = MagicMock()
    mock_response.content = plan_json
    mock_llm.invoke.return_value = mock_response
    mock_chat.return_value = mock_llm

    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {
        "messages": [MagicMock(type="ai", content="done!")]
    }

    graph = build_supervisor_graph()
    with patch.dict("agent.supervisor.AGENT_FACTORY", {"coder": lambda: mock_agent, "searcher": lambda: mock_agent}):
        result = graph.invoke({
            "messages": [],
            "subtasks": [],
            "mode": "build",
        })

    assert "subtasks" in result
    assert len(result["subtasks"]) == 2
    assert result["subtasks"][0]["agent_type"] == "searcher"
    assert result["subtasks"][1]["agent_type"] == "coder"


@patch("agent.supervisor.ChatNVIDIA")
def test_plan_mode_does_not_execute(mock_chat):
    mock_llm = MagicMock()
    plan_json = json.dumps({
        "plan": "Some plan",
        "subtasks": [
            {
                "agent_type": "coder",
                "description": "Write code",
                "relevant_files": [],
            },
        ],
    })
    mock_response = MagicMock()
    mock_response.content = plan_json
    mock_llm.invoke.return_value = mock_response
    mock_chat.return_value = mock_llm

    graph = build_supervisor_graph()
    result = graph.invoke({
        "messages": [],
        "subtasks": [],
        "mode": "plan",
    })

    assert "subtasks" in result
    assert len(result["subtasks"]) == 1
    assert result["subtasks"][0]["status"] == "pending"
    assert result["subtasks"][0]["result"] is None


@patch("agent.supervisor.ChatNVIDIA")
def test_execute_plan_runs_agents(mock_chat):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "plan": "test",
        "subtasks": [
            {"agent_type": "coder", "description": "do something", "relevant_files": []},
        ],
    })
    mock_llm.invoke.return_value = mock_response
    mock_chat.return_value = mock_llm

    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {
        "messages": [MagicMock(type="ai", content="done!")]
    }

    with patch.dict("agent.supervisor.AGENT_FACTORY", {"coder": lambda: mock_agent}):
        graph = build_supervisor_graph()
        result = graph.invoke({
            "messages": [],
            "subtasks": [],
            "mode": "build",
        })

    subtasks = result.get("subtasks", [])
    assert len(subtasks) >= 1
    if subtasks:
        assert subtasks[0]["status"] == "completed"


@patch("agent.supervisor.ChatNVIDIA")
def test_synthesize_generates_summary(mock_chat):
    mock_llm = MagicMock()
    analyze_response = MagicMock()
    analyze_response.content = json.dumps({
        "plan": "test",
        "subtasks": [
            {"agent_type": "tester", "description": "write tests", "relevant_files": []},
        ],
    })
    synthesize_response = MagicMock()
    synthesize_response.content = "Here is a summary of what was done."

    mock_llm.invoke.side_effect = [analyze_response, synthesize_response]
    mock_chat.return_value = mock_llm

    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {
        "messages": [MagicMock(type="ai", content="wrote 5 tests")]
    }

    with patch.dict("agent.supervisor.AGENT_FACTORY", {"tester": lambda: mock_agent}):
        graph = build_supervisor_graph()
        result = graph.invoke({
            "messages": [],
            "subtasks": [],
            "mode": "build",
        })

    final_msg = result["messages"][-1]
    assert "summary" in final_msg.content.lower() or "Here is" in final_msg.content
