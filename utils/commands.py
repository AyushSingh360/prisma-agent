from prompt_toolkit.completion import Completer, Completion


COMMANDS = {
    "basic": {
        "help": "show this help message",
        "clear": "clear conversation history",
        "quit": "exit the agent",
    },
    "info": {
        "model": "show active model configuration",
        "agents": "list available sub-agents and their roles",
        "status": "show session statistics",
        "config": "show full configuration",
    },
    "advanced": {
        "think": "toggle thinking/reasoning mode",
        "retry": "retry the last exchange",
        "export": "export conversation as markdown",
    },
}

ALL_COMMANDS = {}
for group in COMMANDS.values():
    ALL_COMMANDS.update(group)

COMMAND_NAMES = sorted(ALL_COMMANDS.keys())


def handle_command(cmd: str, state: dict) -> tuple[str, dict | None]:
    """
    Handle a command. Returns (output_text, new_state_or_None).
    If new_state is None, state unchanged.
    """
    cmd = cmd.lower().strip()

    if cmd == "help":
        lines = ["commands:\n"]
        for group_name, cmds in COMMANDS.items():
            lines.append(f"  {group_name}")
            for name, desc in cmds.items():
                lines.append(f"    /{name:<12} {desc}")
            lines.append("")
        return "\n".join(lines), None

    if cmd == "clear":
        new_state = {"messages": [], "subtasks": []}
        return "conversation cleared", new_state

    if cmd in ("quit", "exit"):
        return "__EXIT__", None

    if cmd == "model":
        from config import SUPERVISOR_MODEL, SUB_AGENT_MODEL, BASE_URL
        return (
            f"model\n"
            f"  supervisor  {SUPERVISOR_MODEL}\n"
            f"  sub-agent   {SUB_AGENT_MODEL}\n"
            f"  provider    {BASE_URL}"
        ), None

    if cmd == "agents":
        agents_info = (
            "agents\n"
            "  coder     write, read, and modify code files\n"
            "  debugger  find and diagnose bugs\n"
            "  searcher  find files, code patterns, and search the web\n"
            "  tester    write and run tests\n"
            "  spawn     handle everything else"
        )
        return agents_info, None

    if cmd == "status":
        msgs = len(state.get("messages", []))
        tasks = len(state.get("subtasks", []))
        return (
            f"session\n"
            f"  messages   {msgs}\n"
            f"  sub-tasks  {tasks}"
        ), None

    if cmd == "config":
        from config import SUPERVISOR_MODEL, SUB_AGENT_MODEL, TEMPERATURE, TOP_P, MAX_TOKENS, THINKING, BASE_URL
        return (
            f"config\n"
            f"  supervisor  {SUPERVISOR_MODEL}\n"
            f"  sub-agent   {SUB_AGENT_MODEL}\n"
            f"  provider    {BASE_URL}\n"
            f"  temperature {TEMPERATURE}\n"
            f"  top_p       {TOP_P}\n"
            f"  max_tokens  {MAX_TOKENS}\n"
            f"  thinking    {THINKING}"
        ), None

    if cmd == "think":
        from config import THINKING
        new_val = not THINKING
        _set_config("THINKING", new_val)
        return "__REBUILD_GRAPH__", {"thinking": new_val}

    if cmd == "retry":
        return "__RETRY__", None

    if cmd == "export":
        from datetime import datetime
        msgs = state.get("messages", [])
        if not msgs:
            return "no messages to export", None
        lines = [f"# Prisma Agent Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
        for m in msgs:
            role = "You" if m.type == "human" else "Prisma"
            lines.append(f"**{role}:** {m.content}\n")
        content = "\n".join(lines)
        fname = f"prisma-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(content)
        return f"exported to {fname} ({len(msgs)} messages)", None

    return None, None


def _set_config(key: str, val):
    import config as cfg
    setattr(cfg, key, val)


class CommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            word = text[1:]
            for cmd in COMMAND_NAMES:
                if cmd.startswith(word):
                    yield Completion(f"/{cmd}", start_position=-len(text))
