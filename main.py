import sys
import time

from langchain_core.messages import HumanMessage
from rich.text import Text

from config import API_KEY, NVIDIA_API_KEY, SUPERVISOR_MODEL
from agent.supervisor import build_supervisor_graph
from agent.state import AgentState
from utils.commands import handle_command
from utils.renderers import (
    console,
    render_user_message,
    render_assistant_message,
    render_plan_card,
    render_tool_card,
    render_tool_group,
    render_error,
    render_notification,
    render_welcome,
    render_footer,
)
from utils.layout import PrismaLayout
from utils.input import (
    get_user_input,
    get_mode,
    set_pending_request,
    get_pending_request,
)
from utils.animations import LiveManager
from utils.theme import STYLES, ICONS, APP_NAME


MODEL = SUPERVISOR_MODEL.split("/")[-1]


def _estimate_tokens(state: dict) -> int:
    """Rough token estimate from message content lengths."""
    total = 0
    for m in state.get("messages", []):
        content = getattr(m, "content", "") or ""
        total += len(content) // 4
    return total


def main():
    if not API_KEY or API_KEY == "your-key-here":
        if not NVIDIA_API_KEY or NVIDIA_API_KEY == "your-nvidia-api-key":
            console.print()
            console.print(render_error(
                "API key not set. Add GROQ_API_KEY, OPENROUTER_API_KEY, or NVIDIA_API_KEY to .env"
            ))
            sys.exit(1)

    # ── Initialize UI ──
    layout = PrismaLayout()
    layout.initialize(MODEL)
    live_mgr = LiveManager(console)

    # ── Build graph ──
    graph = build_supervisor_graph()
    state: AgentState = {
        "messages": [],
        "subtasks": [],
    }
    turn_count = 0

    while True:
        # Update session data
        layout.update_session(
            turns=turn_count,
            messages=len(state.get("messages", [])),
            est_tokens=_estimate_tokens(state),
            mode=get_mode(),
        )

        layout.print_prompt_chrome(
            mode=get_mode(),
            pending_request=get_pending_request(),
        )
        user_input, mode = get_user_input(console)
        if not user_input:
            break

        if user_input == "__EXECUTE_PENDING__":
            pending_request = get_pending_request()
            if not pending_request:
                console.print(
                    render_notification("Nothing queued to execute", "warn")
                )
                continue
            user_input = pending_request
            mode = "build"
            set_pending_request(None)

        if user_input.startswith("/"):
            output, new_state = handle_command(user_input[1:], state)
            if output == "__EXIT__":
                break
            if output == "__REBUILD_GRAPH__":
                graph = build_supervisor_graph()
                thinking_state = "enabled" if new_state and new_state.get("thinking") else "disabled"
                console.print(
                    render_notification(f"Thinking: {thinking_state}", "ok")
                )
                continue
            if output == "__RETRY__":
                if state["messages"]:
                    state["messages"].pop()
                else:
                    console.print(
                        render_notification("Nothing to retry", "warn")
                    )
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
                console.print()
                console.print(render_user_message(user_input))
                if state["messages"] and state["messages"][-1].type != "human":
                    state["messages"] = state["messages"][:-1]
                if state["messages"] and state["messages"][-1].type == "human":
                    state["messages"] = state["messages"][:-1]
            else:
                if output:
                    console.print()
                    console.print(output)
                if new_state is not None:
                    state = new_state
                continue

        try:
            t0 = time.time()

            # ── Run graph with animated spinner ──
            invoke_args = {
                "messages": state["messages"] + [HumanMessage(content=user_input)],
                "subtasks": [],
                "mode": mode,
            }
            result = live_mgr.run_with_spinner(
                graph.invoke,
                "Thinking...",
                invoke_args,
            )

            elapsed = time.time() - t0
            turn_count += 1

            layout.update_session(
                turns=turn_count,
                messages=len(result.get("messages", [])),
                est_tokens=_estimate_tokens(result),
                latency=elapsed,
            )

            state = result

            if subtasks := result.get("subtasks", []):
                if mode == "plan":
                    set_pending_request(user_input)
                    console.print()
                    console.print(render_plan_card(subtasks, elapsed))
                    console.print()
                    console.print(
                        render_notification(
                            "Press Tab to switch to BUILD mode and execute",
                            "info",
                        )
                    )
                else:
                    set_pending_request(None)
                    # Show tool execution results
                    console.print()
                    console.print(render_tool_group(subtasks))

                    # Show final synthesized response
                    for msg in reversed(result["messages"]):
                        if msg.type == "ai" and msg.content:
                            console.print()
                            console.print(
                                render_assistant_message(msg.content, elapsed)
                            )
                            break
            else:
                set_pending_request(None)
                for msg in reversed(result["messages"]):
                    if msg.type == "ai" and msg.content:
                        console.print()
                        console.print(
                            render_assistant_message(msg.content, elapsed)
                        )
                        break

        except Exception as e:
            console.print()
            console.print(render_error(str(e)))
            import traceback
            traceback.print_exc()

    # ── Exit ──
    console.print()
    console.print(render_notification(f"{APP_NAME} session closed", "ok"))
    console.print()


if __name__ == "__main__":
    main()
