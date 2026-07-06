"""
app.py — FastAPI REST API for the Synapse AI Company System.

Endpoints:
  POST /run       — Run a workflow (mode: 2agent | 4agent | company)
  GET  /health    — System health check
  GET  /logs      — Return recent monitoring logs
  GET  /summary   — Monitoring aggregate stats

Run with:
  uvicorn synapse_agents.app:app --reload --port 8000
"""
from __future__ import annotations

import sys
import os
import time
from typing import Literal

# Ensure the package directory is importable regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from orchestrator import run_2agent, run_4agent, run_company_system
from monitoring import get_logs, get_summary

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Synapse AI — Multi-Agent System API",
    description=(
        "Production API for the Synapse AI multi-agent system. "
        "Supports 2-agent, 4-agent, and full 6-agent company workflows."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    query: str = Field(
        ...,
        description="The business question or request to process.",
        example="Create a go-to-market strategy for an AI customer support product.",
    )
    mode: Literal["2agent", "4agent", "company"] = Field(
        default="company",
        description="Which pipeline to run.",
    )


class RunResponse(BaseModel):
    status: str
    mode: str
    query: str
    latency_ms: int
    result: dict


class HealthResponse(BaseModel):
    status: str
    version: str
    available_modes: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialise(obj) -> dict | list | str | int | float | bool | None:
    """Recursively convert Pydantic models and nested structures to plain dicts."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return {k: _serialise(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialise(i) for i in obj]
    return obj


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    """Returns system health and available pipeline modes."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        available_modes=["2agent", "4agent", "company"],
    )


@app.post("/run", response_model=RunResponse, tags=["Workflow"])
def run(request: RunRequest):
    """
    Run the multi-agent workflow for the given query and mode.

    - **2agent**: Research + Summarizer (Day 1)
    - **4agent**: Planner + Research + Analyst + Report (Day 2)
    - **company**: Full 6-agent production system with monitoring + retry
    """
    start = time.monotonic()

    try:
        if request.mode == "2agent":
            result = run_2agent(request.query)
        elif request.mode == "4agent":
            result = run_4agent(request.query)
        else:
            result = run_company_system(request.query)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workflow error: {exc}")

    latency_ms = round((time.monotonic() - start) * 1000)
    return RunResponse(
        status="success",
        mode=request.mode,
        query=request.query,
        latency_ms=latency_ms,
        result=_serialise(result),
    )


@app.get("/logs", tags=["Monitoring"])
def logs(limit: int = 50):
    """Return the most recent monitoring log entries."""
    return {"logs": get_logs(limit=limit)}


@app.get("/summary", tags=["Monitoring"])
def summary():
    """Return aggregate monitoring statistics across all runs."""
    return get_summary()
