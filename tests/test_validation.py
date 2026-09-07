import asyncio
import unittest

from pydantic import ValidationError

from app.demo import DemoProvider
from app.schemas import Assessment, Brief, Breakdown, Source, government_domain, source_url, validate_report
from app.workflow import run_workflow


def brief():
    return Brief(title="The Last Local", city="Mumbai, India", script="EXT. STREET - NIGHT. Two adults walk outside with a camera crew.")


def breakdown():
    return Breakdown.model_validate({
        "summary": "Night scene", "scenes": [{"id": "S01", "heading": "Street",
        "setting": "exterior", "time_of_day": "night", "people": [], "equipment": [],
        "production_needs": [], "script_excerpt": "Two adults walk outside"}],
        "research_topics": ["night_filming", "drone", "road_control"], "missing_details": [],
    })


def source():
    return Source(id="E01", title="Test fixture", url="https://example.org/film",
                  domain="example.org", government_domain=False,
                  excerpts=["Contact the location manager before planning the visit."],
                  retrieved_at="2026-09-06T00:00:00+00:00", query="test fixture")


def assessment(source_id="E01", quote="Contact the location manager"):
    return Assessment.model_validate({"tasks": [{"title": "Confirm the location", "scene_ids": ["S01"],
        "department": "Locations", "priority": "high", "action": "Ask the manager.",
        "rationale": "A planning suggestion.", "citations": [{"source_id": source_id, "quote": quote}],
        "needs_verification": "Check applicability."}], "questions": []})


class CitationTests(unittest.TestCase):
    def test_real_excerpt_maps_to_source_url(self):
        tasks, warnings = validate_report(assessment(), breakdown(), [source()])
        self.assertEqual(tasks[0]["evidence_status"], "excerpt_matched")
        self.assertEqual(tasks[0]["citations"][0]["url"], source().url)
        self.assertEqual(tasks[0]["review_status"], "open")
        self.assertEqual(warnings, [])

    def test_fabricated_quote_is_removed(self):
        tasks, warnings = validate_report(assessment(quote="Filming has already been fully approved."), breakdown(), [source()])
        self.assertEqual(tasks[0]["evidence_status"], "needs_evidence")
        self.assertEqual(tasks[0]["citations"], [])
        self.assertTrue(warnings)

    def test_unknown_source_is_removed(self):
        tasks, _ = validate_report(assessment(source_id="E99"), breakdown(), [source()])
        self.assertFalse(tasks[0]["citations"])

    def test_whitespace_only_quote_cannot_pass(self):
        tasks, _ = validate_report(assessment(quote=" " * 25), breakdown(), [source()])
        self.assertEqual(tasks[0]["evidence_status"], "needs_evidence")

    def test_whitespace_in_excerpt_is_normalized(self):
        item = source()
        item.excerpts = ["Contact the\nlocation  manager before planning the visit."]
        tasks, _ = validate_report(assessment(), breakdown(), [item])
        self.assertEqual(tasks[0]["evidence_status"], "excerpt_matched")

    def test_unknown_scene_reference_is_removed(self):
        item = assessment()
        item.tasks[0].scene_ids = ["S99"]
        tasks, warnings = validate_report(item, breakdown(), [source()])
        self.assertEqual(tasks[0]["scene_ids"], [])
        self.assertTrue(warnings)

    def test_empty_and_oversized_briefs_rejected(self):
        for script in [" ", "x" * 12001]:
            with self.assertRaises(ValidationError):
                Brief(title="Test", city="Mumbai", script=script)

    def test_url_and_domain_checks(self):
        for url in ["javascript:alert(1)", "https://user:pass@example.org", "https://localhost/x", "https://example.org/\nfoo"]:
            self.assertIsNone(source_url(url))
        self.assertTrue(government_domain("portal.gov.in"))
        self.assertFalse(government_domain("gov.in.example.org"))


class FakeProvider:
    def __init__(self, fail=False, duplicate=False):
        self.calls = []
        self.fail = fail
        self.duplicate = duplicate

    async def breakdown(self, input_brief):
        self.calls.append("breakdown")
        output = breakdown()
        if self.duplicate:
            output.scenes.append(output.scenes[0].model_copy())
        return output

    async def search(self, query):
        self.calls.append("search")
        if self.fail:
            raise RuntimeError("Sensitive provider body must never be exposed.")
        return [source()]

    async def assess(self, *args):
        self.calls.append("assess")
        return assessment()


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def collect(self, provider, demo=False):
        return [event async for event in run_workflow(brief(), provider, demo=demo)]

    async def test_research_is_mandatory_and_bounded(self):
        provider = FakeProvider()
        events = await self.collect(provider)
        self.assertEqual(provider.calls, ["breakdown", "search", "search", "search", "assess"])
        self.assertEqual(events[-1]["type"], "result")
        self.assertEqual(len(events[-1]["report"]["sources"]), 1)

    async def test_search_failures_remain_unknown(self):
        events = await self.collect(FakeProvider(fail=True))
        result = events[-1]["report"]
        self.assertEqual(result["sources"], [])
        self.assertEqual(result["tasks"][0]["evidence_status"], "needs_evidence")
        self.assertTrue(any("failed" in w for w in result["warnings"]))
        self.assertFalse(any("Sensitive" in w for w in result["warnings"]))

    async def test_duplicate_scene_ids_stop_the_run(self):
        with self.assertRaises(ValueError):
            await self.collect(FakeProvider(duplicate=True))

    async def test_demo_is_explicit_and_has_no_sources(self):
        events = await self.collect(DemoProvider(), demo=True)
        result = events[-1]["report"]
        self.assertEqual(result["mode"], "offline_rehearsal")
        self.assertEqual(result["sources"], [])
        self.assertTrue(result["warnings"][0].startswith("OFFLINE REHEARSAL"))

    async def test_each_run_starts_with_unreviewed_tasks(self):
        first = (await self.collect(FakeProvider()))[-1]["report"]
        first["tasks"][0]["review_status"] = "reviewed"
        second = (await self.collect(FakeProvider()))[-1]["report"]
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.assertEqual(second["tasks"][0]["review_status"], "open")


if __name__ == "__main__":
    unittest.main()
