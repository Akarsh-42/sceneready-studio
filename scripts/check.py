"""Offline import/config checks. No API requests and no credentials printed."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.adk.agents import LlmAgent
from google.genai import types
from parallel import AsyncParallel

from app.main import app
from app.providers import gemini_output_schema
from app.prompts import ASSESSMENT_PROMPT, BREAKDOWN_PROMPT
from app.schemas import Assessment, Breakdown

for name, prompt, schema in (
    ("script_breakdown", BREAKDOWN_PROMPT, Breakdown),
    ("production_planner", ASSESSMENT_PROMPT, Assessment),
):
    agent = LlmAgent(
        name=name, model="gemini-3.8-flash", instruction=prompt,
        output_schema=gemini_output_schema(schema), output_key="structured_result",
        generate_content_config=types.GenerateContentConfig(
            max_output_tokens=6000,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
        ),
    )
    assert agent.name == name
assert AsyncParallel
assert any(route.path == "/api/run" for route in app.routes)
print("PASS: agent constructors, model config, Parallel import, and API routes.")
print("Live credentials, model availability, and network requests still need a live run.")
