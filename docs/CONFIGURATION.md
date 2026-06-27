# Configuration

All configuration is loaded from a `.env` file via `python-dotenv`.

## API Keys

| Variable | Provider | Notes |
|---|---|---|
| `GROQ_API_KEY` | [Groq](https://console.groq.com) | Must start with `gsk_` |
| `OPENROUTER_API_KEY` | [OpenRouter](https://openrouter.ai) | Prefix `sk-or-` |
| `NVIDIA_API_KEY` | [NVIDIA NIM](https://integrate.api.nvidia.com) | Prefix `nvapi-` |

Only one is required. Prisma auto-detects which key is available and routes accordingly.

## Provider Routing

Prisma selects the provider based on the model name:

| Model name contains | Provider | Base URL |
|---|---|---|
| `gemini` or starts with `google/` | OpenRouter | `https://openrouter.ai/api/v1` |
| `minimax` or `nvidia` | NVIDIA NIM | `https://integrate.api.nvidia.com/v1` |
| `llama`, `mixtral`, `gemma` | Groq | `https://api.groq.com/openai/v1` |
| anything else | OpenRouter (fallback) | `https://openrouter.ai/api/v1` |

## Default Models

| Key available | Default model |
|---|---|
| `NVIDIA_API_KEY` | `minimaxai/minimax-m3` |
| `OPENROUTER_API_KEY` | `google/gemini-2.5-flash` |
| `GROQ_API_KEY` | `llama-3.3-70b-versatile` |

## Model Overrides

```env
SUPERVISOR_MODEL=google/gemini-2.5-flash   # Model for planning and synthesis
SUB_AGENT_MODEL=llama-3.3-70b-versatile    # Model for sub-agents
```

Different models can be used for the supervisor and sub-agents.

## Base URL Overrides

```env
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
GROQ_BASE_URL=https://api.groq.com/openai/v1
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

## LLM Hyperparameters

Hardcoded defaults in `config.py`:

| Parameter | Default |
|---|---|
| `TEMPERATURE` | `1.0` |
| `TOP_P` | `0.95` |
| `MAX_TOKENS` | `16384` |
| `THINKING` | `False` |

`THINKING` can be toggled at runtime with the `/think` command, which rebuilds the graph.

## Search Configuration

```env
SEARCH_PROVIDER=tavily        # "tavily" | "brave" | "google"
TAVILY_API_KEY=tvly-...
BRAVE_API_KEY=BSA...
GOOGLE_API_KEY=AIza...
GOOGLE_CSE_ID=...
```

## Example `.env`

```env
GROQ_API_KEY=gsk_...
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-...
```
