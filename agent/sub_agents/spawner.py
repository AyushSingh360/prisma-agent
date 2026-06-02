from .base import create_sub_agent
from ..tools import TOOLS

SPAWNER_PROMPT_TEMPLATE = """You are a specialized agent created to handle a specific task. You work autonomously.

Tools available: read files, write files, edit files, run commands, search code, list directories.

Your assignment:
{task_description}

Focus exclusively on this task. Use your tools to investigate and complete it.
When done, provide a complete summary of what you found and what you did."""


def create_spawned_agent(model: str, api_key: str, base_url: str, task_description: str):
    prompt = SPAWNER_PROMPT_TEMPLATE.format(task_description=task_description)
    return create_sub_agent(
        model=model,
        api_key=api_key,
        base_url=base_url,
        system_prompt=prompt,
        tools=TOOLS,
    )
