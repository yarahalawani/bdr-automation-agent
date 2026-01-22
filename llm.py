import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_client() -> OpenAI:
    # OpenAI SDK automatically reads OPENAI_API_KEY from env per quickstart. :contentReference[oaicite:1]{index=1}
    return OpenAI()

def get_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
