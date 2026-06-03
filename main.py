import sys
import time

from langchain_core.messages import HumanMessage

from config import NVIDIA_API_KEY
from agent.supervisor import build_supervisor_graph
from agent.state import AgentState
from utils.display import (
    console,
    print_welcome,
    print_user_message,
    print_assistant_message,
    print_subtask_header,
    print_subtask_completed,
    print_exit,
    print_error,
    get_user_input,
)


def main():
    if not NVIDIA_API_KEY or NVIDIA_API_KEY == "your-key-here":
        print_error("NVIDIA_API_KEY not set or still has default value.")
        console.print("Create a [bold].env[/bold] file with: [green]NVIDIA_API_KEY=your_actual_key[/green]")
        sys.exit(1)

    print_welcome()

    graph = build_supervisor_graph()

    state: AgentState = {
        "messages": [],
        "subtasks": [],
    }

    while True:
        user_input = get_user_input()
        if not user_input:
            break

        if user_input.lower() in ("exit", "quit", "/quit"):
            break

        if user_input.lower() == "/help":
            console.print()
            console.print("[bold]commands[/bold]")
            console.print("  [yellow]/help[/yellow]    show this help")
            console.print("  [yellow]/clear[/yellow]   clear conversation history")
            console.print("  [yellow]/quit[/yellow]    exit the agent")
            console.print()
            console.print("[bold]usage[/bold]")
            console.print("  just describe what you want:")
            console.print('  [italic]"add error handling to the API client and write tests"[/italic]')
            continue

        if user_input.lower() == "/clear":
            state = {"messages": [], "subtasks": []}
            console.print("[dim]cleared[/dim]")
            continue

        print_user_message(user_input)

        try:
            t0 = time.time()
            result = graph.invoke({
                "messages": state["messages"] + [HumanMessage(content=user_input)],
                "subtasks": [],
            })
            elapsed = time.time() - t0

            state = result

            subtasks = result.get("subtasks", [])
            if subtasks:
                print_subtask_header(subtasks)
                for s in subtasks:
                    if s.get("result"):
                        print_subtask_completed(s, s["result"])

            for msg in reversed(result["messages"]):
                if msg.type == "ai" and msg.content:
                    print_assistant_message(msg.content, elapsed)
                    break

        except Exception as e:
            print_error(str(e))
            import traceback
            traceback.print_exc()

    print_exit()


if __name__ == "__main__":
    main()
