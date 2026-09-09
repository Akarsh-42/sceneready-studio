import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StaticFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

    def test_four_real_stage_timers_are_present(self):
        self.assertEqual(self.html.count("data-stage-time="), 4)
        for stage in ("breakdown", "research", "planning", "validation"):
            self.assertIn(f'data-stage-time="{stage}"', self.html)

    def test_full_report_print_control_and_styles_exist(self):
        self.assertIn('id="export-pdf"', self.html)
        self.assertIn('id="print-report"', self.html)
        self.assertIn("printing-full-report", self.js)
        self.assertIn("body.printing-full-report #print-report", self.css)

    def test_session_restore_excludes_secrets_and_storyboards(self):
        self.assertIn("localStorage.setItem(SESSION_KEY", self.js)
        self.assertIn("delete copy.storyboards", self.js)
        self.assertIn("access_code_was_entered:Boolean", self.js)
        self.assertNotIn("access_code:$('access-code').value", self.js)

    def test_saved_work_has_visible_clear_control(self):
        self.assertIn('id="session-banner"', self.html)
        self.assertIn('id="clear-session"', self.html)
        self.assertIn("localStorage.removeItem(SESSION_KEY)", self.js)


if __name__ == "__main__":
    unittest.main()
