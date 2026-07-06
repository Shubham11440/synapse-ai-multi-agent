"""
exceptions.py — Custom exceptions for the Synapse AI Orchestration Platform.
Provides clean wrapping of raw provider API errors and validation failures.
"""
from __future__ import annotations


class SynapseBaseError(Exception):
    """Base exception class for all Synapse AI runtime errors."""

    def __init__(self, message: str, original_exception: Exception | None = None):
        super().__init__(message)
        self.original_exception = original_exception


class ProviderUnavailableError(SynapseBaseError):
    """Raised when the LLM provider (Gemini or OpenAI) is offline or API key is invalid."""
    pass


class ValidationError(SynapseBaseError):
    """Raised when Pydantic schema validation fails or response format is invalid."""
    pass


class MemoryError(SynapseBaseError):
    """Raised when long-term memory operations fail to load or serialize."""
    pass


class SearchToolError(SynapseBaseError):
    """Raised when a mock or live search tool fails to retrieve database findings."""
    pass
