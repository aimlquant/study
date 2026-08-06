# Machine Trading Chapter 1 presentation quality loop — 2026-08-06

## Scope and evidence

- Target: `studies/machine-trading/presentations/2026-07-25-ch01/`
- Source: `materials/quant/active/machine-trading/chapter_1.../01..._ko_explained.md`
- Baseline deck: 25 slides, revision 2026-08-05
- Baseline renders: 25 slides at 1600×900, 1366×768, and 390×844
- Render batch: `tmp/browser-shots/mt-ch1-baseline-20260806/`
- Baseline review order: Codex inspected the source, report, DOM, all three contact sheets, and selected full-size frames before reading any previous quality ledger or Claude verdict.

## Round 1 — independent Codex baseline verdict

### Gate verdicts

| Gate | Verdict | Evidence |
| --- | --- | --- |
| 1. Source structure and payload | Major defect | The DOM covers the main numbered headings, figures, tables, and boxes, but compresses the historical-data section into one slide, drops the eight-row platform comparison, omits drawdown duration and the MAR distinction, and offers no exercise bridge. Structural coordinate presence is therefore masking a thin explanatory payload. |
| 2. Semantic and numerical correctness | Major defect | Box 1.1 reverses the source notation: the source defines log-return mean `μ` and net-return mean `m`, with `μ ≈ m − s²/2`; the report and slide swap `m` and `μ`. CLS protection is stated without the eligible-trade/PvP condition. “Half Kelly” is presented as the source’s practical answer although the source instead sizes leverage against crisis-inclusive backtested drawdown. |
| 3. Independent-document completeness | Major defect | Formula slides use `M`, `C`, `mean`, and `var` without defining the estimands, units, or assumptions. The frontier and allocation results do not distinguish source claims from the AIML Quant reproduction. A reader without the report cannot reconstruct when growth, Sharpe, and Kelly allocations are proportional. |
| 4. Learning flow | Needs revision | The six-part section rhythm is clear, but it jumps from slogans to results. It needs an executable-price hierarchy, a dated-platform-snapshot caveat, a net-vs-log-return derivation, explicit optimization assumptions, and a final application checkpoint tied to selected exercises. |
| 5. Visual and projection quality | Major defect | Slide 8’s divider title occupies four oversized lines; slide 13 has the same 70 px rule but a very different two-line proportion. Slide 19’s takeaway and footer collide. Slide 14 mixes three incompatible formula/value scales. Slides 3, 24, and 25 use layouts whose markup or item count does not match the CSS grid. Several charts, tables, labels, and 12 px source notes are below projector-readable size. |
| 6. Source traceability | Needs revision | The report has coordinate attributes and passes the existing validator, but slides 19 and 20 omit the Box 1.2/1.3 coordinates that own the displayed results. The reproduced sample split and allocation numbers are not visibly labeled as AIML Quant reproduction. The convergence-figure references disagree about the random-seed protocol. |

### Cross-slide visual audit

- Section-divider siblings 4, 8, 11, 13, 17, and 21 need one shared grid, a bounded title width, and explicit density variants; changing only slides 8 and 13 would preserve the systemic defect.
- Slide 3 puts four cards into a three-column grid, leaving one card stranded on a second row.
- Slides 5, 9, 16, and 22 undersize their central figures relative to the available canvas.
- Slide 18 leaves a small table in a large empty field; slides 18 and 19 place content too close to the fixed footer.
- Slide 24’s HTML is an ordered list, while the stylesheet expects `article > span + p`, so the intended question-card design never applies.
- Mobile captures correctly letterbox the 16:9 stage, but every small-type and collision defect becomes more severe at the resulting 390 px display width.

### Source-fidelity corrections required

1. Restore `μ = E[log(1+r)]`, `m = E[r]`, and `μ ≈ m − s²/2` consistently in the report, deck, and formula annotations.
2. Replace the unsupported half-Kelly prescription with the source’s crisis-inclusive drawdown sizing; label any fractional-Kelly discussion as supplemental if retained.
3. State that CLS PvP addresses settlement risk for eligible transactions/currencies; do not imply universal coverage.
4. Separate the book’s Box 1.2/1.3 claims from the repository’s sample-split reproduction and label the latter visibly.
5. State the Gaussian/lognormal approximation, expected-input, constraint, and leverage conditions behind the growth–Sharpe–Kelly proportionality.
6. Restore the tradable-price hierarchy, dated 2017 platform snapshot, broker-protection boundaries, drawdown duration, Calmar/MAR distinction, and a selected-exercise checkpoint.

### Tooling defect found during evidence capture

Chrome 150 intermittently hung when PNG capture always supplied a virtual-time budget. The safe runner now leaves the PNG budget off by default, retains a 15 s PDF default, documents the exception, and has focused regression tests. The owner-only installed runner was refreshed and verified before completing the 75-frame batch.

### Round 1 disposition

Release is blocked. The next round must first repair the detailed report and semantic notation, then rebuild the slide sequence and shared layout rules, then rerun source-fidelity, interaction, full-render, PDF, and deployment checks.

## Round 2 — report-first repair and full-deck rebuild

The detailed report was repaired before the deck so that the presentation had an auditable
semantic source. The final deck has 31 slides and uses the revised report figures or explicitly
declared adaptations.

### Semantic and instructional repairs

- Restored the source notation: `m = E[r]`, `μ = E[log(1+r)]`, and
  `μ ≈ m − s²/2` in the report and deck.
