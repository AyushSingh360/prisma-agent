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
