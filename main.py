import sys
from pathlib import Path

from langchain_core.messages import HumanMessage

from config import NVIDIA_API_KEY
from agent.supervisor import build_supervisor_graph
from agent.state import AgentState
from utils.display import (
    console,
    print_welcome,
    print_assistant_message,
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
            console.print("[dim]Exiting.[/dim]")
            break

        if user_input.lower() == "/help":
            console.print(Panel.fit(
                "[bold]Commands:[/bold]\n"
                "  [yellow]/help[/yellow]  - Show this help\n"
                "  [yellow]/clear[/yellow] - Clear conversation history\n"
                "  [yellow]/quit[/yellow]  - Exit the agent\n"
                "\n"
                "[bold]Usage:[/bold]\n"
                "  Just describe what you want to do with your code.\n"
                "  Example: [italic]'Add error handling to the API client and write tests'[/italic]",
                title="Help",
                border_style="blue",
            ))
            continue

        if user_input.lower() == "/clear":
            state = {"messages": [], "subtasks": []}
            console.print("[dim]Conversation cleared.[/dim]")
            continue

        try:
            with console.status("[bold cyan]Planning...") as status:
                result = graph.invoke({
                    "messages": state["messages"] + [HumanMessage(content=user_input)],
                    "subtasks": [],
                })

            state = result

            for msg in reversed(result["messages"]):
                if msg.type == "ai" and msg.content:
                    print_assistant_message(msg.content)
                    break

        except Exception as e:
            print_error(str(e))
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
