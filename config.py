import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Check which API key is present and set defaults accordingly
if GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_"):
    API_KEY = GROQ_API_KEY
    BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
elif OPENROUTER_API_KEY and OPENROUTER_API_KEY.startswith("gsk_"):
    API_KEY = OPENROUTER_API_KEY
    BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
else:
    API_KEY = OPENROUTER_API_KEY
    BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    DEFAULT_MODEL = "google/gemini-2.5-flash"

SUPERVISOR_MODEL = os.getenv("SUPERVISOR_MODEL", DEFAULT_MODEL)
SUB_AGENT_MODEL = os.getenv("SUB_AGENT_MODEL", DEFAULT_MODEL)

TEMPERATURE = 1.0
TOP_P = 0.95
MAX_TOKENS = 16384
THINKING = False

SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "tavily")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
