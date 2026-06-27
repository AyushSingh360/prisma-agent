# Prisma — Multi-Agent Coding Assistant

Prisma is a terminal-based AI coding assistant that coordinates specialized sub-agents to handle complex development tasks. You describe what you need — Prisma plans, delegates, executes, and summarizes.

## How it works

1. You type a request in the terminal
2. A **supervisor agent** reads it and either answers directly or decomposes it into subtasks
3. **Specialized sub-agents** (coder, debugger, searcher, tester) run in parallel
4. The supervisor synthesizes all results into a single clean response

## Quick Start

```bash
git clone https://github.com/<your-username>/prisma-agent
cd prisma-agent
pip install -r requirements.txt
cp .env .env.backup
# Add your API key to .env
python main.py
```

## Documentation

- **[Architecture](ARCHITECTURE.md)** — how the components fit together
- **[Configuration](CONFIGURATION.md)** — all environment variables and provider setup
- **[Modes](MODES.md)** — Plan mode vs Build mode
- **[Sub-Agents](SUB_AGENTS.md)** — coder, debugger, searcher, tester, spawn
- **[Tools](TOOLS.md)** — built-in tools available to agents
- **[Commands](COMMANDS.md)** — all slash commands
- **[UI](UI.md)** — terminal interface and keybindings
- **[Testing](TESTING.md)** — running the test suite
