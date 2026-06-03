from agent.state import AgentState, SubTask


def test_subtask_defaults():
    task: SubTask = {
        "agent_type": "coder",
        "description": "write code",
        "status": "pending",
        "result": None,
        "relevant_files": [],
    }
    assert task["agent_type"] == "coder"
    assert task["status"] == "pending"
    assert task["result"] is None
    assert task["relevant_files"] == []


def test_subtask_completed():
    task: SubTask = {
        "agent_type": "tester",
        "description": "run tests",
        "status": "completed",
        "result": "all tests pass",
        "relevant_files": ["tests/test_tools.py"],
    }
    assert task["status"] == "completed"
    assert "pass" in task["result"]


def test_agent_state_structure():
    state: AgentState = {
        "messages": [],
        "subtasks": [],
        "mode": "build",
    }
    assert state["messages"] == []
    assert state["subtasks"] == []
    assert state["mode"] == "build"


def test_agent_state_with_subtasks():
    state: AgentState = {
        "messages": [],
        "subtasks": [
            {
                "agent_type": "searcher",
                "description": "find files",
                "status": "completed",
                "result": "found main.py",
                "relevant_files": ["main.py"],
            },
            {
                "agent_type": "coder",
                "description": "edit code",
                "status": "pending",
                "result": None,
                "relevant_files": [],
            },
        ],
        "mode": "build",
    }
    assert len(state["subtasks"]) == 2
    assert state["subtasks"][0]["agent_type"] == "searcher"
    assert state["subtasks"][1]["status"] == "pending"


def test_subtask_required_fields():
    task: SubTask = {
        "agent_type": "coder",
        "description": "some task",
        "status": "pending",
        "result": None,
        "relevant_files": [],
    }
    assert "agent_type" in task
    assert "description" in task
    assert "status" in task
    assert "result" in task
    assert "relevant_files" in task


def test_empty_relevant_files():
    task: SubTask = {
        "agent_type": "spawn",
        "description": "do something",
        "status": "pending",
        "result": None,
        "relevant_files": [],
    }
    assert task["relevant_files"] == []
