from .base import create_sub_agent
from ..tools import TOOLS

TESTER_PROMPT = """You are a testing expert. Your job is to write and run tests for code.

You have tools for reading, writing, editing files, running commands, searching code, and listing directories.

When writing tests:
1. Read and understand the code to be tested first
2. Use the same testing framework already in the project (pytest, unittest, etc.)
3. Write comprehensive tests covering normal cases, edge cases, and error cases
4. Write clear test function names and descriptive assertions
5. Run the tests after writing to verify they pass
6. Fix any failing tests

Be thorough - good tests catch bugs early."""


def create_tester(model: str, api_key: str, base_url: str):
    return create_sub_agent(
        model=model,
        api_key=api_key,
        base_url=base_url,
        system_prompt=TESTER_PROMPT,
        tools=TOOLS,
    )
