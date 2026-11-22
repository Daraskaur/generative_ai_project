
"""
Groq LLM initialization and configuration.
"""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY is missing from .env file")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)
