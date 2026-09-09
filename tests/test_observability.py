import json
import unittest

from app.observability import log_event


class ObservabilityTests(unittest.TestCase):
    def test_event_is_machine_readable_and_keeps_approved_metadata(self):
        with self.assertLogs("sceneready.events", level="INFO") as captured:
            log_event(
                "stage_completed",
                run_id="abc123",
                stage="research",
                seconds=1.25,
                source_count=3,
            )
        payload = json.loads(captured.records[0].getMessage())
        self.assertEqual(payload["event"], "stage_completed")
        self.assertEqual(payload["run_id"], "abc123")
        self.assertEqual(payload["stage"], "research")
        self.assertEqual(payload["source_count"], 3)

    def test_sensitive_or_unapproved_fields_are_dropped(self):
        with self.assertLogs("sceneready.events", level="WARNING") as captured:
            log_event(
                "run_failed",
                severity="warning",
                run_id="abc123",
                error_type="RuntimeError",
                access_code="never-log-this",
                script="EXT. PRIVATE LOCATION",
                query="private location permit",
                provider_body="credential details",
            )
        payload = json.loads(captured.records[0].getMessage())
        self.assertEqual(payload["error_type"], "RuntimeError")
        self.assertNotIn("access_code", payload)
        self.assertNotIn("script", payload)
        self.assertNotIn("query", payload)
        self.assertNotIn("provider_body", payload)


if __name__ == "__main__":
    unittest.main()
