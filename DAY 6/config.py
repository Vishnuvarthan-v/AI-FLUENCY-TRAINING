import os
from dotenv import load_dotenv
from openai import OpenAI

from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROVIDER = os.getenv("PROVIDER", "groq")
MODEL = os.getenv("MODEL", "openai/gpt-oss-120b")

if PROVIDER == "groq":
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
else:
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

def banner(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)