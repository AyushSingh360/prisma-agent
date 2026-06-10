import json
import subprocess
import re as re_module
from pathlib import Path
from langchain_core.tools import tool

try:
    import requests
except ImportError:
    requests = None

from config import SEARCH_PROVIDER, TAVILY_API_KEY, BRAVE_API_KEY

SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".env", ".idea", ".vscode"}


def _should_skip(path: Path) -> bool:
    return any(p.name in SKIP_DIRS for p in path.parents)


@tool
def read_file(path: str) -> str:
    """Read the contents of a file. Returns up to 50000 characters."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(50000)
        return content
    except UnicodeDecodeError:
        return "(binary file, cannot read as text)"
    except FileNotFoundError:
        return f"Error: file not found at {path}"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Edit a file by replacing the first occurrence of old_string with new_string."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if old_string not in content:
            return f"Error: string not found in {path}"
        new_content = content.replace(old_string, new_string, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"Edited {path}"
    except Exception as e:
        return f"Error editing file: {e}"


@tool
def run_command(command: str) -> str:
    """Run a PowerShell command on Windows. Returns stdout and stderr."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = ""
        if result.stdout:
            output += result.stdout[:8000]
        if result.stderr:
            if output:
                output += "\n"
            output += f"[stderr]\n{result.stderr[:2000]}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 60 seconds"
    except Exception as e:
        return f"Error running command: {e}"


@tool
def grep_search(pattern: str, include: str = None) -> str:
    """Search file contents using regex. Optionally filter by file pattern (e.g. '*.py')."""
    results = []
    root = Path.cwd()

    for file_path in root.rglob("*"):
        if file_path.is_dir():
            continue
        if _should_skip(file_path):
            continue
        if include and not file_path.match(include) and not file_path.name.endswith(include.replace("*", "")):
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_no, line in enumerate(f, 1):
                    try:
                        if re_module.search(pattern, line):
                            rel = file_path.relative_to(root)
                            trimmed = line.rstrip()[:200]
                            results.append(f"{rel}:{line_no}: {trimmed}")
                            if len(results) >= 30:
                                break
                    except re_module.error:
                        return f"Invalid regex pattern: {pattern}"
        except Exception:
            continue
        if len(results) >= 30:
            break

    return "\n".join(results) if results else "No matches found"


@tool
def glob_files(pattern: str) -> str:
    """Find files matching a glob pattern (e.g. '**/*.py' or 'src/**/*.ts')."""
    results = []
    root = Path.cwd()

    for file_path in root.rglob(pattern):
        if file_path.is_dir():
            continue
        if _should_skip(file_path):
            continue
        rel = file_path.relative_to(root)
        results.append(str(rel))
        if len(results) >= 100:
            break

    if not results and not pattern.startswith("**/"):
        for file_path in root.rglob(f"**/{pattern}"):
            if file_path.is_dir():
                continue
            if _should_skip(file_path):
                continue
            rel = file_path.relative_to(root)
            results.append(str(rel))
            if len(results) >= 100:
                break

    return "\n".join(results) if results else "No files found"


@tool
def list_directory(path: str = ".") -> str:
    """List files and directories at the given path."""
    try:
        entries = []
        for entry in Path(path).iterdir():
            if entry.name.startswith("."):
                continue
            suffix = "/" if entry.is_dir() else ""
            entries.append(f"{entry.name}{suffix}")
        if not entries:
            return "(empty directory)"
        return "\n".join(sorted(entries))
    except Exception as e:
        return f"Error listing directory: {e}"


TOOLS = [read_file, write_file, edit_file, run_command, grep_search, glob_files, list_directory]
