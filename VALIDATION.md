# Verification record

## Premium interface redesign (2026-09-08)

The interface now uses a cinematic studio visual system with a dark workflow console,
layered ivory workspace, stronger hierarchy, responsive navigation, clearer focus states,
reduced-motion support, and elevated task/evidence cards. All existing DOM IDs and API
behavior are preserved. Python compilation, JavaScript and shell syntax, CSS brace checks,
unique-ID checks, and JavaScript-to-HTML element checks passed in this workspace.

## PDF screenplay import implementation (2026-09-08)

SceneReady now accepts `.txt` locally or a PDF of at most 8 MiB through a protected
endpoint. The PDF path uses Gemini document understanding, treats document instructions
as untrusted data, returns plain Unicode text, and limits the editable result to 12,000
characters. SceneReady does not pass PDF bytes to Parallel.

This workspace passed Python compilation, JavaScript syntax checking, and all 18
dependency-free regression tests. Ten FastAPI tests—including five PDF access, type,
signature, size, and response tests—were discovered but skipped because FastAPI/HTTPX
are unavailable in this local verification environment. Run the complete 28-test suite
in Cloud Shell and complete one real PDF import before claiming the feature in a demo.

## Hosted workflow verification and text correction (2026-09-08)

The user completed two live Cloud Shell workflows and one deployed Cloud Run workflow.
Both scenarios completed extraction, successful Parallel searches, planning, Python
validation, review, and export. The second scenario changed location and introduced a
drone; the workflow selected both relevant searches and reset the previous review.

One model-generated question displayed a numeric HTML entity literally (`caf&#233;`).
The provider now decodes only complete numeric entities and a small allowlist of common
named entities before Pydantic validation; the browser continues escaping all rendered
text. Two regression tests cover decoding and preservation of incomplete/unknown text.

## Schema compatibility correction (2026-09-07)

The user's Cloud Shell diagnostic passed a basic Gemini request, rejected the
original Breakdown response schema with HTTP 400, and passed a simplified schema.
The provider now uses a Pydantic subclass that simplifies only the generated JSON
schema for both agents. Runtime length constraints and enum validation remain intact.
Property names (including task title), required fields, and references are preserved.

After this change: 16 local tests passed, including three schema regressions;
five API tests were skipped because FastAPI/HTTPX were unavailable here. The complete
patched ADK workflow still requires a live Cloud Shell run. This diagnostic establishes
schema compatibility as the immediate issue, not which individual constraint caused it.

## Original package checks

Completed in this workspace when preparing this package:

- 13 unit tests PASSED against local Pydantic 2.13.4: input bounds, source URL checks,
  citation matching, fabricated and whitespace-only quote rejection, unknown source
  and scene handling, mandatory bounded research, deduplication, partial research
  failure, duplicate scene rejection, explicit offline mode, and fresh review state.
- All Python source files compiled successfully.
- `node --check static/app.js` passed.
- Bash syntax checks passed for setup and deployment scripts.
- Static UI checks passed: 48 unique IDs, 3 local asset references present, and all
  42 literal JavaScript element references matched existing IDs.

Not completed here:

- 5 API tests were SKIPPED because FastAPI/HTTPX were unavailable in this workspace.
- The attempted dependency installation could not run because network approval was
  cancelled. Cloud SDK imports and agent construction could not be tested here.
- No authenticated Google or Parallel call was made from this workspace.
- No browser visual QA, Cloud Run build/deployment, or judge-access test was performed.

The version pins in requirements.txt come from the existing Cloud Shell screenshots
in this conversation, rather than an installation completed in this workspace.

The supplied `scripts/setup.sh` runs the complete current test suite in Cloud Shell after
installing the dependencies and checks the ADK agent constructors with `scripts/check.py`. After
that, run the app and inspect one real live report. A syntactically valid agent is
not evidence of a successful live model call. Keep these distinctions in the demo
and submission claims.

The earlier combined connection test shown by the user successfully used Secret
Manager, Parallel, and Gemini. That does not verify this new app end to end.
