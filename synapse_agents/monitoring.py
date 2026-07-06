"""
monitoring.py — Logging and performance telemetry for the Synapse Multi-Agent Platform.
Provides Python standard logging configuration and structured JSON output to logs.json.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Any

import config

# Setup storage path from config
_LOGS_PATH = Path(config.LOG_FILE_PATH)
_LOGS_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Setup Standard Python Logging
# ---------------------------------------------------------------------------

# Configure root-level logging for SynapseAI
logger = logging.getLogger("SynapseAI")
logger.setLevel(logging.DEBUG)

# Avoid adding duplicate handlers if reloaded
if not logger.handlers:
    # Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Text Format: [Timestamp] [Level] [Logger] message
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def _load_logs() -> list[dict[str, Any]]:
    """Loads current execution log history from logs.json."""
    if _LOGS_PATH.exists():
        try:
            return json.loads(_LOGS_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error(f"Could not load disk logs file: {exc}")
            return []
    return []


def _save_logs(logs: list[dict[str, Any]]) -> None:
    """Saves updated execution log list to logs.json."""
    try:
        _LOGS_PATH.write_text(
            json.dumps(logs, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as exc:
        logger.error(f"Could not write log entry to logs.json: {exc}")


class _LogEntry(dict):
    """
    Subclass representing a structured agent execution telemetry record.
    Writes itself to logs.json on completion and triggers console logging.
    """

    def close(self, status: str = "success", error: str | None = None) -> None:
        self["end_time"] = datetime.now(timezone.utc).isoformat()
        elapsed = time.monotonic() - self["_start_mono"]
        self["duration_ms"] = round(elapsed * 1000)
        self["status"] = status
        self["error"] = error
        
        # Remove internal mono timer
        self.pop("_start_mono", None)
        
        # Write to JSON storage
        logs = _load_logs()
        logs.append(dict(self))
        _save_logs(logs)

        # Output to console log stream based on execution outcome
        log_msg = (
            f"Agent: {self['agent']} | Status: {status} | "
            f"Duration: {self['duration_ms']}ms | Provider: {self['provider']} | "
            f"Model: {self['model']} | Retries: {self['retry_count']}"
        )
        if error:
            log_msg += f" | Error: {error}"
            logger.error(log_msg)
        else:
            logger.info(log_msg)


@contextmanager
def monitor(
    agent_name: str,
    input_text: str = "",
    retry_count: int = 0
) -> Iterator[_LogEntry]:
    """
    Context manager to log agent telemetry (latency, token chars, and providers).

    Purpose:
        Wrap agent execution in a telemetry timer, capture input/output metadata,
        and log the structured entry to both logs.json and system output.

    Arguments:
        agent_name: Unique identifier of the executing agent.
        input_text: Content passed to the agent (used to measure size).
        retry_count: Current retry iteration index.

    Returns:
        An active _LogEntry dictionary tracking execution states.

    Raises:
        Any exceptions raised inside the block will be caught, logged as errors,
        and then re-raised.
    """
    entry = _LogEntry(
        run_id=str(uuid.uuid4()),
        agent=agent_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
        start_time=datetime.now(timezone.utc).isoformat(),
        input_chars=len(input_text),
        output_chars=0,
        provider=config.DEFAULT_PROVIDER,
        model=config.DEFAULT_MODEL,
        retry_count=retry_count,
        _start_mono=time.monotonic(),
    )
    try:
        yield entry
        entry.close(status="success")
    except Exception as exc:
        entry.close(status="error", error=str(exc))
        raise


def get_logs(limit: int = 50) -> list[dict[str, Any]]:
    """
    Get recent monitoring logs.

    Arguments:
        limit: Max number of log items to return.

    Returns:
        List of recent log dictionaries.
    """
    return _load_logs()[-limit:]


def get_summary() -> dict[str, Any]:
    """
    Compute aggregate performance telemetry.

    Returns:
        A summary dictionary containing overall KPIs (Total runs, success rate, latencies).
    """
    logs = _load_logs()
    if not logs:
        return {
            "total_runs": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration_ms": 0,
            "max_duration_ms": 0,
            "agents_called": [],
            "provider": config.DEFAULT_PROVIDER,
            "model": config.DEFAULT_MODEL,
            "retry_count": 0,
        }
    
    successful = [l for l in logs if l.get("status") == "success"]
    failed = [l for l in logs if l.get("status") == "error"]
    durations = [l["duration_ms"] for l in successful if "duration_ms" in l]
    total_retries = sum(l.get("retry_count", 0) for l in logs)

    return {
        "total_runs": len(logs),
        "successful": len(successful),
        "failed": len(failed),
        "avg_duration_ms": round(sum(durations) / len(durations)) if durations else 0,
        "max_duration_ms": max(durations) if durations else 0,
        "agents_called": list({l.get("agent", "") for l in logs}),
        "provider": config.DEFAULT_PROVIDER,
        "model": config.DEFAULT_MODEL,
        "retry_count": total_retries,
    }
