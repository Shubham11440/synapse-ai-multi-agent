"""
client.py — Unified LLM client factory.
Manages API client instances, executes structured schema generation,
and handles custom exception wrapping for OpenAI and Google Gemini.
"""
from __future__ import annotations

import logging
from typing import Type, TypeVar, Any
from pydantic import BaseModel, ValidationError as PydanticValidationError

import config
from exceptions import ProviderUnavailableError, ValidationError

# Global Logger Setup
logger = logging.getLogger("SynapseAI")

# Check that at least one API key is present
if not config.GEMINI_API_KEY and not config.OPENAI_API_KEY:
    raise EnvironmentError(
        "No API key found. Please set GEMINI_API_KEY or OPENAI_API_KEY in your env/dotenv configuration."
    )

# Select default provider and setup client
USE_OPENAI: bool = (config.DEFAULT_PROVIDER == "OpenAI")
MODEL_NAME: str = config.DEFAULT_MODEL

_client: Any = None

if USE_OPENAI:
    try:
        from openai import OpenAI as _OpenAI
        _client = _OpenAI(
            api_key=config.OPENAI_API_KEY,
            timeout=config.LLM_TIMEOUT_SECONDS,
        )
        logger.info(f"LLM Client initialized with OpenAI (Model: {MODEL_NAME})")
    except Exception as exc:
        raise ProviderUnavailableError("Failed to initialize OpenAI client instance.", exc)
else:
    try:
        from google import genai as _genai
        from google.genai import types as _types
        # Client initializes with key or picks it up from environment
        _client = _genai.Client(api_key=config.GEMINI_API_KEY)
        logger.info(f"LLM Client initialized with Gemini (Model: {MODEL_NAME})")
    except Exception as exc:
        raise ProviderUnavailableError("Failed to initialize Google GenAI client instance.", exc)

T = TypeVar("T", bound=BaseModel)


def llm_call(
    system_prompt: str,
    user_content: str,
    response_schema: Type[T],
    temperature: float | None = None,
) -> T:
    """
    Sends a structured LLM request and returns a validated Pydantic model.

    Purpose:
        Executes structured generation using either OpenAI structured outputs
        or Gemini JSON schema validation, wrapping any provider/network/parsing errors.

    Arguments:
        system_prompt: The agent's system role/instructions.
        user_content: The context or query to process.
        response_schema: A Pydantic BaseModel type to validate the output against.
        temperature: Optional custom temperature. Defaults to config.DEFAULT_TEMPERATURE.

    Returns:
        An instance of the response_schema BaseModel populated with structured data.

    Raises:
        ProviderUnavailableError: If the LLM provider fails to respond, timeouts, or API authentication fails.
        ValidationError: If the model returns invalid JSON or fails Pydantic schema validation.

    Examples:
        >>> from schemas import SummarizerOutput
        >>> result = llm_call("You are a summarizer.", "Context data...", SummarizerOutput)
    """
    temp = temperature if temperature is not None else config.DEFAULT_TEMPERATURE

    if USE_OPENAI:
        try:
            resp = _client.beta.chat.completions.parse(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format=response_schema,
                temperature=temp,
            )
            parsed = resp.choices[0].message.parsed
            if parsed is None:
                raise ValidationError("OpenAI parsed response is null.")
            return parsed
        except PydanticValidationError as exc:
            logger.error(f"OpenAI response failed Pydantic validation: {exc}")
            raise ValidationError("Failed to validate LLM response format.", exc)
        except Exception as exc:
            logger.error(f"OpenAI API call failed: {exc}")
            raise ProviderUnavailableError("OpenAI provider API call failed or timed out.", exc)
    else:
        try:
            resp = _client.models.generate_content(
                model=MODEL_NAME,
                contents=user_content,
                config=_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=temp,
                ),
            )
            # Response text might be raw JSON; validate against target schema
            if not resp.text:
                raise ValidationError("Gemini generated an empty text response.")
            return response_schema.model_validate_json(resp.text)
        except PydanticValidationError as exc:
            logger.error(f"Gemini response failed Pydantic validation: {exc}")
            raise ValidationError("Failed to validate LLM response format.", exc)
        except Exception as exc:
            logger.error(f"Gemini API call failed: {exc}")
            raise ProviderUnavailableError("Google Gemini provider API call failed or timed out.", exc)


# Expose raw client for diagnostic or advanced usage
raw_client = _client
