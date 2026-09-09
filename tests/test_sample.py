import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class RecordedSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample_text = (ROOT / "static" / "sample-report.json").read_text(encoding="utf-8")
        cls.sample = json.loads(cls.sample_text)
        cls.frontend = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        cls.server = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

    def test_sample_is_a_real_bounded_report(self):
        self.assertEqual(self.sample["mode"], "live")
        self.assertTrue(self.sample["sample"]["generation_disabled"])
        self.assertEqual(len(self.sample["trace"]), 4)
        self.assertGreater(len(self.sample["sources"]), 0)
        self.assertGreater(len(self.sample["tasks"]), 0)

    def test_sample_excludes_private_and_large_fields(self):
        lowered = self.sample_text.lower()
        self.assertNotIn("storyboards", self.sample)
        for forbidden in (
            "data:image/", "access_code", "access_token", "api_key",
            "hawa mahal", "badi choupad", "jaipur", "2026-10-18",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertIn("original screenplay redacted", lowered)
        self.assertIn("exact location redacted", lowered)

    def test_sample_route_is_read_only_in_the_frontend(self):
        self.assertIn('@app.get("/sample")', self.server)
        self.assertIn("SAMPLE_MODE", self.frontend)
        self.assertIn("generation_disabled", self.frontend)
        self.assertIn("if(!SAMPLE_MODE)restoreSession()", self.frontend)


if __name__ == "__main__":
    unittest.main()
