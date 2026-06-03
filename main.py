import sys
import time

from langchain_core.messages import HumanMessage

from config import NVIDIA_API_KEY
from agent.supervisor import build_supervisor_graph
from agent.state import AgentState
from utils.commands import handle_command
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
        user_input, mode = get_user_input()
        if not user_input:
            break

        if user_input.startswith("/"):
            output, new_state = handle_command(user_input[1:], state)
            if output == "__EXIT__":
                break
            if output == "__RETRY__":
                if state["messages"]:
                    state["messages"].pop()
                else:
                    console.print("[dim]nothing to retry[/dim]")
                    continue
                if not state.get("messages"):
                    continue
                last_human = None
                for m in reversed(state["messages"]):
                    if m.type == "human":
                        last_human = m
                        break
                if last_human is None:
                    continue
                user_input = last_human.content
                print_user_message(user_input)
                state["messages"] = state["messages"][:-1]
            else:
                if output:
                    console.print()
                    console.print(output)
                if new_state is not None:
                    state = new_state
                continue

        else:
            print_user_message(user_input)

        try:
            t0 = time.time()
            result = graph.invoke({
                "messages": state["messages"] + [HumanMessage(content=user_input)],
                "subtasks": [],
                "mode": mode,
            })
            elapsed = time.time() - t0

            state = result

            subtasks = result.get("subtasks", [])
            if subtasks:
                if mode == "plan":
                    console.print()
                    console.print("[bold]Plan[/bold]")
                    for s in subtasks:
                        color = {"coder": "blue", "debugger": "magenta", "searcher": "cyan", "tester": "green"}.get(s["agent_type"], "white")
                        console.print(f"  [{color}]{s['agent_type']}[/{color}] {s['description']}")
                    console.print(Text(f"  {elapsed:.1f}s", style="dim"))
                    console.print()
                    console.print("[dim]press [yellow]Tab[/yellow] to switch to build mode and execute[/dim]")
                else:
                    print_subtask_header(subtasks)
                    for s in subtasks:
                        if s.get("result"):
                            print_subtask_completed(s, s["result"])

                    for msg in reversed(result["messages"]):
                        if msg.type == "ai" and msg.content:
                            print_assistant_message(msg.content, elapsed)
                            break
            else:
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
