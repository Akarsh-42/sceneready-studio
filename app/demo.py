"""Explicit offline rehearsal fixture. Never substituted for failed live results."""
from .schemas import Assessment, Breakdown


class DemoProvider:
    async def breakdown(self, brief):
        return Breakdown.model_validate({
            "summary": "Offline rehearsal: one scene, with planning questions and no verified external requirements.",
            "scenes": [{"id": "S01", "heading": "Rehearsal scene", "setting": "unknown", "time_of_day": "unknown",
                        "people": [], "equipment": [], "production_needs": ["Review the location and production details"],
                        "script_excerpt": brief.script[:180]}],
            "research_topics": ["location_access"],
            "missing_details": ["Which authority manages the exact location?", "What is the confirmed filming schedule?"],
        })

    async def search(self, query):
        return []

    async def assess(self, brief, breakdown, sources, warnings):
        items = [
            ("Confirm the location owner", "Locations", "high", "Identify the owner or managing authority before making a filming request."),
            ("Prepare an equipment list", "Camera", "medium", "List the cameras, lights, power sources, and any temporary structures."),
            ("Review the working schedule", "Production", "medium", "Confirm the proposed date and crew working hours."),
            ("Arrange a site safety review", "Safety", "high", "Ask a competent crew member to review site-specific hazards."),
        ]
        return Assessment.model_validate({
            "tasks": [{"title": title, "scene_ids": ["S01"], "department": department, "priority": priority,
                       "action": action, "rationale": "Illustrative planning suggestion; this offline run has no external evidence.",
                       "citations": [], "needs_verification": "Run live research and verify with the responsible person."}
                      for title, department, priority, action in items],
            "questions": ["What is the exact filming location?", "What equipment will the crew bring?"],
        })
