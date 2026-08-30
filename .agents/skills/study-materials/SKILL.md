---
name: study-materials
description: Set up a study textbook's runnable code and data, place upstream chapter sources under the matching book chapters, and build explainer-based chapter notebooks. Use when a participant mentions a new textbook, asks for 교재 코드 실행 환경, 챕터별 src 배치, 해설 노트북, data manifest, or says a chapter notebook fails verification.
---

# Study Materials

Read `AGENTS.md`, `agent-support/studies.toml`, `agent-support/procedures/study-materials.md`, and `agent-support/templates/study-materials/DESIGN.md` completely before touching study materials. They are the shared source of truth for Claude Code and Codex.

Resolve textbook paths through the registry because books move from
`materials/<track>/active/` to `materials/<track>/archive/` when completed.
Each textbook carries its own `study.toml` and `.venv`; the shared tooling
lives once in `agent-support/studykit/`. Never copy `studykit` into a
textbook folder.

Choose the notebook mode before generating anything. Use the standard
listing-reproduction flow below when book listings map to chapter source and
the goal is to execute or explain those listings. If the official companion
repository already contains a large, complete chapter corpus whose full run
requires APIs, GPUs, or large datasets, use the source-map flow described in
`agent-support/procedures/study-materials.md`: preserve the official snapshot,
link to its Jupytext source, and build small deterministic chapter guides from
a book-local manifest and harness. Do not claim that those guides reproduced
the heavy official results.

Use the CLIs rather than hand-rolling equivalents:

```bash
python3 "materials/<track>/active/<study-slug>/setup_env.py"  # 환경 구축
python3 agent-support/scripts/study-new-notebook.py "materials/<track>/active/<study-slug>" --list
python3 agent-support/scripts/study-new-notebook.py "materials/<track>/active/<study-slug>" <chXX> [--dry-run|--embed]
python3 agent-support/scripts/study-verify.py "materials/<track>/active/<study-slug>" [--lint|--no-urls|--execute]
```

Never guess the chapter-to-source mapping. Upstream repositories often keep MEAP numbering, so directory names and book chapters diverge and matching counts produces wrong placements. Confirm each mapping with distinctive keyword frequencies in the chapter's original markdown, and separate directories with no final-edition counterpart into `meap-only/`.

Treat `[mapping.listings.chXX]` in `study.toml` as authoritative for listing numbers. A single per-chapter offset cannot express a book that inserts a code-free listing mid-chapter, which shifts everything after it. Offsets differ per chapter, so never carry one chapter's value to another. Declare broken upstream listings — zero-byte or duplicated files — as `{ source = "explainer" }` and carry the explainer text instead, correcting any query that would mutate the graph.

Build notebooks only for chapters that have code in `src`. Generate the skeleton first, fill every `TODO(agent)` from the explainer, embed figures as notebook attachments, then declare `listing_coverage` for every book listing as `executed`, `substituted`, `documented-only`, or `optional` and set `status` to `complete`. Embed figures as attachments; remote `<img>` URLs and relative paths have both failed to render, and a 200 response does not prove a figure displays. Link in-repo targets with relative paths so the notebook works before anything is pushed.

Check external service requirements per chapter before promising execution. Neo4j editions and plugins can be mutually exclusive — `n10s` crashes on Enterprise while `seedUri` and `IS NODE KEY` require it — so plan container switching. Enterprise evaluation use is free, but the user must accept the licence themselves. Route OpenAI-dependent listings through the endpoint named by `[llm].env_file`, which is referenced from outside the repository so no secret is copied in, and override hard-coded model constants at runtime instead of editing upstream files.

Run the verification gate before reporting anything complete. `--lint` and the default completion gate differ; a `draft` notebook only needs lint, so without that distinction a partial notebook reports as passing.

For a book-local source-map harness, require the same completion evidence:
the chapter set and source pin match their catalogs, every notebook source
matches its generator, relative links resolve, all code cells have clean
saved outputs, and provenance hashes cover the explainer, source README,
manifest, harness, builder, and dependency lock. Refresh notebooks one at a
time through temporary files so a failure does not overwrite the last good
notebook or multiply memory use.

```bash
python3 agent-support/scripts/study-verify.py "materials/<track>/active/<study-slug>"
python3 -m unittest discover -s agent-support/tests
```

Prepare changes locally by default, and perform commits, pushes, or PR creation only when the user explicitly requests them.
