from .base import create_sub_agent
from ..tools import read_file, grep_search, glob_files, list_directory

SEARCHER_PROMPT = """You are a code search expert. Your job is to find files, code patterns, and information in the codebase.

You have tools for searching file contents, finding files by glob patterns, reading files, and listing directories.

When searching:
1. Use multiple search strategies if needed
2. Be thorough - check different locations and naming conventions
3. Provide complete file paths and relevant code snippets
4. If you don't find what you need, try different search terms

Always report exact file paths."""


def create_searcher(model: str, api_key: str, base_url: str):
    return create_sub_agent(
        model=model,
        api_key=api_key,
        base_url=base_url,
        system_prompt=SEARCHER_PROMPT,
        tools=[read_file, grep_search, glob_files, list_directory],
    )