- Removed the unsupported half-Kelly prescription. The deck now explains the source's
  crisis-inclusive drawdown sizing and identifies the assumptions behind the Kelly direction.
- Bounded CLS protection to eligible PvP transactions and separated the 2017 text from current
  official SIPC, CFTC, and CLS checks.
- Reproduced Table 1.1 in full. Table 1.2 is shown with its printed source values, while the AIML
  Quant sample-split calculation is labeled and presented separately.
- Restored drawdown duration, the Calmar/MAR distinction, the executable-price hierarchy, the
  2017 platform snapshot, the three source boxes, and all 26 exercises.
- Added an explicit source-summary section, source notes 1–8, the source glossary, and a separate
  mathematical notation table.
- Restored the source's historical evidence: Herstatt, MF Global/PFGBest, the 2015 SNB event,
  Black Monday 1987, and the 2015 All Weather example.

### Visual and interaction repairs

- Rebuilt the six section-divider siblings on one bounded title grid. The reported slide 8
  overflow and slide 13 proportion defect are both closed without one-off markup hacks.
- Generalized the shared four-card and section-density rules in the deck template, then applied
  them to the target deck.
- Rebalanced the metric, formula, result, and checkpoint slides; corrected footer clearance and
  promoted small figures and tables to projection-readable sizes.
- Redrew `fig-trading-loop.svg` on equal-width nodes with a cropped viewBox and aligned the right
  column of `fig-metric-map.svg`. The sibling SVGs were inspected at final display size.
- Localized the embedded English chart text in the efficient-frontier raster using a deterministic
  mask-and-typeset spec. The original image remains preserved; canonical Korean documents point
  to `fig-efficient-frontier-ko.png`.
- Restored report deep-fragment capture after load, kept the image lightbox keyboard-operable, and
  checked the responsive report cover and every requested section at 1440 and 390 pixels.
- Corrected print pagination so the summary callout and the estimation-risk closing paragraph are
  not orphaned. The final report is 24 A4 portrait pages.

### Publication and QA contract repairs

- Preserved the historical `index_정훈.html` instead of deleting it and declared the retention
  reason in `presentation.toml`.
- Extended site validation to require an audit record for every noncanonical HTML sibling, with
  positive and negative regression tests.
- Made source-outline extraction of bold numbered exercises an explicit opt-in to prevent false
  positives in unrelated materials.
- Hardened the guarded browser workflow: PNG capture omits a virtual-time budget by default,
  PDF uses 15 seconds, and both behavior and owner-installed-byte parity have regression tests.

## Peer review — tmux `study:4` Claude

The valid independent review was recorded as `peer-council` request
`e6fba4acb9fd4d569e8c6abe6cdc30b7`. Claude marked one gate sufficient and five insufficient on an
earlier stable snapshot and reported eleven remaining items. All eleven were resolved in Round 2:

| Claude finding | Disposition |
| --- | --- |
| Explicit source summary missing | Closed by `#source-summary` and a deck bridge. |
| Source notes 1–8 missing | Closed by `#source-notes`. |
| Source glossary replaced by a short symbol table | Closed by restoring the source terms and separating symbols. |
| Historical evidence removed | Closed by restoring the five named events next to their claims. |
| Herstatt definition and PvP boundary missing | Closed in the broker section and glossary. |
| `fig-trading-loop.svg` unequal node grid | Closed with five equal-width nodes. |
| Trading-loop viewBox wasted about half its height | Closed with a content-bounded viewBox. |
| `fig-metric-map.svg` right edge misaligned | Closed by a common right-column grid. |
| Efficient-frontier chart remained English | Closed by the inspected Korean raster derivative. |
| `index_정훈.html` was an undeclared public alternate | Closed by the retention ledger and validator contract. |
| Source Table 1.2 and reproduction values were conflated | Closed by exact source/reproduction separation. |

A final fixed-hash re-review was queued as request `959689e7dd9347cb934a276e09219495`.
The requested `study:4` window had unrelated unsubmitted user input, so the safe nudge correctly
left that input untouched; the request remains recoverable in the council inbox.

## Final render evidence

- Deck: `tmp/browser-shots/mt-ch1-final-20260806/`
  - 31 slides × 1600×900, 1366×768, and 390×844 = 93 validated PNGs.
  - Contact sheets were regenerated after the last chart-layout change.
  - All three contact sheets and the high-risk slides 8, 9, 13, 15, 18, 19, 22, 24, 29, 30,
    and 31 were visually inspected at original size.
- Report: `tmp/browser-shots/mt-ch1-report-final-20260806/`
  - Twelve deep-linked sections at 1440×1200 and 390×844.
  - Screen cover at both widths.
  - Final PDF and all-page render in `pdf-v2/` and `pdf-pages-v2/`; 24 A4 portrait pages inspected.
- Localized chart source and final pixels were inspected at 2062×783 and at slide display size.

## Final verification

Completed on the fixed target hashes recorded in the review request:

- `227` unit tests passed; `6` environment-dependent tests skipped.
- `build_site.py` reported the generated site already up to date.
- `build_site.py --check` passed.
- `validate-site.py --site html` passed for 44 HTML files; the eight warnings are the existing
  external YouTube iframe review notices.
- `git diff --check`, `xmllint` on every target SVG, the localization-skill validator, and the
  owner-installed guarded-browser readiness check passed.

Release remains pending until the final branch commit, merge, Pages completion, and live URL
smoke check are recorded.
