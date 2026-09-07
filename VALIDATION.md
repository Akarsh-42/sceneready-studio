# Verification record

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

The supplied `scripts/setup.sh` runs all 18 tests in Cloud Shell after installing the
dependencies and checks the ADK agent constructors with `scripts/check.py`. After
that, run the app and inspect one real live report. A syntactically valid agent is
not evidence of a successful live model call. Keep these distinctions in the demo
and submission claims.

The earlier combined connection test shown by the user successfully used Secret
Manager, Parallel, and Gemini. That does not verify this new app end to end.
