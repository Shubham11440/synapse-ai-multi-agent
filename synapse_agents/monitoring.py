"""
monitoring.py — Per-agent execution logger for the Synapse company system.

Usage:
    from monitoring import monitor

    with monitor("research_agent") as log:
        result = research_agent_company(plan)
    # log is automatically saved to data/logs.json

Or wrap imperatively:
    monitor.start("planner_agent")
    ...
    monitor.finish("planner_agent", status="success")
"""
from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

_LOGS_PATH = Path(__file__).resolve().parent / "data" / "logs.json"
_LOGS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_logs() -> list:
    if _LOGS_PATH.exists():
        try:
            return json.loads(_LOGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_logs(logs: list) -> None:
    try:
        _LOGS_PATH.write_text(
            json.dumps(logs, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as exc:
        print(f"[Monitoring] Could not write logs: {exc}")


class _LogEntry(dict):
    """A dict subclass that also writes itself to disk when closed."""

    def close(self, status: str = "success", error: str | None = None) -> None:
        self["end_time"] = datetime.now(timezone.utc).isoformat()
        elapsed = time.monotonic() - self["_start_mono"]
        self["duration_ms"] = round(elapsed * 1000)
        self["status"] = status
        self["error"] = error
        # Remove internal key before persisting
        self.pop("_start_mono", None)
        logs = _load_logs()
        logs.append(dict(self))
        _save_logs(logs)


@contextmanager
def monitor(agent_name: str, input_text: str = "") -> Iterator[_LogEntry]:
    """
    Context manager that times an agent call and logs the result.

    Example:
        with monitor("analyst_agent", input_text=context) as entry:
            result = analyst_agent(...)
            entry["output_chars"] = len(result.model_dump_json())
    """
    entry = _LogEntry(
        run_id=str(uuid.uuid4()),
        agent=agent_name,
        start_time=datetime.now(timezone.utc).isoformat(),
        input_chars=len(input_text),
        output_chars=0,
        _start_mono=time.monotonic(),
    )
    try:
        yield entry
        entry.close(status="success")
    except Exception as exc:
        entry.close(status="error", error=str(exc))
        raise


def get_logs(limit: int = 50) -> list:
    """Return the most recent *limit* log entries."""
    return _load_logs()[-limit:]


def get_summary() -> dict:
    """Aggregate stats across all logged runs."""
    logs = _load_logs()
    if not logs:
        return {"total_runs": 0}
    successful = [l for l in logs if l.get("status") == "success"]
    failed = [l for l in logs if l.get("status") == "error"]
    durations = [l["duration_ms"] for l in successful if "duration_ms" in l]
    return {
        "total_runs": len(logs),
        "successful": len(successful),
        "failed": len(failed),
        "avg_duration_ms": round(sum(durations) / len(durations)) if durations else 0,
        "max_duration_ms": max(durations) if durations else 0,
        "agents_called": list({l["agent"] for l in logs}),
    }
