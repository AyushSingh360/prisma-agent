from .base import create_sub_agent
from ..tools import read_file, run_command, grep_search, glob_files, list_directory

DEBUGGER_PROMPT = """You are a debugging expert. Your job is to find and diagnose bugs in code.

You have tools for reading files, running commands, searching code, and listing directories.

When debugging:
1. First understand the code and the error context
2. Reproduce the issue if possible
3. Identify the root cause
4. Provide a clear diagnosis with exact file paths and line numbers
5. Suggest the fix (but do not apply it)

Be thorough and systematic. Check error messages, logs, and code logic."""


def create_debugger(model: str, api_key: str, base_url: str):
    return create_sub_agent(
        model=model,
        api_key=api_key,
        base_url=base_url,
        system_prompt=DEBUGGER_PROMPT,
        tools=[read_file, run_command, grep_search, glob_files, list_directory],
    )
