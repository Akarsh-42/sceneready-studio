"""Run automatically in Cloud Shell after FastAPI/HTTPX are installed."""
import importlib.util
import json
import os
import unittest
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
