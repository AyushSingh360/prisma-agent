import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# Check model names from environment first
env_supervisor_model = os.getenv("SUPERVISOR_MODEL")
env_sub_agent_model = os.getenv("SUB_AGENT_MODEL")

# Determine defaults based on available keys
if NVIDIA_API_KEY and not NVIDIA_API_KEY.startswith("your-"):
    DEFAULT_MODEL = "minimaxai/minimax-m3"
elif OPENROUTER_API_KEY and not OPENROUTER_API_KEY.startswith("your-"):
    DEFAULT_MODEL = "google/gemini-2.5-flash"
elif GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_"):
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
else:
    DEFAULT_MODEL = "google/gemini-2.5-flash"

SUPERVISOR_MODEL = env_supervisor_model or DEFAULT_MODEL
SUB_AGENT_MODEL = env_sub_agent_model or DEFAULT_MODEL

# Route to the appropriate provider based on the selected model name
if "gemini" in SUPERVISOR_MODEL.lower() or SUPERVISOR_MODEL.startswith("google/"):
    API_KEY = OPENROUTER_API_KEY
    BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
elif "minimax" in SUPERVISOR_MODEL.lower() or "nvidia" in SUPERVISOR_MODEL.lower():
    API_KEY = NVIDIA_API_KEY
    BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
else:
    if GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_") and any(m in SUPERVISOR_MODEL.lower() for m in ["llama", "mixtral", "gemma"]):
        API_KEY = GROQ_API_KEY
        BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    else:
        API_KEY = OPENROUTER_API_KEY
        BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

TEMPERATURE = 1.0
TOP_P = 0.95
MAX_TOKENS = 16384
THINKING = False

SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "tavily")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_CX") or "AQ.Ab8RN6KCx2Gfep4AtBJoQDEnSniAY1Gxu4NnkuCmhQuCfuM08Q"

# AeroLive API key (provided by user)
AERO_API_KEY = os.getenv("AERO_API_KEY")
