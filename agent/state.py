from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class SubTask(TypedDict):
    agent_type: str
    description: str
    status: str
    result: Optional[str]
    relevant_files: list[str]


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    subtasks: list[SubTask]
    mode: str
