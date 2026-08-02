---
name: study-presentation
description: Create, revise, review, and prepare paired long-form HTML reports and browser slide decks for AIML Quant sessions. Use when a participant mentions an assigned study date or chapter, asks for a report, slides, 발표자료, or a session package for GitHub Pages.
---

# Study Presentation

Read `AGENTS.md`, `agent-support/studies.toml`, and `agent-support/procedures/study-presentation.md` completely before editing. For a new session also read `agent-support/templates/STUDY_SESSION_BLUEPRINT.md` and both template `DESIGN.md` files, then scaffold with `agent-support/scripts/new-presentation.py`. The registry resolves active/archive material paths; the public `html/studies/<study-slug>` path never follows that move. Create the paired report and deck unless the user asks for one artifact, and never overwrite an existing session with the scaffolder.

## Checkpoint 1 — source inventory

Audit the raw explainer before authoring. Record every chapter/section, figure, table, listing, example, box, and exercise in source order with its exact translated title, claim owner and strength, conditions, dated demonstrations, examples, and visual relationships. Copyright-safe paraphrase may change prose and artwork, not navigational coordinates or meaning. Link private material through `../../../../materials/?p=...`; keep the registry-relative path in `source_material`.

## Checkpoint 2 — integrated report

Finish `report.html` before writing session-specific slides. Rebuild the body on the source outline; put every coordinate at its real explanatory position with a stable `id`, `data-source-kind`, and `data-source-ref`. A mapping table is not a substitute. Keep AIML Quant synthesis visibly outside the source numbering namespace. Preserve conditional claims, precise attribution, and comparison levels; define specialist terms at first use. Use the report's own explanatory voice, with source notes adjacent to source-dependent claims and reconstruction scope.

Give each source figure coordinate a semantically distinct asset. Repeated mental models must visibly preserve changed state; process and result figures need different visual grammar. Never alias one `src` or byte-identical copies under different captions. Label source visuals `그림 N`, not `교재 그림 N`. Mark visuals the deck must carry with `data-deck-use="required"`. The report gate includes complete structure and argument coverage, captions/sources, TOC/lightbox, desktop/mobile render, and inspected A4 PDF. Only then set `source_fidelity = "source-structure-v1"` and `source_material`.

## Checkpoint 3 — report-derived deck

Derive every deck claim, term, table, and visual from the approved report; update the report first if a slide needs new evidence. Keep `data-report-source="report.html"`, valid `data-report-refs`, visible source coordinates, and `data-source-refs`. Assign each source section title to exactly one slide with `data-source-title="section:N.N"`; that slide must show the explainer's exact translated title and also reference the same section. Later slides within the section may use conclusion-style titles.

Use one substantive source figure per slide by default. Keep its exact source coordinate and caption title (the first complete sentence) visible; rewrite later explanatory caption sentences as independent teaching prose instead of copying them into the title. Multiple `figure:` refs require a real simultaneous comparison, final-size legibility, and `data-figure-comparison="intentional"`. Explain how to read a visual, why it matters, and its interpretation/failure boundary in at most three short points; split overflow instead of truncating the title or making type unreadable. All deck images need click/keyboard fullscreen zoom. Every block code sample needs a language marker on `<pre>` or its direct `<code>` and visible code-window chrome.

## Checkpoint 4 — independent publication

Remove prompts, scaffold/blueprint language, pipeline diagrams, compliance claims, and statements about following source order from audience-facing artifacts. Covers, overviews, TOC text, summaries, and takeaways must teach the subject itself. Re-audit the paired report and every slide after either changes so conditions, attribution, IDs, visible labels, and trace metadata cannot drift.

## Checkpoint 5 — migration and completion

Before replacing or deleting an existing artifact, inventory official, retained, and duplicate outputs plus all public links. When the user explicitly retires a derivative, preserve the immutable session ID/page URL, recover or deliberately discard any unique useful assets, remove artifact directories and registry links together, rebuild generated pages, and check broken links. Never infer permission to delete an unregistered sibling artifact.

Run the repository's complete required verification, render the deck at 1600×900 and 1366×768 plus 390px mobile, and inspect the report at desktop/mobile/A4. Source-fidelity decks may exceed the normal 18–30-slide guideline when one-figure-per-slide and complete learning-coordinate coverage require it. Use peer review for semantic visual fidelity, claim ownership, beginner friendliness, and audience-facing prose; string checks do not decide those qualities.

At minimum, after creating or editing a report or deck, run:

```bash
python3 agent-support/scripts/build_site.py
python3 agent-support/scripts/build_site.py --check
python3 agent-support/scripts/validate-site.py --site html
```

Inspect actual pixels; DOM and CSS declarations alone do not prove legibility. Preserve user changes. Commit, push, PR, or change Pages only when the user requested that scope.
