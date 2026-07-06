import os
import json
from dotenv import load_dotenv

from schemas import ResearchAgentOutput, SummarizerAgentOutput
from tools import mock_search
from prompts import RESEARCH_AGENT_SYSTEM_PROMPT, SUMMARIZER_AGENT_SYSTEM_PROMPT

# Load environment variables from current directory, parent directory, and system environment
load_dotenv()
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env')
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

# Check which API key is available
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

use_openai = False
# Prefer Gemini if both exist (as it is standard in the workspace), fallback to OpenAI
if OPENAI_API_KEY and not GEMINI_API_KEY:
    use_openai = True
elif not GEMINI_API_KEY and not OPENAI_API_KEY:
    raise ValueError(
        "Neither GEMINI_API_KEY nor OPENAI_API_KEY is set. "
        "Please configure at least one API key in a .env file or environment variables."
    )

if use_openai:
    from openai import OpenAI
    # Clean standard OpenAI setup
    client = OpenAI(api_key=OPENAI_API_KEY)
    MODEL_NAME = "gpt-4o-mini"
    print(f"[Initialization] Using OpenAI Engine: {MODEL_NAME}")
else:
    from google import genai
    from google.genai import types
    # Modern Google GenAI SDK setup
    client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL_NAME = "gemini-2.5-flash"
    print(f"[Initialization] Using Gemini Engine: {MODEL_NAME}")

def research_agent(user_query: str) -> ResearchAgentOutput:
    """
    Research Agent: Gathers raw findings using the mock_search tool,
    sends them to the API, and returns a structured ResearchAgentOutput object.
    """
    # 1. Fetch raw findings from mock database
    search_data = mock_search(user_query)
    results_str = "\n".join([f"- {r}" for r in search_data["results"]])
    sources_str = ", ".join(search_data["sources"])

    # 2. Structure context for the LLM
    context = f"""User Query: {user_query}

Retrieved Database Snippets:
{results_str}

Sources:
{sources_str}
"""

    # 3. Request structured output from LLM
    if use_openai:
        response = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": RESEARCH_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            response_format=ResearchAgentOutput,
            temperature=0.1
        )
        return response.choices[0].message.parsed
    else:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=RESEARCH_AGENT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ResearchAgentOutput,
                temperature=0.1,
            )
        )
        # Parse and validate JSON against Pydantic schema
        return ResearchAgentOutput.model_validate_json(response.text)

def summarizer_agent(research_output: ResearchAgentOutput) -> SummarizerAgentOutput:
    """
    Summarizer Agent: Accepts structured research findings,
    synthesizes a clean user-facing summary, and returns a structured SummarizerAgentOutput.
    """
    # 1. Prepare structured findings as JSON string context
    context = f"""Please summarize the following research findings:
{research_output.model_dump_json(indent=2)}
"""

    # 2. Request structured output from LLM
    if use_openai:
        response = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SUMMARIZER_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            response_format=SummarizerAgentOutput,
            temperature=0.3
        )
        return response.choices[0].message.parsed
    else:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=SUMMARIZER_AGENT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=SummarizerAgentOutput,
                temperature=0.3,
            )
        )
        # Parse and validate JSON against Pydantic schema
        return SummarizerAgentOutput.model_validate_json(response.text)
