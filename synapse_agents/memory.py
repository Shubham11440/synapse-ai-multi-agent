"""
memory.py — Shared MemoryStore used by the Day 2 orchestrator.

Supports:
  - Session memory  : in-memory dict for the current run
  - Long-term memory: JSON file serialization for cross-run recall
  - Recall lookup   : keyword-based matching of past reports
"""
from __future__ import annotations

import json
from pathlib import Path


class MemoryStore:
    """Unified session + persistent memory store."""

    def __init__(self, storage_path: str | None = None):
        if storage_path is None:
            base = Path(__file__).resolve().parent / "data"
            self.storage_path = base / "memory_store.json"
        else:
            self.storage_path = Path(storage_path)

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory session dict (reset each run)
        self._session: dict = {}
        # Persistent cross-run dict (loaded from disk)
        self._long_term: dict = self._load()

    # ------------------------------------------------------------------
    # Session memory
    # ------------------------------------------------------------------
    def save_session(self, key: str, value) -> None:
        self._session[key] = value

    def load_session(self, key: str):
        return self._session.get(key)

    # ------------------------------------------------------------------
    # Long-term memory
    # ------------------------------------------------------------------
    def save_report(self, query: str, report: dict) -> None:
        """Persist a final report keyed by the normalised query string."""
        self._long_term[query.lower().strip()] = {"query": query, "report": report}
        self._flush()

    def recall(self, query: str) -> dict | None:
        """
        Return the closest past report matching keywords in *query*, or None.
        Useful for injecting historical context into the Analyst prompt.
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

    # ------------------------------------------------------------------
    # Disk helpers
    # ------------------------------------------------------------------
    def _load(self) -> dict:
        if self.storage_path.exists():
            try:
                return json.loads(self.storage_path.read_text(encoding="utf-8"))
            except Exception as exc:
                print(f"[MemoryStore] Could not load disk store: {exc}")
        return {}

    def _flush(self) -> None:
        try:
            self.storage_path.write_text(
                json.dumps(self._long_term, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            print(f"[MemoryStore] Could not write disk store: {exc}")
