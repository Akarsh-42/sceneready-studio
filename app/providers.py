"""Google ADK agents and the required live Parallel Search API integration."""
import json
import os
import re
from html import unescape
from datetime import datetime, timezone
from uuid import uuid4

from .prompts import ASSESSMENT_PROMPT, BREAKDOWN_PROMPT
from .schemas import Assessment, Breakdown, Source, government_domain, source_url

HTML_ENTITY = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|amp|quot|apos|lt|gt);")


def decode_html_entities(value):
    """Decode complete entities emitted by a model without interpreting HTML."""
    if isinstance(value, str):
        return HTML_ENTITY.sub(lambda match: unescape(match.group(0)), value)
    if isinstance(value, list):
        return [decode_html_entities(item) for item in value]
    if isinstance(value, dict):
        return {key: decode_html_entities(item) for key, item in value.items()}
    return value


def gemini_output_schema(model):
    """Simplify generation constraints; retain all Pydantic runtime validation."""
    def simplify(node):
        if isinstance(node, list):
            return [simplify(item) for item in node]
        if not isinstance(node, dict):
            return node
        result = {}
        for key, value in node.items():
            if key in {"minLength", "maxLength", "minItems", "maxItems", "title"}:
                continue
            if key in {"properties", "$defs"}:
                # Property names such as a task's 'title' are not schema keywords.
                result[key] = {name: simplify(child) for name, child in value.items()}
            else:
                result[key] = simplify(value)
        return result

    class GeminiOutput(model):
        @classmethod
        def model_json_schema(cls, *args, **kwargs):
            return simplify(super().model_json_schema(*args, **kwargs))

    return GeminiOutput


class LiveProvider:
    async def structured(self, name, instruction, schema, payload):
        from google.adk.agents import LlmAgent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        agent = LlmAgent(
            name=name,
            model=os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
            instruction=instruction,
            output_schema=gemini_output_schema(schema),
            output_key="structured_result",
            generate_content_config=types.GenerateContentConfig(
                max_output_tokens=6000,
                thinking_config=types.ThinkingConfig(thinking_level="LOW"),
            ),
        )
        service = InMemorySessionService()
        session = await service.create_session(app_name="sceneready", user_id="run", session_id=uuid4().hex)
        runner = Runner(agent=agent, app_name="sceneready", session_service=service)
        try:
            async for event in runner.run_async(
                user_id="run", session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part(text=json.dumps(payload))]),
            ):
                if getattr(event, "error_code", None):
                    raise RuntimeError("The agent returned an error.")
            result_session = await service.get_session(app_name="sceneready", user_id="run", session_id=session.id)
            value = result_session.state.get("structured_result")
            value = json.loads(value) if isinstance(value, str) else value
            return schema.model_validate(decode_html_entities(value))
        finally:
            await runner.close()

    async def breakdown(self, brief):
        return await self.structured("script_breakdown", BREAKDOWN_PROMPT, Breakdown, brief.model_dump(mode="json"))

    async def assess(self, brief, breakdown, sources, warnings):
        return await self.structured("production_planner", ASSESSMENT_PROMPT, Assessment, {
            "brief": brief.model_dump(mode="json"), "breakdown": breakdown.model_dump(),
            "sources": [source.model_dump() for source in sources], "research_warnings": warnings,
        })

    async def search(self, query):
        from parallel import AsyncParallel
        async with AsyncParallel(api_key=os.environ["PARALLEL_API_KEY"], timeout=30.0, max_retries=1) as client:
            response = await client.search(
                objective="Find authoritative filming guidance relevant to this query. Prefer official sources: " + query,
                search_queries=[query],
            )
        now = datetime.now(timezone.utc).isoformat()
        sources = []
        for result in response.results[:3]:
            parsed = source_url(result.url)
            if not parsed:
                continue
            url, host = parsed
            sources.append(Source(
                id="pending", title=result.title[:300], url=url, domain=host,
                government_domain=government_domain(host),
                excerpts=[text[:3000] for text in (result.excerpts or [])[:2]],
                retrieved_at=now, query=query,
            ))
        return sources
