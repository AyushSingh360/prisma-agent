from langchain.agents import create_agent
from langchain_nvidia_ai_endpoints import ChatNVIDIA


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
        base_url=base_url,
        temperature=0.3,
    )

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )

    return agent
