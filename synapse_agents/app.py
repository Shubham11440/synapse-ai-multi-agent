"""
app.py — FastAPI REST API for the Synapse AI Orchestration Platform.
Exposes routes to trigger pipelines and inspect performance/telemetry logs.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Literal, Any

# Ensure the package directory is importable regardless of CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

import config
from orchestrator import run_2agent, run_4agent, run_company_system, memory
from monitoring import get_logs, get_summary

# Initialize FastAPI instance
app = FastAPI(
    title="Synapse AI — Multi-Agent System API",
    description=(
        "Production API for the Synapse AI multi-agent system. "
        "Supports 2-agent, 4-agent, and full 6-agent company workflows."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    query: str = Field(
        ...,
        description="The business question or request to process.",
        example="Create a go-to-market strategy for an AI customer support product.",
    )
    mode: Literal["2agent", "4agent", "company"] = Field(
        default="company",
        description="Which pipeline mode to execute.",
    )


class RunResponse(BaseModel):
    status: str = Field(description="Execution result status (e.g. 'success').")
    mode: str = Field(description="The pipeline mode that was executed.")
    query: str = Field(description="The query that was submitted.")
    latency_ms: int = Field(description="Workflow execution duration in milliseconds.")
    result: dict[str, Any] = Field(description="Serialized output structures from all executing agents.")


class HealthResponse(BaseModel):
    status: str = Field(description="Overall system health status (e.g. 'healthy').")
    provider: str = Field(description="Current primary LLM provider (Gemini or OpenAI).")
    model: str = Field(description="Primary model name used by the system.")
    memory: str = Field(description="Status of long-term memory storage ('ok' or error detail).")
    logs: str = Field(description="Status of system logs storage ('ok' or error detail).")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialise(obj: Any) -> Any:
    """
    Recursively converts Pydantic models and nested structures to plain primitive types.

    Purpose:
        Clean JSON output payload generation for API responses.

    Arguments:
        obj: The object to serialize.

    Returns:
        Primitive Python representation of the object (dict, list, str, etc.).
    """
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

@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """
    Redirects root requests to Swagger UI docs.

    Purpose:
        Provide a friendly landing page pointing to developer endpoints.

    Returns:
        A RedirectResponse redirecting to '/docs'.
    """
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    """
    Get system health and state of storage.

    Purpose:
        Perform diagnostics check on long-term memory and logs storage paths.

    Returns:
        A HealthResponse containing status of LLM provider and persistent storage.

    Raises:
        HTTPException: 500 error if vital storage checks fail.
    """
    # Verify memory store access
    try:
        memory._load()
        memory_status = "ok"
    except Exception as exc:
        memory_status = f"error: {exc}"

    # Verify logs accessibility
    try:
        get_logs(limit=1)
        logs_status = "ok"
    except Exception as exc:
        logs_status = f"error: {exc}"

    return HealthResponse(
        status="healthy" if (memory_status == "ok" and logs_status == "ok") else "degraded",
        provider=config.DEFAULT_PROVIDER,
        model=config.DEFAULT_MODEL,
        memory=memory_status,
        logs=logs_status,
    )


@app.post("/run", response_model=RunResponse, tags=["Workflow"])
def run(request: RunRequest) -> RunResponse:
    """
    Execute a multi-agent workflow.

    Purpose:
        Dispatch user strategy requests to the appropriate agent loop execution.

    Arguments:
        request: The RunRequest containing the query and pipeline mode.

    Returns:
        A RunResponse mapping output results and overall runtime latency.

    Raises:
        HTTPException: 422 error for guardrail violations, 500 for runtime failure.
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
        raise HTTPException(status_code=500, detail=f"Workflow execution failure: {exc}")

    latency_ms = round((time.monotonic() - start) * 1000)
    return RunResponse(
        status="success",
        mode=request.mode,
        query=request.query,
        latency_ms=latency_ms,
        result=_serialise(result),
    )


@app.get("/logs", tags=["Monitoring"])
def logs(limit: int = 50) -> dict[str, list[dict[str, Any]]]:
    """
    Fetch recent telemetry logs.

    Purpose:
        Read structured performance telemetry entries.

    Arguments:
        limit: Max number of log items to retrieve.

    Returns:
        A dictionary mapping the key "logs" to a list of log records.
    """
    return {"logs": get_logs(limit=limit)}


@app.get("/summary", tags=["Monitoring"])
def summary() -> dict[str, Any]:
    """
    Get aggregate telemetry metrics.

    Purpose:
        Fetch aggregate latency, success rates, and active models.

    Returns:
        A telemetry summary dictionary.
    """
    return get_summary()
