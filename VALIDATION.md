# SceneReady verification record

Last updated: **2026-09-09**

This document separates checks that were actually completed from claims that still require
human or production validation.

## Current verified state

- Cloud Run service `sceneready-studio` is deployed in `us-central1` and serves the public UI.
- A deployed revision completed live planning and storyboard generation; the new demo-readiness
  changes in this commit still require redeployment and a fresh-browser check.
- The complete local suite passed: **37 tests**.
- `scripts/check.py` passed agent constructors, model configuration, Parallel import, and API routes.
- Multiple `LIVE` workflows completed all four stages against real Gemini and Parallel services.
- A protected PDF screenplay was extracted with Gemini and used in a completed planning run.
- The app detected intentionally conflicting city, date, and crew details instead of silently
  merging them.
- Task review, ownership, notes, evidence inspection, JSON export, Markdown export, and review
  resets on rerun were exercised in the browser.
- A live scene storyboard produced two structured, visually continuous generated frames.

## Regression coverage

The test suite covers:

- brief length, crew-size, date, and URL bounds;
- source domain classification and duplicate URL removal;
- valid excerpt matching and fabricated/whitespace-only quotation removal;
- unknown source and scene-reference removal;
- mandatory bounded research and visible partial-search failures;
- duplicate scene-ID rejection and fresh review state per run;
- explicit offline mode with no automatic fallback after a live error;
- Gemini-compatible generated JSON schemas with full Pydantic runtime validation;
- safe numeric/common HTML-entity decoding while preserving unknown entities;
- protected PDF access, content type, signature, size, and response behavior;
- protected workflow routes and stable API configuration behavior.
- structured storyboard planning before image generation, bounded shot counts, partial rendering
  failures, protected access and cross-frame reference reuse;
- static contracts for four stage timers, browser restore secret exclusions, clear controls and
  full-report browser printing.

## Static and build checks

- All Python source files compile successfully.
- `node --check static/app.js` passes.
- Bash syntax checks pass for setup and deployment scripts.
- CSS braces are balanced.
- HTML IDs are unique and JavaScript element references resolve.
- Credential scanning found no committed API keys or studio access codes.
- The Dockerfile successfully built and deployed through Cloud Build.
- GitHub Actions now repeats Python tests, JavaScript and shell syntax checks, Python compilation,
  and a dependency audit on pushes and pull requests.

## Live integration evidence

Observed live runs included:

- Gemini/ADK screenplay breakdown;
- authority-focused Parallel Search queries with successful results;
- Gemini/ADK production planning;
- deterministic Python citation validation;
- source, excerpt, warning, and stage-timing display;
- completed plans in approximately 15–24 seconds during observed runs.

Timings and model outputs vary. These observations are not a latency guarantee or an accuracy score.

## Security behavior verified by implementation and tests

- Paid endpoints require a bearer studio access code when configured.
- The Cloud Run process rejects a production start with an access code shorter than 24 characters.
- Parallel and access credentials are supplied through Secret Manager.
- Request sizes, workflow concurrency, PDF concurrency, and timeouts are bounded.
- Error responses expose error type/status only—not provider bodies or user content.
- Static responses use a restrictive Content Security Policy and related security headers.

## Claims intentionally not made

- A matched quotation is not proof that advice is current, complete, or legally applicable.
- A human `Reviewed` marker is not filming clearance.
- SceneReady has not measured legal accuracy or guaranteed production time savings.
- No permit was submitted, payment made, resource booked, or authority contacted.
- Browser state is not a durable or tamper-proof audit trail.
- Restored browser data may be stale or locally modified; storyboard image data is not persisted.
- Shared studio-code access is not individual user authentication.

## Final pre-submission checks

- Run one clean, internally consistent PDF example on the deployed URL.
- Open every source shown in the recorded demo and confirm its current relevance.
- Verify missing and incorrect studio codes cannot call either protected endpoint.
- Test the final deployed revision on desktop and mobile widths.
- Exercise refresh restore, Clear saved work, and Print / Save PDF after the final deployment.
- Confirm repository visibility, license, and teammate access from a signed-out browser.
- Record a public English demo of no more than three minutes.
- Keep secrets, private scripts, and confidential production material out of the recording/repository.
