"""
utils.py - Core Utilities and LLM Engine Interface
Provides environment variable loading, LLM connector (Groq, Ollama, OpenAI),
text cleaning, and formatting helpers.
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Locate and load .env from the project root
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

DEFAULT_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()


def get_llm_config():
    """Returns the current LLM configuration dictionary."""
    return {
        "provider": DEFAULT_PROVIDER,
        "groq_model": GROQ_MODEL,
        "ollama_model": OLLAMA_MODEL,
        "openai_model": OPENAI_MODEL,
        "has_groq_key": bool(GROQ_API_KEY and not GROQ_API_KEY.startswith("your_")),
        "has_openai_key": bool(OPENAI_API_KEY and not OPENAI_API_KEY.startswith("your_")),
    }


def call_groq(prompt: str, system_prompt: str = None, temperature: float = 0.5) -> str:
    """Invokes the Groq Cloud LLM API using requests."""
    if not GROQ_API_KEY or GROQ_API_KEY.startswith("your_"):
        raise ValueError("GROQ_API_KEY is not configured in .env")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1500
    }

    response = requests.post(url, headers=headers, json=payload, timeout=45)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def call_ollama(prompt: str, system_prompt: str = None, temperature: float = 0.5) -> str:
    """Invokes the local Ollama LLM API."""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }

    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"].strip()


def call_openai(prompt: str, system_prompt: str = None, temperature: float = 0.5) -> str:
    """Invokes OpenAI Chat Completion API."""
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("your_"):
        raise ValueError("OPENAI_API_KEY is not configured in .env")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": temperature
    }

    response = requests.post(url, headers=headers, json=payload, timeout=45)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def call_llm(prompt: str, system_prompt: str = None, temperature: float = 0.5) -> str:
    """
    Unified LLM caller that prioritizes the configured DEFAULT_LLM_PROVIDER
    and automatically falls back if needed.
    """
    provider = DEFAULT_PROVIDER

    # 1. Try Groq if selected or if key is provided
    if provider == "groq" or (provider != "ollama" and GROQ_API_KEY and not GROQ_API_KEY.startswith("your_")):
        try:
            return call_groq(prompt, system_prompt, temperature)
        except Exception as e:
            print(f"[Warning] Groq call failed ({e}). Falling back to local Ollama...")

    # 2. Try Ollama (Local fallback)
    try:
        return call_ollama(prompt, system_prompt, temperature)
    except Exception as e:
        print(f"[Warning] Ollama call failed ({e}).")

    # 3. Try OpenAI if available
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("your_"):
        return call_openai(prompt, system_prompt, temperature)

    raise RuntimeError("No LLM provider was able to respond. Check your Groq key or Ollama service.")


def sanitize_text(text: str) -> str:
    """
    Sanitizes unicode characters (fancy quotes, non-breaking hyphens, em-dashes)
    to prevent UnicodeEncodeError on Windows cp1252 console.
    """
    if not isinstance(text, str):
        return str(text)
    replacements = {
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "--",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u2022": "*",
        "\xa0": " ",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text.encode("ascii", "replace").decode("ascii")


def clean_json_response(text: str) -> dict:
    """
    Safely extracts and parses JSON from LLM markdown code blocks or raw strings.
    """
    clean_text = sanitize_text(text).strip()
    if "```json" in clean_text:
        clean_text = clean_text.split("```json", 1)[1]
        clean_text = clean_text.split("```", 1)[0]
    elif "```" in clean_text:
        clean_text = clean_text.split("```", 1)[1]
        clean_text = clean_text.split("```", 1)[0]

    return json.loads(clean_text.strip())


def print_banner(title: str, width: int = 60):
    """Prints a styled terminal banner."""
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width + "\n")
