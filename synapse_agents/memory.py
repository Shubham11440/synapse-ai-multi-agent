"""
memory.py — Shared MemoryStore used by orchestrators.
Supports session memory (in-memory dict) and persistent long-term storage
for cross-run recall with custom exception wrapping.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import config
from exceptions import MemoryError

logger = logging.getLogger("SynapseAI")


class MemoryStore:
    """
    Unified session + persistent memory store.
    Provides session caching and persistent JSON storage.
    """

    def __init__(self, storage_path: str | None = None) -> None:
        """
        Initialize MemoryStore with standard path or override.

        Purpose:
            Load persistent memory data from disk and prepare empty session state.

        Arguments:
            storage_path: Optional storage path override. Defaults to config.MEMORY_STORE_PATH.
        """
        if storage_path is None:
            self.storage_path = Path(config.MEMORY_STORE_PATH)
        else:
            self.storage_path = Path(storage_path)

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self._session: dict[str, Any] = {}
        self._long_term: dict[str, Any] = self._load()

    def save_session(self, key: str, value: Any) -> None:
        """
        Save a value into current session state.

        Purpose:
            Keep runtime values active for the current orchestrator loop execution.

        Arguments:
            key: State key name.
            value: The data or object to cache.
        """
        self._session[key] = value

    def load_session(self, key: str) -> Any | None:
        """
        Retrieve a value from current session state.

        Purpose:
            Access cached runtime objects within the current orchestrator session.

        Arguments:
            key: State key name.

        Returns:
            The cached value or None if not found.
        """
        return self._session.get(key)

    def save_report(self, query: str, report: dict[str, Any]) -> None:
        """
        Persist a final report keyed by normalised query.

        Purpose:
            Write finalized reports to disk for long-term recall capability.

        Arguments:
            query: The business query string.
            report: The dictionary representation of the report.

        Raises:
            MemoryError: If file writing fails.
        """
        self._long_term[query.lower().strip()] = {"query": query, "report": report}
        self._flush()

    def recall(self, query: str) -> dict[str, Any] | None:
        """
        Find the closest past report matching query keywords.

        Purpose:
            Recall historical business insight summaries to guide agents in future planning.

        Arguments:
            query: The business query string.

        Returns:
            A matching past report dictionary or None.
        """
        q = query.lower().strip()
        _KEYWORDS = ["support", "sales", "operations", "customer", "productivity", "automation"]
        q_kws = [kw for kw in _KEYWORDS if kw in q]

        for past_q, data in self._long_term.items():
            if past_q in q or q in past_q:
                return data["report"]
            if any(kw in past_q for kw in q_kws):
                return data["report"]
        return None

    def _load(self) -> dict[str, Any]:
        """Loads JSON storage from disk."""
        if self.storage_path.exists():
            try:
                return json.loads(self.storage_path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.error(f"Failed to load long term memory from {self.storage_path}: {exc}")
                raise MemoryError(f"Could not load memory file at {self.storage_path}", exc)
        return {}

    def _flush(self) -> None:
        """Serializes current long-term memory to disk."""
        try:
            self.storage_path.write_text(
                json.dumps(self._long_term, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error(f"Failed to save long term memory to {self.storage_path}: {exc}")
            raise MemoryError(f"Could not save memory file at {self.storage_path}", exc)
