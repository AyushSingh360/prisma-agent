import os
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

SUPERVISOR_MODEL = "deepseek-ai/deepseek-v4-pro"
SUB_AGENT_MODEL = "deepseek-ai/deepseek-v4-pro"

TEMPERATURE = 1.0
TOP_P = 0.95
MAX_TOKENS = 16384
THINKING = False
