# Scene storyboards

Complete a live production plan, open **Scenes**, choose 2–4 frames, and select
**Generate Storyboard**. Each scene can generate one board per run. Frames arrive
progressively and include shot number, shot type, camera/framing, and description.
Click a frame to download it; JSON report export also includes the board and images.
Refreshing loses browser state. A new production run starts with fresh boards.

## Generation pipeline

1. Only the selected structured scene and its matched excerpt are sent to a Gemini
   text/ADK planner. The original excerpt is currently limited to 400 characters;
   long scenes may therefore have incomplete coverage.
2. Gemini returns a validated shot plan and shared visual continuity description.
   Unstated appearance choices are listed as creative assumptions.
3. Google Gemini image generation renders one image per planned shot. Each subsequent
   call receives the first successful image as a reference, the same continuity
   description, and its own distinct camera/action prompt.
4. The browser shows the plan, available frames, and explicit errors for missing frames.

The Google image model defaults to `gemini-2.5-flash-image`, in `global`. Override
`STORYBOARD_IMAGE_MODEL` and `STORYBOARD_LOCATION` in the runtime environment if needed.
The existing Gemini text model remains unchanged. Google's Imagen documentation lists
this image model as the migration target for its listed Imagen endpoints:
https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images

## Limits and deployment

The existing runtime service account and Vertex AI credentials are reused. No new
secret or database is needed. `/api/storyboard` uses the same studio access-code
protection, a 64 KiB input cap, one active board per process, and a 380-second deadline.
Offline rehearsal cannot trigger generation. There are at most four image calls per
board and no automatic application retries. Reference conditioning improves consistency
but does not guarantee identical faces or geometry. Provider filtering may omit images.
All frames are AI-generated concepts, not evidence or approved shooting instructions.

The new code passes mocked regression tests; live model access, image quality, and
deployed gallery rendering still need verification in the owner's Cloud Run project.
After deploying, run a short original scene, open Scenes, choose 2 frames, and check
the plan, continuity, image downloads, and JSON export. Check the service logs if
frames are unavailable; do not expose credentials or provider response bodies.
