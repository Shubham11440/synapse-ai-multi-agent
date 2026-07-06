"""
config.py — Central configuration management for Synapse AI.
Reads environment variables with production-ready defaults.
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory Setup
BASE_DIR = Path(__file__).resolve().parent

# Load environment files
load_dotenv(dotenv_path=BASE_DIR / ".env")
load_dotenv(dotenv_path=BASE_DIR.parent / ".env")
load_dotenv()  # system fallback

# API Keys
GEMINI_API_KEY: str | None = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY: str | None = os.environ.get("OPENAI_API_KEY")

# Provider Detection & Selection
DEFAULT_PROVIDER: str = os.environ.get("DEFAULT_PROVIDER", "").strip()

if not DEFAULT_PROVIDER:
    # Auto-detect based on key availability
    if GEMINI_API_KEY:
        DEFAULT_PROVIDER = "Gemini"
    elif OPENAI_API_KEY:
        DEFAULT_PROVIDER = "OpenAI"
    else:
        DEFAULT_PROVIDER = "Gemini"

if DEFAULT_PROVIDER.lower() == "openai":
    DEFAULT_PROVIDER = "OpenAI"
    DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gpt-4o-mini")
else:
    DEFAULT_PROVIDER = "Gemini"
    DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gemini-2.5-flash")

# LLM Options
DEFAULT_TEMPERATURE: float = float(os.environ.get("LLM_TEMPERATURE", "0.2"))
LLM_TIMEOUT_SECONDS: float = float(os.environ.get("LLM_TIMEOUT_SECONDS", "30.0"))

# Orchestrator & Retries
MAX_API_RETRIES: int = int(os.environ.get("MAX_API_RETRIES", "3"))
MAX_REVIEWER_RETRIES: int = int(os.environ.get("MAX_REVIEWER_RETRIES", "1"))
RATE_LIMIT_SLEEP_SECONDS: int = int(os.environ.get("RATE_LIMIT_SLEEP_SECONDS", "5"))

# Storage Paths
MEMORY_STORE_PATH: Path = Path(os.environ.get(
    "MEMORY_STORE_PATH",
    str(BASE_DIR / "data" / "memory_store.json")
))
LOG_FILE_PATH: Path = Path(os.environ.get(
    "LOG_FILE_PATH",
    str(BASE_DIR / "data" / "logs.json")
))

# Create directories if they do not exist
MEMORY_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Dashboard Styling Settings
DASHBOARD_THEME: str = os.environ.get("DASHBOARD_THEME", "dark")
