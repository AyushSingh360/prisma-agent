from langchain.agents import create_agent
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from config import TEMPERATURE, TOP_P, MAX_TOKENS, THINKING


def create_sub_agent(
    model: str,
    api_key: str,
    base_url: str,
    system_prompt: str,
    tools: list,
) -> callable:
    llm = ChatNVIDIA(
        model=model,
        api_key=api_key,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        max_tokens=MAX_TOKENS,
    )

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )
