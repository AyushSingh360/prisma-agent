import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from agent.tools import (
    read_file, write_file, edit_file, run_command,
    grep_search, glob_files, list_directory, search_web,
)


def test_write_and_read_file(tmp_path):
    path = tmp_path / "test.txt"
    result = write_file.invoke({"path": str(path), "content": "hello world"})
    assert "Wrote" in result
    assert "hello world" in read_file.invoke({"path": str(path)})


def test_write_creates_parent_dirs(tmp_path):
    path = tmp_path / "a" / "b" / "deep.txt"
    result = write_file.invoke({"path": str(path), "content": "nested"})
    assert "Wrote" in result
    assert path.exists()


def test_read_file_not_found(tmp_path):
    result = read_file.invoke({"path": str(tmp_path / "nope.txt")})
    assert "not found" in result


def test_edit_file(tmp_path):
    path = tmp_path / "edit.txt"
    path.write_text("foo bar baz")
    result = edit_file.invoke({"path": str(path), "old_string": "bar", "new_string": "qux"})
    assert "Edited" in result
    assert path.read_text() == "foo qux baz"


def test_edit_file_string_not_found(tmp_path):
    path = tmp_path / "edit.txt"
    path.write_text("hello")
    result = edit_file.invoke({"path": str(path), "old_string": "nope", "new_string": "x"})
    assert "not found" in result


def test_edit_file_replaces_first_only(tmp_path):
    path = tmp_path / "edit.txt"
    path.write_text("a a a")
    edit_file.invoke({"path": str(path), "old_string": "a", "new_string": "b"})
    assert path.read_text() == "b a a"


def test_run_command_echo(tmp_path):
    result = run_command.invoke({"command": "'hello from powershell'"})
    assert "hello from powershell" in result


def test_run_command_timeout():
    import subprocess
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="powershell", timeout=60)):
        result = run_command.invoke({"command": "Start-Sleep -Seconds 120"})
        assert "timed out" in result


def test_grep_search(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    py_file = tmp_path / "example.py"
    py_file.write_text("def hello():\n    pass\n")
    result = grep_search.invoke({"pattern": "def hello", "include": "*.py"})
    assert "example.py" in result


def test_grep_search_no_matches(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dummy.py").write_text("x = 1")
    result = grep_search.invoke({"pattern": "zzz_nonexistent_zzz"})
    assert "No matches" in result


def test_grep_search_invalid_regex():
    result = grep_search.invoke({"pattern": "["})
    assert "Invalid regex" in result


def test_glob_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "foo.py").write_text("")
    (tmp_path / "bar.py").write_text("")
    result = glob_files.invoke({"pattern": "*.py"})
    assert "foo.py" in result
    assert "bar.py" in result


def test_glob_files_no_matches(tmp_path):
    result = glob_files.invoke({"pattern": "*.zzz"})
    assert "No files found" in result


def test_list_directory(tmp_path):
    (tmp_path / "file_a.txt").write_text("")
    (tmp_path / "file_b.txt").write_text("")
    result = list_directory.invoke({"path": str(tmp_path)})
    assert "file_a.txt" in result
    assert "file_b.txt" in result


def test_list_directory_empty(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    result = list_directory.invoke({"path": str(empty_dir)})
    assert "empty" in result


def test_list_directory_hidden_skipped(tmp_path):
    (tmp_path / ".hidden").write_text("")
    (tmp_path / "visible").write_text("")
    result = list_directory.invoke({"path": str(tmp_path)})
    assert ".hidden" not in result
    assert "visible" in result


def test_read_file_binary(tmp_path):
    path = tmp_path / "binary.bin"
    path.write_bytes(b"\xff\xfe\x80\x81\x82")
    result = read_file.invoke({"path": str(path)})
    assert "binary file" in result or "Error reading" in result


def test_search_web_tavily_no_key(monkeypatch):
    monkeypatch.setattr("agent.tools.TAVILY_API_KEY", None)
    monkeypatch.setattr("agent.tools.SEARCH_PROVIDER", "tavily")
    result = search_web.invoke({"query": "test query"})
    assert "TAVILY_API_KEY not set" in result


def test_search_web_brave_no_key(monkeypatch):
    monkeypatch.setattr("agent.tools.BRAVE_API_KEY", None)
    monkeypatch.setattr("agent.tools.SEARCH_PROVIDER", "brave")
    result = search_web.invoke({"query": "test query"})
    assert "BRAVE_API_KEY not set" in result


def test_search_web_unknown_provider(monkeypatch):
    monkeypatch.setattr("agent.tools.SEARCH_PROVIDER", "unknown")
    result = search_web.invoke({"query": "test query"})
    assert "Unknown search provider" in result


@patch("agent.tools.requests.post")
def test_search_web_tavily_success(mock_post, monkeypatch):
    monkeypatch.setattr("agent.tools.TAVILY_API_KEY", "test-key")
    monkeypatch.setattr("agent.tools.SEARCH_PROVIDER", "tavily")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "answer": "Test answer",
        "results": [
            {"title": "Result 1", "url": "https://example.com/1", "content": "Content 1"},
            {"title": "Result 2", "url": "https://example.com/2", "content": "Content 2"},
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = search_web.invoke({"query": "test query", "max_results": 5})
    assert "Test answer" in result
    assert "Result 1" in result
    assert "https://example.com/1" in result
    assert "Content 1" in result


@patch("agent.tools.requests.get")
def test_search_web_brave_success(mock_get, monkeypatch):
    monkeypatch.setattr("agent.tools.BRAVE_API_KEY", "test-key")
    monkeypatch.setattr("agent.tools.SEARCH_PROVIDER", "brave")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "web": {
            "results": [
                {"title": "Brave Result 1", "url": "https://brave.com/1", "description": "Brave desc 1"},
                {"title": "Brave Result 2", "url": "https://brave.com/2", "description": "Brave desc 2"},
            ]
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = search_web.invoke({"query": "test query", "max_results": 5})
    assert "Brave Result 1" in result
    assert "https://brave.com/1" in result
    assert "Brave desc 1" in result


@patch("agent.tools.requests.post")
def test_search_web_tavily_timeout(mock_post, monkeypatch):
    monkeypatch.setattr("agent.tools.TAVILY_API_KEY", "test-key")
    monkeypatch.setattr("agent.tools.SEARCH_PROVIDER", "tavily")

    import requests
    mock_post.side_effect = requests.exceptions.Timeout()

    result = search_web.invoke({"query": "test query"})
    assert "timed out" in result.lower()


@patch("agent.tools.requests.post")
def test_search_web_tavily_request_error(mock_post, monkeypatch):
    monkeypatch.setattr("agent.tools.TAVILY_API_KEY", "test-key")
    monkeypatch.setattr("agent.tools.SEARCH_PROVIDER", "tavily")

    import requests
    mock_post.side_effect = requests.exceptions.RequestException("Connection error")

    result = search_web.invoke({"query": "test query"})
    assert "Search error" in result
