# Machine Trading Chapter 2 presentation quality loop — 2026-08-06

## Scope and evidence

- Target: `studies/machine-trading/presentations/2026-08-01-ch02/`
- Source: `materials/quant/active/machine-trading/chapter_2_factor_models/02_chapter_2_factor_models_ko_explained.md`
- Baseline: `origin/main` at `7585785`; 34-slide deck and its detailed report
- Baseline renders: `tmp/browser-shots/mt-ch2-baseline-20260806/`
- Review order: Codex inspected the source, baseline DOM, report, contact sheet, and selected
  full-size slides before opening a previous quality ledger or a peer verdict.

## Round 1 — independent Codex baseline verdict

### Gate verdicts

| Gate | Verdict | Evidence |
| --- | --- | --- |
| 1. Explanatory payload | Needs revision | The numbered sections are present, but the source's exact Table 2.1, Figures 2.1–2.4, summary, exercises 2.1–2.12, notes 1–11, and full glossary are absent. Several result slides consequently depend on narration rather than an auditable document. |
| 2. Semantic visual fidelity | Major defect | All four source raster figures are replaced by presenter-made abstractions or reproduction plots. The deck does not let a reader distinguish the source's backtests from AIML Quant's own reconstructions. |
| 3. Source and claim ownership | Major defect | Example 2.1's source prose reports 242% in-sample CAGR and Sharpe 3.7 with a negative OOS result, while the private reproduction script's `BOOK_RESULTS` constants and the local rerun report different values. Those three owners are not separated clearly enough. |
| 4. Beginner friendliness | Needs revision | The flow is coherent, but the reader cannot follow the exact source result, then the implementation caveat, then the reproduction boundary in one sequence. The source exercises are unavailable as a bridge from reading to practice. |
| 5. Audience-facing prose | Sufficient with visual repair | The Korean prose is generally direct and professional. Long exact source titles on section dividers wrap too aggressively, weakening projection readability. |
| 6. Render quality | Major defect | The overview puts four cards into a three-column grid, leaving a stranded fourth card. Long divider titles use one oversized rule and have inconsistent line count and visual weight. |

### Required repair set

1. Restore the exact source Table 2.1 and localized derivatives of source Figures 2.1–2.4.
2. Separate source prose, private script constants, and local reproduction values in Example 2.1.
3. Restore the source summary, exercises 2.1–2.12, notes 1–11, and all 23 source glossary entries.
4. Add a four-card layout contract and a shared bounded grid for every section divider.
5. Make report fragments restorable after page load so specific sections can be captured and audited.
6. Fix source-fidelity validation so uppercase `TABLE` and `FIGURE` labels in source Markdown are recognized.

## Round 2 — report-first repair and deck rebuild

### Source fidelity and claim ownership

- Reproduced source Table 2.1 in full and mapped it as `table:2.1`.
- Added deterministic Korean derivatives of source Figures 2.1–2.4. Editable localization specs
  live beside the four PNG outputs; the original pixels are not overwritten.
- Separated Example 2.1's source prose (242% CAGR, Sharpe 3.7, negative OOS), the private
  reproduction script's `BOOK_RESULTS` constants, and the current local reproduction.
- Labeled the malformed final residual term in the source equation as an AIML Quant correction
  instead of silently attributing the correction to the book.
- Restored the source summary, all 12 exercises, all 11 notes, and the 23-entry source glossary;
  supplemental notation is kept in a separate block.
- Made bold numbered exercise extraction opt-in through `source_exercise_style`.

### Presentation and interaction repairs

- Expanded the deck from 34 to 36 slides so each source figure has an auditable presentation
  context without crowding the existing factor explanations.
- Put all section-divider siblings on one `.section-copy` grid and applied an explicit long-title
  density variant to the affected exact source titles.
- Added a real four-column overview contract, eliminating the asymmetric three-plus-one layout.
- Kept every deck-to-report link valid and mapped every report figure marked `data-deck-use="required"`.
- Restored report fragments after load and added the opt-in `fragment-capture=1` path used by the
  guarded browser runner.
- Corrected report A4 section labels, mobile cover spacing, Korean font fallback, exercise-grid
  responsiveness, and print cover pagination.

### Validator repair

`validate-site.py` previously extracted lowercase source captions only. Chapter 2 uses uppercase
`TABLE` and `FIGURE` labels, so valid coordinates appeared unknown. Caption extraction is now
case-insensitive, with a regression test covering uppercase labels.

## Peer review — tmux `study:4` Claude

The independent Chapter 2 request is recorded as peer-council request
`cad208605e9d41b5a843b5b4c41bbc34`. The requested `study:4` Claude window contained unrelated
unsubmitted user input, so the safe nudge did not overwrite it and the request remained queued
during Round 2. A fixed-tree final review is requested before publication if that exact window
becomes available. Until its response is recorded, the peer criterion is **pending**, not
mutually sufficient; the Codex six-gate verdict below is independent.

## Final render evidence

### Deck

- Root: `tmp/browser-shots/mt-ch2-final-20260806/`
- 36 slides × 1600×900, 1366×768, and 390×844 = 108 validated PNG captures.
- Inspected all three contact sheets and full-size high-risk slides 3, 7, 10, 13–16, 18, 25,
  28, and 34.
- The four-card overview is symmetric, section titles share one grid, source figures remain
  legible and distinct, the final checklist fits, and no text or controls clip.

### Report and localized figures

- Inspected responsive report cover and section captures at 1440 and 390 pixels.
- The report's section-level `fragment-capture=1` restoration works. Ordinary direct hashes to
  inner table/figure elements did not produce valid screenshots in the safe one-shot runner and
  are not counted as evidence.
- Inspected the four localized figures together at final display size in
  `tmp/browser-shots/mt-ch2-source-figures-ko-contact.png`; month labels, legends, axes, and
  residual labels are readable with no remaining English chart text or clipping.
- Printed and inspected a 39-page A4 portrait PDF. No heading is split or orphaned; sparse pages
  13, 19, 27, and 33 are the consequence of keeping an atomic paragraph, hero callout, or figure
  intact. Pages 34–39 cleanly contain the source summary, exercises, notes, glossary, and
  references. No raw math delimiters remain.

## Independent final gate verdict

| Gate | Verdict | Closing evidence |
| --- | --- | --- |
| 1. Explanatory payload | Sufficient | Exact source results and complete study appendices are present in the report and bridged from the deck. |
| 2. Semantic visual fidelity | Sufficient | All four source figures have inspected Korean derivatives and explicit source coordinates; presenter figures remain visibly distinct. |
| 3. Source and claim ownership | Sufficient | Source prose, script constants, reproductions, and AIML Quant correction are labeled separately. |
| 4. Beginner friendliness | Sufficient | The sequence moves from definition to source evidence, failure boundary, reproduction scope, and practice checkpoint. |
| 5. Audience-facing prose | Sufficient | Exact source titles are preserved while bounded layout rules keep them readable. |
| 6. Render quality | Sufficient | 108 deck frames, responsive report captures, localized-figure contact sheet, and every A4 page were inspected at final display size. |

The Codex quality gates are sufficient. Mutual sufficiency remains pending the exact-window Claude
response and the final publication checks.
