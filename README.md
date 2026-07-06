# Multi-Agent Collaboration Labs

This repository contains implementation code and high-level designs for two multi-agent system labs.

---

## 1. Day 1: 2-Agent Research and Summarization System
Located in `multi_agent_day1/`.
* **Research Agent**: Fetches internal knowledge base facts and creates structured notes.
* **Summarizer Agent**: Synthesizes structured findings into bullet points.
* **Features**: Dynamic fallback for OpenAI and Gemini APIs, structured Pydantic outputs, and side-by-side comparison metrics with a single-agent baseline.

---

## 2. Day 2: 4-Agent Business Analyst System
Located in `day2_multi_agent_system/`.
* **Planner Agent**: Decomposes the user request into strategic subtasks.
* **Research Agent**: Scans the mock database and collects factual evidence for subtasks.
* **Analyst Agent**: Evaluates the findings to extract insights, identify risks, and draft recommendations.
* **Report Generator Agent**: Compiles intermediate outputs into an executive business report.
* **Features**:
  - Task decomposition & sequential execution flow.
  - Multi-agent orchestrator with step-wise schema validation checks.
  - Shared memory layer with automated file serialization.
  - Historical memory recall to maintain context continuity across multiple runs.
  - Dynamic API configuration matching your local key setups (Gemini or OpenAI).

---

## 3. How to Run the Labs

### Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r multi_agent_day1/requirements.txt
   # OR
   pip install -r day2_multi_agent_system/requirements.txt
   ```
3. Set your API credentials in a `.env` file at the root directory:
   ```env
   GEMINI_API_KEY=your_key_here
   # OR
   OPENAI_API_KEY=your_key_here
   ```

### Execution
* **Day 1**: Run the 2-agent loop:
  ```bash
  python multi_agent_day1/main.py
  ```
* **Day 2**: Run the 4-agent orchestrator:
  ```bash
  python day2_multi_agent_system/main.py
  ```
