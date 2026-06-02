import json
import concurrent.futures
from langgraph.graph import StateGraph, START, END
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from config import NVIDIA_API_KEY, NVIDIA_BASE_URL, SUPERVISOR_MODEL, SUB_AGENT_MODEL
from .state import AgentState, SubTask
from .sub_agents.coder import create_coder
from .sub_agents.debugger import create_debugger
from .sub_agents.searcher import create_searcher
from .sub_agents.tester import create_tester
from .sub_agents.spawner import create_spawned_agent


SUPERVISOR_PROMPT = """You are the supervisor agent. You coordinate specialized sub-agents to help with coding tasks.

AVAILABLE SUB-AGENTS:
- coder: Writes, reads, and modifies code files.
- debugger: Finds and diagnoses bugs in code.
- searcher: Finds files, code patterns, and information in the project.
- tester: Writes and runs tests.
- spawn: For tasks that don't fit the above roles (e.g., configuration, docs, setup, etc.)

HOW TO RESPOND:
If the user wants conversation or asks a simple question, respond with a plain message.

If the user asks for code work, output ONLY valid JSON with this exact format (no other text):
{
  "plan": "brief description of the overall approach",
  "subtasks": [
    {
      "agent_type": "searcher",
      "description": "Detailed task description for the agent",
      "relevant_files": []
    }
  ]
}

GUIDELINES:
- Break complex tasks into parallel subtasks assigned to different agents
- Make each subtask description detailed enough for the agent to work independently
- Include known file paths in relevant_files
- For multi-step work, include all subtasks in one plan
- If you're unsure about file locations, use the searcher
- "spawn" agent can handle anything that isn't code-writing/debugging/searching/testing

Current workspace: the project directory
"""


AGENT_FACTORY = {
    "coder": lambda: create_coder(SUB_AGENT_MODEL, NVIDIA_API_KEY, NVIDIA_BASE_URL),
    "debugger": lambda: create_debugger(SUB_AGENT_MODEL, NVIDIA_API_KEY, NVIDIA_BASE_URL),
    "searcher": lambda: create_searcher(SUB_AGENT_MODEL, NVIDIA_API_KEY, NVIDIA_BASE_URL),
    "tester": lambda: create_tester(SUB_AGENT_MODEL, NVIDIA_API_KEY, NVIDIA_BASE_URL),
}


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1
        if lines[0].startswith("```") and len(lines[0]) > 3:
            start = 1
        end = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "```":
                end = i
                break
        text = "\n".join(lines[start:end])
    return text.strip()


def build_supervisor_graph():
    llm = ChatNVIDIA(
        model=SUPERVISOR_MODEL,
        api_key=NVIDIA_API_KEY,
        base_url=NVIDIA_BASE_URL,
        temperature=0.3,
    )

    def analyze(state: AgentState):
        response = llm.invoke([
            SystemMessage(content=SUPERVISOR_PROMPT),
            *state["messages"],
        ])

        content = response.content.strip()

        try:
            json_str = _extract_json(content)
            plan = json.loads(json_str)

            if "plan" in plan and "subtasks" in plan:
                subtasks = [
                    SubTask(
                        agent_type=s["agent_type"],
                        description=s["description"],
                        status="pending",
                        result=None,
                        relevant_files=s.get("relevant_files", []),
                    )
                    for s in plan["subtasks"]
                ]
                return {"subtasks": subtasks}

        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        return {"messages": [AIMessage(content=content)]}

    def execute_plan(state: AgentState):
        subtasks = state.get("subtasks", [])
        if not subtasks:
            return {}

        results = [None] * len(subtasks)

        def run_agent(i: int, subtask: SubTask):
            agent_type = subtask["agent_type"]
            description = subtask["description"]

            try:
                if agent_type in AGENT_FACTORY:
                    executor = AGENT_FACTORY[agent_type]()
                else:
                    task_for_spawn = f"Agent type '{agent_type}' requested.\n\nTask: {description}"
                    executor = create_spawned_agent(
                        SUB_AGENT_MODEL, NVIDIA_API_KEY, NVIDIA_BASE_URL, task_for_spawn
                    )

                result = agent.invoke({
                    "messages": [HumanMessage(content=description)],
                })
                ai_msgs = [m for m in result["messages"] if m.type == "ai"]
                return ai_msgs[-1].content if ai_msgs else "(no response)"
            except Exception as e:
                return f"Agent error: {e}"

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            future_map = {
                pool.submit(run_agent, i, subtask): i
                for i, subtask in enumerate(subtasks)
            }
            for future in concurrent.futures.as_completed(future_map):
                i = future_map[future]
                try:
                    subtasks[i]["result"] = future.result() or "(no output)"
                    subtasks[i]["status"] = "completed"
                except Exception as e:
                    subtasks[i]["result"] = f"Agent execution failed: {e}"
                    subtasks[i]["status"] = "failed"

        return {"subtasks": subtasks}

    def synthesize(state: AgentState):
        subtasks = state.get("subtasks", [])
        if not subtasks:
            return {}

        summary_parts = []
        for s in subtasks:
            status_mark = "✓" if s["status"] == "completed" else "✗"
            header = f"### {s['agent_type'].title()}: {s['description']} ({status_mark})"
            result_text = s.get("result", "") or ""
            summary_parts.append(f"{header}\n\n{result_text}")

        summary = "\n\n---\n\n".join(summary_parts)

        synthesis_response = llm.invoke([
            SystemMessage(content="You are a helpful coding assistant. Summarize the completed work clearly for the user."),
            HumanMessage(content=f"Here are results from sub-agents:\n\n{summary}\n\nGive the user a clear summary of what was done."),
        ])

        return {"messages": [AIMessage(content=synthesis_response.content)]}

    workflow = StateGraph(AgentState)

    workflow.add_node("analyze", analyze)
    workflow.add_node("execute_plan", execute_plan)
    workflow.add_node("synthesize", synthesize)

    def route_after_analyze(state: AgentState):
        if state.get("subtasks"):
            return "execute_plan"
        return END

    workflow.add_edge(START, "analyze")
    workflow.add_conditional_edges("analyze", route_after_analyze)
    workflow.add_edge("execute_plan", "synthesize")
    workflow.add_edge("synthesize", END)

    return workflow.compile()
