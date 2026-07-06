import os
import json
from pathlib import Path

class MemoryStore:
    """
    MemoryStore manages in-memory session states during orchestrator runs
    and handles long-term file-based serialization of completed reports for context recall.
    """
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            self.storage_dir = Path(__file__).resolve().parent / "data"
            self.storage_path = self.storage_dir / "memory_store.json"
        else:
            self.storage_path = Path(storage_path)
            self.storage_dir = self.storage_path.parent
            
        # Ensure directories exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Session Memory (in-memory dict)
        self.session_memory = {}
        
        # Long-Term Memory (persistent file-based dict)
        self.long_term_memory = self._load_from_disk()

    def save_session(self, key: str, value: any):
        """Saves intermediate outputs or values to the active orchestration session."""
        self.session_memory[key] = value

    def load_session(self, key: str) -> any:
        """Loads a session value by key."""
        return self.session_memory.get(key)

    def save_to_long_term(self, query: str, final_report: dict):
        """Persists a final report to the JSON file on disk."""
        self.long_term_memory[query.lower().strip()] = {
            "query": query,
            "final_report": final_report
        }
        self._write_to_disk()

    def recall_memory(self, query: str) -> dict:
        """
        Scans long-term memory for past reports matching keywords in the query.
        Returns the matching final report or None.
        """
        query_lower = query.lower().strip()
        keywords = ["support", "sales", "operations", "customer", "productivity", "automation"]
        query_keywords = [kw for kw in keywords if kw in query_lower]
        
        for past_query, data in self.long_term_memory.items():
            if past_query in query_lower or query_lower in past_query:
                return data["final_report"]
            if any(kw in past_query for kw in query_keywords):
                return data["final_report"]
                
        return None

    def _load_from_disk(self) -> dict:
        """Loads long-term memory from JSON file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[MemoryStore Warning] Failed to load disk memory: {e}")
                return {}
        return {}

    def _write_to_disk(self):
        """Saves long-term memory to JSON file."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.long_term_memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MemoryStore Error] Failed to write memory to disk: {e}")
