import os
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

SUPERVISOR_MODEL = "meta/llama-3.1-70b-instruct"
SUB_AGENT_MODEL = "meta/llama-3.1-70b-instruct"
