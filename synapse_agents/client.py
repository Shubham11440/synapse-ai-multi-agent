"""
client.py — Shared LLM client factory.

Eliminates the duplicated API-key detection and client initialisation
that previously lived in every agents.py file.

Usage (from any module):
    from client import llm_call

    output = llm_call(
        system_prompt="...",
        user_content="...",
        response_schema=MyPydanticModel,
        temperature=0.1,
    )
    # returns a validated Pydantic model instance
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Type, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel

# Load .env from the package directory first, then the repo root
_pkg = Path(__file__).resolve().parent
load_dotenv(dotenv_path=_pkg / ".env")
load_dotenv(dotenv_path=_pkg.parent / ".env")
load_dotenv()  # system environment fallback

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not GEMINI_API_KEY and not OPENAI_API_KEY:
    raise EnvironmentError(
        "No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY "
        "in a .env file or as an environment variable."
    )

# Prefer Gemini; fall back to OpenAI
USE_OPENAI: bool = bool(OPENAI_API_KEY and not GEMINI_API_KEY)

if USE_OPENAI:
    from openai import OpenAI as _OpenAI

    _client = _OpenAI(api_key=OPENAI_API_KEY)
    MODEL_NAME = "gpt-4o-mini"
    print(f"[LLM Client] Provider: OpenAI  |  Model: {MODEL_NAME}")
else:
    from google import genai as _genai
    from google.genai import types as _types

    _client = _genai.Client(api_key=GEMINI_API_KEY)
    MODEL_NAME = "gemini-2.5-flash"
    print(f"[LLM Client] Provider: Gemini  |  Model: {MODEL_NAME}")

T = TypeVar("T", bound=BaseModel)


def llm_call(
    system_prompt: str,
    user_content: str,
    response_schema: Type[T],
    temperature: float = 0.2,
) -> T:
    """
    Send a single structured LLM request and return a validated Pydantic model.

    Args:
        system_prompt   : The agent's role/instruction string.
        user_content    : The user-facing context/question.
        response_schema : A Pydantic BaseModel class defining the output structure.
        temperature     : Sampling temperature (lower = more deterministic).

    Returns:
        A validated instance of *response_schema*.
    """
    if USE_OPENAI:
        resp = _client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format=response_schema,
            temperature=temperature,
        )
        return resp.choices[0].message.parsed
    else:
        resp = _client.models.generate_content(
            model=MODEL_NAME,
            contents=user_content,
            config=_types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=temperature,
            ),
        )
        return response_schema.model_validate_json(resp.text)


# Expose the underlying client for edge cases (e.g. streaming)
raw_client = _client
