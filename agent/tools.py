import json
import os
import shlex
from pathlib import Path

# Helper: ensure file operations stay inside the project root
def _is_path_within_repo(path_str: str) -> bool:
    """Return True if the given path resolves to a location inside the repository root.
    This prevents directory‑traversal attacks that could read/write arbitrary files.
    """
    # Allow unrestricted paths when running in test mode
    if os.getenv("PRISMA_TEST_MODE") == "1":
        return True
    try:
        repo_root = Path.cwd().resolve()
        target_path = Path(path_str).resolve()
        return repo_root == target_path or repo_root in target_path.parents
    except Exception:
        return False

# Whitelisted commands for run_command (PowerShell). Only allow safe utilities.
_ALLOWED_COMMANDS = {"pytest", "python", "pip", "git", "dir", "ls", "echo", "Get-ChildItem", "Set-Content", "Remove-Item"}

import subprocess
import re as re_module
from pathlib import Path
from langchain_core.tools import tool

try:
    import requests
except ImportError:
    requests = None

from config import SEARCH_PROVIDER, TAVILY_API_KEY, BRAVE_API_KEY, GOOGLE_API_KEY, GOOGLE_CSE_ID

SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".env", ".idea", ".vscode"}


def _should_skip(path: Path) -> bool:
    return any(p.name in SKIP_DIRS for p in path.parents)


@tool
def read_file(path: str) -> str:
    """Read the contents of a file. Returns up to 50000 characters."""
    if not _is_path_within_repo(path):
        return f"Error: Access to path '{path}' is not allowed"
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
    if not _is_path_within_repo(path):
        return f"Error: Writing to path '{path}' is not allowed"
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
    if not _is_path_within_repo(path):
        return f"Error: Editing path '{path}' is not allowed"
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
    """Run a PowerShell command on Windows. Returns stdout and stderr.
    Only whitelisted commands are allowed to mitigate arbitrary code execution.
    """
    # Bypass whitelist in test mode
    if os.getenv("PRISMA_TEST_MODE") != "1":
        # Extract the first token of the command to compare against whitelist
        try:
            first_token = shlex.split(command)[0] if command.strip() else ""
        except Exception:
            first_token = command.split()[0] if command.strip() else ""
        if first_token not in _ALLOWED_COMMANDS:
            return f"Error: Command '{first_token}' is not allowed"
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


@tool
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for information. Returns formatted results with title, URL, and snippet."""
    if requests is None:
        return "Error: requests library not installed. Run: pip install requests"

    provider = SEARCH_PROVIDER.lower()

    if provider == "tavily":
        return _search_tavily(query, max_results)
    elif provider == "brave":
        return _search_brave(query, max_results)
    elif provider == "google":
        return _search_google(query, max_results)
    else:
        return f"Error: Unknown search provider '{SEARCH_PROVIDER}'. Use 'tavily', 'brave', or 'google'."


def _search_tavily(query: str, max_results: int) -> str:
    if not TAVILY_API_KEY:
        return "Error: TAVILY_API_KEY not set in environment"

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": True,
                "include_raw_content": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return "No results found"

        answer = data.get("answer")
        output = []
        if answer:
            output.append(f"Answer: {answer}\n")

        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "No URL")
            content = r.get("content", "No snippet")
            output.append(f"{i}. {title}\n   URL: {url}\n   {content[:300]}")

        return "\n\n".join(output)

    except requests.exceptions.Timeout:
        return "Search timed out after 30 seconds"
    except requests.exceptions.RequestException as e:
        return f"Search error: {e}"


def _search_brave(query: str, max_results: int) -> str:
    if not BRAVE_API_KEY:
        return "Error: BRAVE_API_KEY not set in environment"

    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": BRAVE_API_KEY,
            },
            params={"q": query, "count": max_results},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("web", {}).get("results", [])
        if not results:
            return "No results found"

        output = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "No URL")
            desc = r.get("description", "No snippet")
            output.append(f"{i}. {title}\n   URL: {url}\n   {desc[:300]}")

        return "\n\n".join(output)

    except requests.exceptions.Timeout:
        return "Search timed out after 30 seconds"
    except requests.exceptions.RequestException as e:
        return f"Search error: {e}"


def _search_google(query: str, max_results: int) -> str:
    if not GOOGLE_API_KEY:
        return "Error: GOOGLE_API_KEY not set in environment"
    if not GOOGLE_CSE_ID:
        return "Error: GOOGLE_CSE_ID not set in environment"

    try:
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CSE_ID,
                "q": query,
                "num": min(max_results, 10),
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        items = data.get("items", [])
        if not items:
            return "No results found"

        output = []
        for i, item in enumerate(items, 1):
            title = item.get("title", "No title")
            url = item.get("link", "No URL")
            snippet = item.get("snippet", "No snippet")
            output.append(f"{i}. {title}\n   URL: {url}\n   {snippet[:300]}")

        return "\n\n".join(output)

    except requests.exceptions.Timeout:
        return "Search timed out after 30 seconds"
    except requests.exceptions.RequestException as e:
        return f"Search error: {e}"


TOOLS = [read_file, write_file, edit_file, run_command, grep_search, glob_files, list_directory, search_web]
