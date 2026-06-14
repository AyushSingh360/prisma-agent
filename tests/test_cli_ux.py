from utils.display import get_pending_request, set_pending_request
from utils.commands import handle_command


def test_pending_request_round_trip():
    set_pending_request("fix the bug")
    assert get_pending_request() == "fix the bug"
    set_pending_request(None)
    assert get_pending_request() is None


def test_retry_command_signal():
    output, new_state = handle_command("retry", {"messages": [], "subtasks": []})
    assert output == "__RETRY__"
    assert new_state is None


def test_think_command_requests_rebuild():
    output, new_state = handle_command("think", {"messages": [], "subtasks": []})
    assert output == "__REBUILD_GRAPH__"
    assert new_state is not None
    assert "thinking" in new_state
