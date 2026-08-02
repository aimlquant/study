---
name: study-operations
description: Publish and maintain AIML Quant sessions, GitHub Pages materials, and public YouTube links. Use when adding a study session, publishing reports or slides, connecting a public video, checking the materials-to-video lifecycle, or updating the two active study tracks in aimlquant.
---

# Study Operations

Maintain the public study hub around a stable session URL. Publish materials
first, then add the YouTube connection only after the video is public.

## Load the sources of truth

Before editing, read:

1. `AGENTS.md`
2. `agent-support/site.toml`
3. `agent-support/studies.toml`
4. `agent-support/sessions.toml`
5. `agent-support/procedures/study-lifecycle.md`

Treat `agent-support/sessions.toml` as the public session registry. Keep private
upload state in the separate private `ai-odyssey` operations repository.

## Choose the lifecycle transition

- New schedule: add a globally unique `session_id` with status `scheduled`,
  plus its date, chapters, presenters, and the public `meeting_url` when the
  Webex join URL is confirmed. Do not use `#` or invent a placeholder URL.
- Meeting ended: remove the join URL and set `meeting_status = "ended"` so
  member-facing schedules do not advertise a stale Webex button.
- Materials ready: copy public artifacts under
  `html/studies/<study-slug>/presentations/<session-slug>/`, register each
  artifact, then set status to `materials-published`.
- Video public: verify the YouTube visibility is actually `public`, add the
  11-character `youtube_video_id`, then set status to `video-public`.
- Cancelled: set status to `cancelled` and do not store a video ID.

Never store a private or unlisted video ID, OAuth credential, cookie, local
recording path, subtitle work file, or upload recovery ledger in this public
repository.

## Preserve the reciprocal links

Use this stable URL in the YouTube description:

`https://restful3.github.io/aimlquant/sessions/<session_id>/`

Do not rename an already published session ID. The site builder creates the
reverse YouTube link and embed when the public video ID is present.

For an artifact page that can be edited, include a visible link back to its
session hub. This keeps navigation intact even when someone opens slides or a
report directly.

## Build and verify

Run:

```bash
uv run --with 'nbformat>=5,<6' python -m unittest discover -s agent-support/tests -v
python3 agent-support/scripts/build_site.py
python3 agent-support/scripts/build_site.py --check
python3 agent-support/scripts/validate-site.py --site html --check-materials
git diff --check
```

If HTML or CSS changed, render desktop and mobile pages at their final display
sizes. Inspect text wrapping, clipping, card alignment, gaps, artifact links,
the pending-video state, and the 16:9 video frame.

Before publishing, verify that no non-public upload metadata or secret entered
the diff.
