# Tools

All tools are LangChain `@tool`-decorated functions available to sub-agents.

## Security

File tools (`read_file`, `write_file`, `edit_file`) are sandboxed to the repository root via path resolution. Paths that resolve outside `Path.cwd()` are rejected.

`run_command` only allows whitelisted commands: `pytest`, `python`, `pip`, `git`, `dir`, `ls`, `echo`, `Get-ChildItem`, `Set-Content`, `Remove-Item`.

Recursive search tools skip these directories: `node_modules`, `.git`, `__pycache__`, `.venv`, `venv`, `.env`, `.idea`, `.vscode`.

## File Tools

### `read_file(path: str) -> str`
Read the contents of a file. Returns up to 50,000 characters.

- Returns `"(binary file, cannot read as text)"` for binary files
- Returns `"Error: file not found at {path}"` if missing
- Sandboxed to repo root

### `write_file(path: str, content: str) -> str`
Write content to a file. Creates parent directories if needed.

- Returns `"Wrote {len(content)} bytes to {path}"` on success
- Overwrites existing files

### `edit_file(path: str, old_string: str, new_string: str) -> str`
Edit a file by replacing the first occurrence of old_string with new_string.

- Returns `"Error: string not found in {path}"` if `old_string` not present
- Returns `"Edited {path}"` on success

## Command Tool

### `run_command(command: str) -> str`
Run a PowerShell command on Windows. Returns stdout and stderr.

- Only whitelisted commands are allowed to mitigate arbitrary code execution
- 60-second timeout
- Stdout capped at 8,000 chars; stderr capped at 2,000 chars
- Non-zero exit codes are appended to output

## Search Tools

### `grep_search(pattern: str, include: str = None) -> str`
Search file contents using regex. Optionally filter by file pattern (e.g. '*.py').

- Returns up to 30 matches in format `path:line_number: content`
- Returns `"Invalid regex pattern: {pattern}"` for bad regex
- Returns `"No matches found"` if no matches

### `glob_files(pattern: str) -> str`
Find files matching a glob pattern (e.g. '**/*.py' or 'src/**/*.ts').

- Returns up to 100 matching relative paths
- If no results and pattern doesn't start with `**/`, retries with `**/{pattern}`
- Returns `"No files found"` if no matches

### `list_directory(path: str = ".") -> str`
List files and directories at the given path.

- Skips dotfiles (names starting with `.`)
- Appends `/` to directory names
- Returns `"(empty directory)"` if empty

## Web Search Tool

### `search_web(query: str, max_results: int = 5) -> str`
Search the web for information. Returns formatted results with title, URL, and snippet.

**Providers** (selected by `SEARCH_PROVIDER` config):

- **Tavily**: POST to `https://api.tavily.com/search`. Returns answer + numbered results.
- **Brave**: GET to `https://api.search.brave.com/res/v1/web/search`. Returns numbered results.
- **Google**: GET to `https://www.googleapis.com/customsearch/v1`. Returns numbered results.

All backends: 30-second timeout, return `"Search error: {e}"` on failure.
