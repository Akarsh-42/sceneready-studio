"""Run automatically in Cloud Shell after FastAPI/HTTPX are installed."""
import importlib.util
import json
import os
import unittest
from unittest.mock import AsyncMock, patch

AVAILABLE = all(importlib.util.find_spec(name) for name in ("fastapi", "httpx"))
if AVAILABLE:
    from fastapi.testclient import TestClient
    from app.main import app


@unittest.skipUnless(AVAILABLE, "FastAPI/HTTPX unavailable in this verification environment")
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {
            "SCENEREADY_DEMO": "1", "STUDIO_ACCESS_TOKEN": "test-only-code-with-at-least-24-characters",
        })
        self.environment.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.headers = {"Authorization": "Bearer test-only-code-with-at-least-24-characters"}
        self.brief = {"title": "Test", "city": "Mumbai", "script": "Two adult actors walk along a street with a small film crew."}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.environment.stop()

    def test_access_code_required(self):
        response = self.client.post("/api/run", json=self.brief)
        self.assertEqual(response.status_code, 401)

    def test_oversized_body_is_rejected(self):
        response = self.client.post("/api/run", content=b"x" * 65537, headers=self.headers)
        self.assertEqual(response.status_code, 413)

    def test_invalid_brief_is_rejected(self):
        response = self.client.post("/api/run", json={"title": "Test"}, headers=self.headers)
        self.assertEqual(response.status_code, 422)

    def test_complete_streamed_demo(self):
        response = self.client.post("/api/run", json=self.brief, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        events = [json.loads(line) for line in response.text.splitlines()]
        self.assertEqual(events[-1]["type"], "result")
        self.assertEqual(events[-1]["report"]["mode"], "offline_rehearsal")
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_configuration_does_not_leak_secrets(self):
        response = self.client.get("/api/config")
        self.assertTrue(response.json()["access_required"])
        self.assertNotIn("test-only-code", response.text)

    def test_pdf_import_requires_access_code(self):
        response = self.client.post(
            "/api/extract-document", content=b"%PDF-1.7 sample", headers={"Content-Type": "application/pdf"},
        )
        self.assertEqual(response.status_code, 401)

    def test_oversized_pdf_is_rejected(self):
        response = self.client.post(
            "/api/extract-document", content=b"%PDF-" + b"x" * (8 * 1024 * 1024),
            headers={**self.headers, "Content-Type": "application/pdf"},
        )
        self.assertEqual(response.status_code, 413)

    def test_pdf_import_rejects_wrong_media_type(self):
        response = self.client.post(
            "/api/extract-document", content=b"%PDF-1.7 sample",
            headers={**self.headers, "Content-Type": "text/plain"},
        )
        self.assertEqual(response.status_code, 415)

    def test_pdf_import_rejects_invalid_signature(self):
        response = self.client.post(
            "/api/extract-document", content=b"not really a PDF",
            headers={**self.headers, "Content-Type": "application/pdf"},
        )
        self.assertEqual(response.status_code, 400)

    def test_pdf_import_returns_bounded_text(self):
        extracted = "EXT. STREET — DAY\n\nTwo actors cross a quiet street."
        environment = patch.dict(os.environ, {
            "SCENEREADY_DEMO": "0", "GOOGLE_CLOUD_PROJECT": "test-project",
        })
        provider = patch("app.main.LiveProvider.extract_pdf", new=AsyncMock(return_value=(extracted, False)))
        with environment, provider:
            response = self.client.post(
                "/api/extract-document", content=b"%PDF-1.7 sample",
                headers={**self.headers, "Content-Type": "application/pdf"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], extracted)
        self.assertFalse(response.json()["truncated"])


if __name__ == "__main__":
    unittest.main()
