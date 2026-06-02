from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from config import TEMPERATURE, TOP_P, MAX_TOKENS, THINKING


def create_sub_agent(
    model: str,
    api_key: str,
    base_url: str,
    system_prompt: str,
    tools: list,
) -> callable:
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        max_tokens=MAX_TOKENS,
        extra_body={"chat_template_kwargs": {"thinking": THINKING}},
    )

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )
