# Terminal UI & Keybindings

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Enter` | Send message |
| `Tab` | Toggle between BUILD and PLAN mode |
| `Ctrl+J` | Insert a newline (multi-line editing) |
| `Ctrl+L` | Clear the screen |
| `Ctrl+C` | Exit |
| `↑` / `↓` | Navigate command history |

## Status Bar

The status bar is shown above the prompt on every iteration:

```
◆ Prisma · llama-3.3-70b-versatile · BUILD · queued          ~25 tokens · Turn 3 · 2.1s
```

Fields:
- **Mode** — `BUILD` or `PLAN`
- **queued** — a pending request is stored (visible in PLAN mode)
- **~N tokens** — rough estimate of conversation context size
- **Turn N** — number of completed exchanges
- **N.Ns** — latency of the last response

## Message Panels

| Panel | When shown |
|---|---|
| **Plan card** | PLAN mode — shows agent assignments |
| **Execution group** | BUILD mode — shows each subtask result status |
| **Assistant message** | Every response — final synthesized reply with Markdown rendering |
| **Error panel** | On exceptions — shows error message in red |
| **Notification** | Mode switches, retries, exports — inline status toasts |

## Theme

The UI uses a dark blue/cyan palette:

| Color role | Hex |
|---|---|
| Primary (cyan-blue) | `#6EC6FF` |
| Accent (bright) | `#A0DCFF` |
| Success (green) | `#10B981` |
| Warning (amber) | `#F59E0B` |
| Error (red) | `#EF4444` |
| Background | `#0B1220` |
| Surface | `#111827` |

**Agent colors:**

| Agent | Color |
|---|---|
| coder | Blue `#3B82F6` |
| debugger | Purple `#A855F7` |
| searcher | Cyan `#06B6D4` |
| tester | Green `#10B981` |
| spawn | Amber `#F59E0B` |
