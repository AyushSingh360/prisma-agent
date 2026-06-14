import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

SUPERVISOR_MODEL = os.getenv("SUPERVISOR_MODEL", "google/gemini-2.5-flash")
SUB_AGENT_MODEL = os.getenv("SUB_AGENT_MODEL", "google/gemini-2.5-flash")

TEMPERATURE = 1.0
TOP_P = 0.95
MAX_TOKENS = 16384
THINKING = False

SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "tavily")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
