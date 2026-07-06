# Synapse AI — Multi-Agent Labs

A progressive multi-agent AI system built across three labs, all consolidated into the `synapse_agents/` unified package.

---

## Architecture Overview

```
User Request
  → Planner Agent        (decomposes task)
  → Research Agent       (gathers evidence via tools)
  → Analyst Agent        (extracts insights + risks)
  → Strategy Agent       (business recommendations)       ← Final Lab only
  → Report Generator     (executive report)
  → Reviewer / QA Agent  (quality validation + retry)     ← Final Lab only
  → FastAPI Response + Monitoring Dashboard               ← Final Lab only
```

---

## Lab Progression

### Day 1 — 2-Agent Research & Summarization
Located in `synapse_agents/` (`--mode 2agent`)
- **Research Agent** — scans the knowledge base and extracts structured facts
- **Summarizer Agent** — synthesizes findings into a clean user-facing report
- Dual-provider support: Google Gemini (default) or OpenAI fallback

### Day 2 — 4-Agent Business Analyst System
Located in `synapse_agents/` (`--mode 4agent`)
- **Planner Agent** — decomposes the business query into subtasks
- **Research Agent** — collects evidence-backed findings per subtask
- **Analyst Agent** — derives insights, risks, and recommendations
- **Report Generator Agent** — compiles an executive business report
- **Features:** Shared memory with JSON persistence and keyword-based cross-run recall

### Final Project — 6-Agent AI Company Mini-System (Production Ready)
Located in `synapse_agents/` (`--mode company`)
- **Planner Agent** — estimates complexity and assigns the full agent team
- **Research Agent** — multi-tool evidence gathering (search + market data)
- **Analyst Agent** — strategic pattern recognition with memory recall injection
- **Strategy Agent** — converts insights into prioritized business recommendations
- **Report Generator Agent** — creates a polished, structured executive report
- **Reviewer / QA Agent** — validates quality and triggers automatic report regeneration if rejected
- **Features:**
  - Per-agent monitoring: latency, character counts, status, errors
  - Persistent logs written to `data/logs.json`
  - FastAPI: `POST /run`, `GET /health`, `GET /logs`
  - Streamlit dashboard: live workflow visualization + metrics

---

## Project Structure

```
synapse_agents/
├── .env                  # API keys (Gemini or OpenAI)
├── requirements.txt
├── schemas.py            # All Pydantic models
├── tools.py              # Mock knowledge base + market tools
├── memory.py             # Session + persistent JSON memory
├── prompts.py            # All agent system prompts
├── client.py             # Shared LLM factory (llm_call)
├── agents.py             # All 8 agent functions
├── monitoring.py         # Per-agent execution logger
├── orchestrator.py       # run_2agent / run_4agent / run_company_system
├── app.py                # FastAPI REST API
├── dashboard.py          # Streamlit monitoring dashboard
└── main.py               # CLI entrypoint (--mode flag)
    data/
    ├── memory_store.json
    └── logs.json
```

---

## How to Run

### Setup
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
pip install -r synapse_agents/requirements.txt
```

Set API keys in `synapse_agents/.env`:
```env
GEMINI_API_KEY=your_key_here
# OR
OPENAI_API_KEY=your_key_here
```

### CLI Execution
```bash
# Day 1 — 2-agent pipeline
python synapse_agents/main.py --mode 2agent

# Day 2 — 4-agent pipeline
python synapse_agents/main.py --mode 4agent

# Final — 6-agent company system
python synapse_agents/main.py --mode company

# Run all three back-to-back
python synapse_agents/main.py --mode all
```

### API Server
```bash
uvicorn synapse_agents.app:app --reload --port 8000
```
Endpoints:
- `POST http://localhost:8000/run` — submit a business query
- `GET  http://localhost:8000/health` — health check
- `GET  http://localhost:8000/logs` — recent monitoring logs

### Monitoring Dashboard
```bash
streamlit run synapse_agents/dashboard.py
```

---

## Example API Request
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a go-to-market strategy for an AI support product", "mode": "company"}'
```
