"""Launch in Google Cloud Shell without writing any API keys to files."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--demo", action="store_true", help="Offline UI rehearsal; no provider requests")
args = parser.parse_args()
env = os.environ.copy()
env["SCENEREADY_DEMO"] = "1" if args.demo else "0"
if not args.demo:
    project = env.get("GOOGLE_CLOUD_PROJECT") or subprocess.check_output(
        ["gcloud", "config", "get-value", "project"], text=True
    ).strip()
    if not project or project == "(unset)":
        raise SystemExit("Choose your project in Cloud Shell first.")
    env["GOOGLE_CLOUD_PROJECT"] = project
    env["GOOGLE_CLOUD_LOCATION"] = "global"
    env["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
    env.setdefault("GEMINI_MODEL", "gemini-3.8-flash")
    env["PARALLEL_API_KEY"] = subprocess.check_output(
        ["gcloud", "secrets", "versions", "access", "latest",
         "--secret=parallel-api-key", "--project=" + project], text=True
    ).strip()
    if not env["PARALLEL_API_KEY"]:
        raise SystemExit("The Parallel secret is empty.")
print("SceneReady is starting. In Cloud Shell choose Web Preview > Preview on port 8080.", flush=True)
print("Use Ctrl+C to stop. Export your report before closing the browser tab.", flush=True)
try:
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"],
        cwd=Path(__file__).resolve().parent.parent, env=env, check=True,
    )
except KeyboardInterrupt:
    pass
