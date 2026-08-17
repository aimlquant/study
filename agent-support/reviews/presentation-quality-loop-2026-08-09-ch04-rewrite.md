# Chapter 4 presentation quality loop — full rewrite

Date: 2026-08-09

## Observed defect

- The deployed `2026-08-08-ch04` deck had slide content in the HTML but missed the runtime control DOM (`tocButton`, `toc`, `tocItems`, `prevButton`, `nextButton`, `deckCounter`, `progress`). `assets/deck.js` failed before activating the first slide, while CSS kept slides hidden by default.
- The report preserved many source coordinates but treated them as a coverage checklist rather than a detailed learning report. Unnumbered source learning payloads, exercises, DWPC calculation details, Claude interpretation output, and clinical safety boundaries were underdeveloped.
- The SVG set reused a generic card-and-arrow grammar across distinct source figures. Several figures failed to preserve the source's actual comparison axes, path direction, metric meaning, or schema state.

## Restart decision

The rebuild restarts from the report gate, not from the slide layer. The stable public path and session id remain unchanged:

`html/studies/knowledge-graphs-and-llms-in-action/presentations/2026-08-08-ch04/`

## Changed layer

- Rebuilt `report.html` with the source section order as the primary spine.
- Replaced `assets/figs/*.svg` with semantically distinct reconstructions for Figures 4.1-4.13.
- Rebuilt `index.html` from the report and restored the deck runtime control DOM.
- Kept deployment pending for user feedback before `git push`.

## Feedback pass

- Added first-use acronym/concept notes in `report.html` for core terms such as KG, LLM, PPI, DISGeNET, WCC, Louvain, Hetionet, DWPC, CKG, UMLS, GO, GWAS, EHR, and Omics.
- Reworked Figures 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.10, and 4.13 for text containment, dark-box contrast, alignment, line routing, and clearer semantic labels.
- Expanded the DWPC explanation below Figure 4.10 to explain why high-degree hubs can weaken specificity under plain path counts.

## Source inventory focus

- Sections: 4.1, 4.2, 4.2.1, 4.2.2, 4.2.3, 4.3, 4.3.1, 4.3.2, 4.4, 4.4.1.
- Figures: 4.1-4.13, with separate visual grammars for application map, omics flow, identifier reconciliation, PPI pathway, metric distributions, Hetionet schema, DWPC calculation, CKG schema, and clinical journey.
- Tables: 4.1-4.5 preserved as source tables, plus report-only synthesis tables.
- Listings: 4.1-4.23 included as source listing anchors. DWPC Listings 4.17 and 4.18 preserve the degree extraction and `reduce(... d ^ -0.4)` calculation.
- Exercises: visible reader checkpoints restored near the relevant source flow, without adding unsupported source-fidelity coordinates.

## Verification policy

Before deployment, run the repository validation suite and perform visual QA. If the owner-only browser runner remains blocked on macOS host prerequisites, record the unverified viewport set and do not claim live visual proof.
