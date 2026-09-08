# Three-minute SceneReady demo

## Demo story

Show one realistic preproduction decision from screenplay import to grounded crew action. The
strongest narrative is a Goa promenade scene with a drone: it creates location, aviation, date,
and ownership questions that visibly benefit from both Gemini and Parallel.

## Recording sequence

**0:00–0:20 — Problem and input**

“A short scene can trigger scattered permit, safety, and location research. SceneReady converts
that uncertainty into a reviewable production plan.” Import the original short PDF, show the
Gemini-extracted editable text, and confirm the form values are consistent:

- Production: `Skyline Take`
- Region: `Panaji, Goa, India`
- Crew: `8`
- Exact location: `D.B. Road, Panaji`
- Shoot date: `20-09-2026`

**0:20–0:55 — Live agent workflow**

Enter the studio access code off-camera, select **Build production plan**, and show the four real
stages. Say that Gemini/Google ADK performs breakdown and planning, while Python enforces order,
timeouts, and the search budget.

**0:55–1:25 — Partner integration**

Open **Run log** and show the actual Parallel queries and success statuses. Then open **Evidence**,
inspect one official source and its retrieved excerpt, and explain that Parallel receives search
queries—not the screenplay PDF.

**1:25–1:55 — Human decision layer**

Open one action's **Evidence & verification**, assign it to the location team, improve the action,
add a short review note, and mark it reviewed. State clearly: reviewed means checked by a person,
not legally cleared to film.

**1:55–2:25 — Revision awareness**

Change one material detail, rerun, and show the revision comparison plus reset review state. Use a
result already rehearsed before recording; model wording and exact task titles can vary.

**2:25–2:50 — Export and implementation**

Export the Markdown report. Briefly show `app/providers.py` and `app/workflow.py` in GitHub so judges
can see the actual Google ADK/Gemini and Parallel runtime calls plus deterministic validation.

**2:50–3:00 — Close**

“SceneReady gives production teams a faster, evidence-visible starting point while keeping humans
responsible for every real-world decision.” Show the live URL and public repository.

## Recording rules

- Keep the final video at or below three minutes and in English or with English subtitles.
- Use a successful `LIVE` run; never present offline rehearsal as provider-backed output.
- Do not display the studio code, API keys, Secret Manager values, or private browser tabs.
- If latency is edited, label the edit and preserve real timing in the Run log.
- Open and verify every source used in the final recording before filming.
- Do not claim permits, legal approval, measured accuracy, or time savings without evidence.

## Capture checklist

- Clean desktop recording at 1080p.
- Browser zoom that keeps input and output visible together.
- No personal email, billing balance, API key, or unrelated tabs visible.
- One PDF import, one live run, one Parallel evidence card, one human review, and one export.
- Final frame includes product name, live URL, repository, Google Cloud, Gemini/ADK, and Parallel.
