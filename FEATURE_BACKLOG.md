# SceneReady feature backlog

This backlog reflects the repository as it exists. A feature is marked `shipped` only after
implementation and automated checks; deployment and live-provider validation are tracked
separately in `VALIDATION.md`.

Status: `idea` → `planned` → `in-progress` → `shipped` / `rejected`.

## Already implemented

- Four-stage workflow: breakdown → research → planning → validation.
- Gemini/ADK scene extraction and planning with bounded Parallel research.
- Deterministic citation/excerpt and scene-ID validation.
- Human task editing, assignment, notes, review state, revision comparison, JSON and Markdown export.
- Gemini PDF extraction and per-scene structured storyboard planning plus Google image generation.
- Protected paid routes, bounded request sizes/concurrency/timeouts, Cloud Run and Secret Manager.

## Tier 1 — demo readiness

### T1. Live stage progress and timers `shipped`

Sticky four-stage rail, real client-side ticking timers during streaming, animated completion
marks, and final server-measured timings. No simulated durations.

### T2. Full-report browser PDF export `shipped`

`Print / Save PDF` renders scenes, action items, evidence, questions and the run trace through
the browser print dialog. A call sheet is not claimed because the product does not yet collect
the schedule and contact data required for a trustworthy call sheet.

### T3. Browser session restore `shipped`

Completed report, brief and review edits are saved locally and restored after refresh. The
studio code and generated storyboard images are deliberately excluded. The interface labels
restored data and provides a clear button.

### T4. GitHub Actions CI `shipped`

Python tests, frontend syntax, shell/Python compilation and dependency audit on pushes and
pull requests.

### T5. Public recorded sample `planned`

Read-only `/sample` experience using an anonymized JSON export from a real live run. It must
show the recording date and must not call paid endpoints. Blocked until the team selects and
redacts a real exported report; illustrative data must not be presented as live evidence.

### T6. Mobile validation pass `planned`

Test the complete workflow, review dialog, exports and storyboard gallery on a real phone and
common responsive widths. Record the tested widths and remaining issues in `VALIDATION.md`.

## Tier 2 — differentiators

### T7. Production attention flags and evidence coverage `planned`

Use deterministic present/absent/unknown flags for night exterior, drone, minors, animals,
stunts, road control and other facts actually represented by the schema. Display department
excerpt coverage—not an authoritative risk percentage or safety verdict. Preserve negations
such as “no drone” and link every flag back to the brief evidence.

### T8. Location advisor `planned`

Provide sourced advantages, constraints and up to two candidate alternatives for the exact
location. Alternatives remain candidates—not claims of availability, approval or safety.
The query must compete transparently within the three-query research budget.

### T9. Field-aware revision and research reuse `planned`

Replace task-title comparison with actual changed fields and stable scene/task relationships.
Any research cache must include exact location, topic, date/window, relevant scene flags,
prompt/provider version, retrieval time and an expiry. Planning and human review reset after
material changes even when eligible public research is reused.

### T10. Weather and seasonal context `idea`

Use Parallel for dated, cited web research when an exterior scene and relevant date justify
it. Retrieval time is not the forecast issue time. Label old, unavailable and distant-date
information as unknown, and never displace higher-priority permit/drone/safety research
silently.

### T11. Firestore project history `idea`

Persist projects only with a clear ownership model, authentication/authorization rules,
privacy notice, retention policy and deletion path. Client-side restore covers the demo need;
Firestore is valuable only if collaborative history is demonstrated.

## Tier 3 — after the submission path is secure

- Multi-day scheduling and a genuine call-sheet data model.
- Structured Cloud Logging with run/stage IDs and durations, excluding scripts, excerpts and secrets.
- Brief templates for common production patterns.
- Stronger storyboard shot differentiation while retaining cross-frame continuity.
- Source publication-date, freshness and authority review tools.

## Rejected for the current submission

- Subjective profitability or “reward” scores.
- Invented budgets, permit fees or safety percentages.
- Automatic permit submission, payments or authority messaging.
- A second agent framework or non-permitted runtime AI provider.
- A generic chatbot that obscures the fixed, inspectable workflow.

## P0 submission gate

1. Deploy the tested commit and verify the protected live workflow from a fresh browser.
2. Complete desktop and real-phone QA, including PDF import and storyboard generation.
3. Open and manually inspect every source used in the recorded example.
4. Record the honest three-minute demo in `DEMO_PLAN.md`.
5. Verify the public repository, MIT license, README links and teammate contributions while signed out.

