"""원본 학습 좌표 추출과 report/deck 추적 계약을 검증한다."""

from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPO_ROOT / "agent-support" / "scripts" / "validate-site.py"
SPEC = importlib.util.spec_from_file_location("aimlquant_validate_site", VALIDATOR_PATH)
assert SPEC and SPEC.loader
validate_site = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_site
SPEC.loader.exec_module(validate_site)


CHAPTER_THREE_SOURCE = (
    REPO_ROOT
    / "materials/aiml/active/knowledge-graphs-and-llms-in-action"
    / "chapter_03_create_your_first_knowledge_graph_from_ontologies"
    / "03_create_your_first_knowledge_graph_from_ontologies_ko_explained.md"
)
CHAPTER_ONE_SOURCE = (
    REPO_ROOT
    / "materials/aiml/active/knowledge-graphs-and-llms-in-action"
    / "chapter_01_knowledge_graphs_and_llms_a_killer_combination"
    / "01_knowledge_graphs_and_llms_a_killer_combination_ko_explained.md"
)
CHAPTER_TWO_SOURCE = (
    REPO_ROOT
    / "materials/aiml/active/knowledge-graphs-and-llms-in-action"
    / "chapter_02_intelligent_systems_a_hybrid_approach"
    / "02_intelligent_systems_a_hybrid_approach_ko_explained.md"
)
CHAPTER_TWO_SESSION = (
    REPO_ROOT
    / "html/studies/knowledge-graphs-and-llms-in-action/presentations/2026-07-25-ch02"
)
KG_PRESENTATIONS = (
    REPO_ROOT
    / "html/studies/knowledge-graphs-and-llms-in-action/presentations"
)

SYNTHETIC_SOURCE = """\
# 정확한 장 제목

## 1.1 첫 번째 절

그림 1.1 첫 번째 그림. 공개 제목 뒤의 원문 설명입니다.

## 1.2 두 번째 절

그림 1.2 두 번째 그림.
"""

SYNTHETIC_REPORT = """\
<section class="report-section" id="source-1-1"
  data-source-kind="section" data-source-ref="1.1">
  <h2>1.1 첫 번째 절</h2>
</section>
<figure class="report-figure" id="figure-1-1" data-deck-use="required"
  data-source-kind="figure" data-source-ref="1.1">
  <figcaption>그림 1.1 첫 번째 그림.</figcaption>
</figure>
<section class="report-section" id="source-1-2"
  data-source-kind="section" data-source-ref="1.2">
  <h2>1.2 두 번째 절</h2>
</section>
<figure class="report-figure" id="figure-1-2" data-deck-use="required"
  data-source-kind="figure" data-source-ref="1.2">
  <figcaption>그림 1.2 두 번째 그림.</figcaption>
</figure>
"""

SYNTHETIC_DECK = """\
<main data-report-source="report.html">
  <section class="slide" aria-label="첫 절" data-report-refs="source-1-1 figure-1-1"
    data-source-refs="section:1.1 figure:1.1" data-source-title="section:1.1">
    <h1>1.1 첫 번째 절</h1><p>그림 1.1</p>
  </section>
  <section class="slide" aria-label="둘째 절" data-report-refs="source-1-2 figure-1-2"
    data-source-refs="section:1.2 figure:1.2" data-source-title="section:1.2">
    <h1>1.2 두 번째 절</h1><p>그림 1.2</p>
  </section>
</main>
"""

ORDERED_SOURCE = """\
# 팩터 모델 (해설판)

## 도입 — 알파와 팩터

## 1. 시계열 요인

### 예제 2.1 — 다음 날 수익 예측

## 2. 횡단면 요인

### 2-1) 적재량 읽기

## 요약
"""

ORDERED_SOURCE_WITH_NUMBERED_EXERCISES = """\
# 알고리즘 트레이딩의 기초 — 해설판

## 들어가며

## 연습문제

**1.1.** API란 무엇입니까?

**1.2.** 동일 프로그램을 쓰는 이점은 무엇입니까?

## 핵심 용어 정리
"""


class SourceFidelityTest(unittest.TestCase):
    def test_chapter_title_strips_plain_or_easy_explainer_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "chapter.md"
            source.write_text("# 시계열 분석 — 해설판\n", encoding="utf-8")
            self.assertEqual("시계열 분석", validate_site.parse_source_chapter_title(source))

            source.write_text("# 시계열 분석 — 쉬운 해설판\n", encoding="utf-8")
            self.assertEqual("시계열 분석", validate_site.parse_source_chapter_title(source))

            source.write_text("# 시계열 분석 (해설판)\n", encoding="utf-8")
            self.assertEqual("시계열 분석", validate_site.parse_source_chapter_title(source))

    def test_ordered_heading_outline_assigns_stable_chapter_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "chapter_2.md"
            source.write_text(ORDERED_SOURCE, encoding="utf-8")
            outline = validate_site.parse_source_outline(
                source, "ordered-headings-v1"
            )

        self.assertEqual(
            [
                ("section", "2.0"),
                ("section", "2.1"),
                ("example", "2.1"),
                ("section", "2.2"),
                ("section", "2.2.1"),
            ],
            list(outline),
        )
        self.assertEqual("도입 — 알파와 팩터", outline[("section", "2.0")])
        self.assertNotIn(("section", "2.3"), outline)

    def test_bold_numbered_exercises_are_opt_in_traceable_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "chapter_1.md"
            source.write_text(
                ORDERED_SOURCE_WITH_NUMBERED_EXERCISES, encoding="utf-8"
            )
            default_outline = validate_site.parse_source_outline(
                source, "ordered-headings-v1"
            )
            exercise_outline = validate_site.parse_source_outline(
                source, "ordered-headings-v1", "bold-numbered-v1"
            )

        self.assertFalse(any(kind == "exercise" for kind, _ in default_outline))
        self.assertEqual(
            [
                (("exercise", "1.1"), "연습문제 1.1"),
                (("exercise", "1.2"), "연습문제 1.2"),
            ],
            [item for item in exercise_outline.items() if item[0][0] == "exercise"],
        )

    def validate_synthetic_source_fidelity(
        self,
        *,
        deck_html: str = SYNTHETIC_DECK,
        metadata_title: str = "Chapter 1. 정확한 장 제목",
        include_materials: bool = True,
    ) -> tuple[list[str], list[str]]:
        report = validate_site.ReportDeckTraceParser()
        report.feed(SYNTHETIC_REPORT)
        deck = validate_site.ReportDeckTraceParser()
        deck.feed(deck_html)
        errors: list[str] = []
        warnings: list[str] = []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "materials/study/chapter.md"
            if include_materials:
                source_path.parent.mkdir(parents=True)
                source_path.write_text(SYNTHETIC_SOURCE, encoding="utf-8")
            with mock.patch.object(validate_site, "REPO_ROOT", root):
                validate_site.validate_source_fidelity(
                    {
                        "source_fidelity": validate_site.SOURCE_FIDELITY_VERSION,
                        "source_material": "materials/study/chapter.md",
                        "title": metadata_title,
                    },
                    {"materials_path": "materials/study"},
                    report,
                    deck,
                    root / "html/session/report.html",
                    root / "html/session/index.html",
                    errors,
                    warnings,
                )
        return errors, warnings

    @unittest.skipUnless(
        CHAPTER_ONE_SOURCE.is_file() and CHAPTER_TWO_SOURCE.is_file(),
        "교재를 함께 체크아웃한 환경에서만 Chapter 1·2 좌표를 검사한다.",
    )
    def test_chapter_one_and_two_outlines_preserve_subsections_and_listing(self) -> None:
        chapter_one = validate_site.parse_source_outline(CHAPTER_ONE_SOURCE)
        chapter_two = validate_site.parse_source_outline(CHAPTER_TWO_SOURCE)

        self.assertEqual(12, sum(kind == "section" for kind, _ in chapter_one))
        self.assertEqual(6, sum(kind == "figure" for kind, _ in chapter_one))
        self.assertEqual(12, sum(kind == "section" for kind, _ in chapter_two))
        self.assertEqual(14, sum(kind == "figure" for kind, _ in chapter_two))
        self.assertEqual(
            "추론 능력을 확인하기 위한 프롬프트",
            chapter_two[("listing", "2.1")],
        )
        self.assertEqual(
            "의료 도메인의 KG 예시.",
            chapter_one[("figure", "1.1")],
        )
        self.assertEqual(
            "전이 학습에서는, 특정 과제로 학습한 모델(또는 그 일부)을 다른 "
            "과제의 학습과 예측에 가져다 씁니다.",
            chapter_one[("figure", "1.2")],
        )
        self.assertEqual(
            "지식 그래프와 LLM: 환상의 조합",
            validate_site.parse_source_chapter_title(CHAPTER_ONE_SOURCE),
        )
        self.assertEqual(
            "지능형 시스템: 하이브리드 접근법",
            validate_site.parse_source_chapter_title(CHAPTER_TWO_SOURCE),
        )

    def test_chapter_two_deck_preserves_listing_2_1_prompt_verbatim(self) -> None:
        report_html = (CHAPTER_TWO_SESSION / "report.html").read_text(encoding="utf-8")
        deck_html = (CHAPTER_TWO_SESSION / "index.html").read_text(encoding="utf-8")
        report_match = re.search(
            r'id="source-listing-2-1".*?<code[^>]*>(.*?)</code>',
            report_html,
            re.DOTALL,
        )
        deck_match = re.search(
            r'data-source-refs="listing:2\.1".*?<code[^>]*>(.*?)</code>',
            deck_html,
            re.DOTALL,
        )

        self.assertIsNotNone(report_match)
        self.assertIsNotNone(deck_match)
        assert report_match and deck_match
        self.assertEqual(unescape(report_match.group(1)), unescape(deck_match.group(1)))

    @unittest.skipUnless(
        CHAPTER_THREE_SOURCE.is_file(),
        "교재는 aimlquant/study-materials (private) 에 있다. "
        "이 검사는 두 저장소를 함께 체크아웃한 환경에서만 실행된다.",
    )
    def test_chapter_three_outline_extracts_every_learning_coordinate(self) -> None:
        outline = validate_site.parse_source_outline(CHAPTER_THREE_SOURCE)

        counts = {
            kind: sum(1 for item_kind, _ in outline if item_kind == kind)
            for kind in validate_site.SOURCE_KINDS
        }
        self.assertEqual(11, counts["section"])
        self.assertEqual(11, counts["figure"])
        self.assertEqual(3, counts["table"])
        self.assertEqual(28, counts["listing"])
        self.assertEqual(2, counts["exercise"])
        self.assertEqual(
            "주석 수집과 처리 — TSV 파일로 그래프 완성하기",
            outline[("section", "3.3.2")],
        )
        self.assertEqual(
            "HpoDisease와 HpoPhenotype 노드 사이 관계 만들기",
            outline[("listing", "3.20")],
        )

    def test_trace_parser_collects_integrated_source_anchors_and_deck_refs(self) -> None:
        report = validate_site.ReportDeckTraceParser()
        report.feed(
            '<section class="report-section" id="source-3-1" '
            'data-source-kind="section" data-source-ref="3.1">'
            '<h1>3.1 원본 제목</h1><p>해설 본문</p></section>'
        )
        item = report.source_anchors[("section", "3.1")]
        self.assertEqual("source-3-1", item.element_id)
        self.assertIn("원본 제목", item.text)

        deck = validate_site.ReportDeckTraceParser()
        deck.feed(
            '<main data-report-source="report.html"><section class="slide" '
            'aria-label="원본 절" data-report-refs="source-3-1" '
            'data-source-refs="section:3.1">교재 §3.1</section></main>'
        )
        self.assertEqual(["section:3.1"], deck.slides[0].source_refs)
        self.assertIn("3.1", deck.slides[0].text)

    def test_deck_parser_collects_title_owner_comparison_and_code_language(self) -> None:
        deck = validate_site.ReportDeckTraceParser()
        deck.feed(
            '<main data-report-source="report.html">'
            '<section class="slide" aria-label="소절 제목" '
            'data-report-refs="source-2-1" '
            'data-source-refs="section:2.1 figure:2.1 figure:2.2" '
            'data-source-title="section:2.1" '
            'data-figure-comparison="intentional">'
            '<h1>2.1 원본 제목</h1>'
            '<pre><code class="language-cypher">MATCH (n)</code></pre>'
            '</section></main>'
        )
        slide = deck.slides[0]
        self.assertEqual("section:2.1", slide.source_title_ref)
        self.assertEqual("intentional", slide.figure_comparison)
        self.assertEqual([True], slide.code_blocks_with_language)

    def test_deck_visual_must_derive_from_report(self) -> None:
        report = validate_site.ReportDeckTraceParser()
        report.feed(
            '<figure class="report-figure" id="report-figure">'
            '<img src="assets/report.svg" alt="report"></figure>'
        )
        deck = validate_site.ReportDeckTraceParser()
        deck.feed(
            '<main data-report-source="report.html"><section class="slide" '
            'aria-label="deck only" data-report-refs="report-figure">'
            '<img src="assets/deck.svg" alt="deck"></section></main>'
        )
        errors: list[str] = []
        validate_site.validate_deck_visual_provenance(
            report, deck, Path("/tmp/session/index.html"), errors
        )
        self.assertTrue(any("deck image must first appear" in error for error in errors))

    def test_intentional_deck_visual_adaptation_names_and_links_report_figure(self) -> None:
        report = validate_site.ReportDeckTraceParser()
        report.feed(
            '<figure class="report-figure" id="report-figure">'
            '<img src="assets/report.svg" alt="report"></figure>'
        )
        deck = validate_site.ReportDeckTraceParser()
        deck.feed(
            '<main data-report-source="report.html"><section class="slide" '
            'aria-label="adapted" data-report-refs="report-figure" '
            'data-report-visual-adaptation="intentional">'
            '<a href="report.html#report-figure">source</a>'
            '<img src="assets/deck.svg" alt="deck"></section></main>'
        )
        errors: list[str] = []
        validate_site.validate_deck_visual_provenance(
            report, deck, Path("/tmp/session/index.html"), errors
        )
        self.assertEqual([], errors)

    def test_unreferenced_public_svg_requires_retention_record(self) -> None:
        report = validate_site.ReportDeckTraceParser()
        report.feed(
            '<figure class="report-figure" id="used">'
            '<img src="assets/figs/used.svg" alt="used"></figure>'
        )
        deck = validate_site.ReportDeckTraceParser()
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            figures = session / "assets/figs"
            figures.mkdir(parents=True)
            (figures / "used.svg").write_text("<svg/>", encoding="utf-8")
            (figures / "dormant.svg").write_text("<svg/>", encoding="utf-8")
            errors: list[str] = []
            validate_site.validate_retained_unreferenced_assets(
                {}, session, report, deck, errors
            )
        self.assertTrue(any("unreferenced public SVG" in error for error in errors))

    def test_retained_unreferenced_svg_needs_reason_and_must_stay_dormant(self) -> None:
        report = validate_site.ReportDeckTraceParser()
        report.feed(
            '<figure class="report-figure" id="used">'
            '<img src="assets/figs/used.svg" alt="used"></figure>'
        )
        deck = validate_site.ReportDeckTraceParser()
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            figures = session / "assets/figs"
            figures.mkdir(parents=True)
            (figures / "used.svg").write_text("<svg/>", encoding="utf-8")
            errors: list[str] = []
            validate_site.validate_retained_unreferenced_assets(
                {
                    "retained_unreferenced_assets": [
                        {"path": "assets/figs/used.svg", "reason": ""}
                    ]
                },
                session,
                report,
                deck,
                errors,
            )
        self.assertTrue(any("needs a reason" in error for error in errors))
        self.assertTrue(any("record is stale" in error for error in errors))

    def test_declared_dormant_svg_is_auditable_without_deletion(self) -> None:
        report = validate_site.ReportDeckTraceParser()
        deck = validate_site.ReportDeckTraceParser()
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            figures = session / "assets/figs"
            figures.mkdir(parents=True)
            (figures / "dormant.svg").write_text("<svg/>", encoding="utf-8")
            errors: list[str] = []
            validate_site.validate_retained_unreferenced_assets(
                {
                    "retained_unreferenced_assets": [
                        {
                            "path": "assets/figs/dormant.svg",
                            "reason": "이전 대안 도형을 명시적 폐기 결정 전까지 보존",
                        }
                    ]
                },
                session,
                report,
                deck,
                errors,
            )
        self.assertEqual([], errors)

    def test_noncanonical_public_html_requires_retention_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            (session / "index.html").write_text("canonical", encoding="utf-8")
            (session / "report.html").write_text("report", encoding="utf-8")
            (session / "index_presenter.html").write_text("draft", encoding="utf-8")
            errors: list[str] = []
            validate_site.validate_retained_alternate_html({}, session, errors)
        self.assertTrue(any("non-canonical public session HTML" in error for error in errors))

    def test_retained_alternate_html_needs_reason_and_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            errors: list[str] = []
            validate_site.validate_retained_alternate_html(
                {
                    "retained_alternate_html": [
                        {"path": "index_presenter.html", "reason": ""}
                    ]
                },
                session,
                errors,
            )
        self.assertTrue(any("needs a reason" in error for error in errors))
        self.assertTrue(any("does not exist" in error for error in errors))

    def test_declared_alternate_html_is_auditable_without_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            (session / "index_presenter.html").write_text("draft", encoding="utf-8")
            errors: list[str] = []
            validate_site.validate_retained_alternate_html(
                {
                    "retained_alternate_html": [
                        {
                            "path": "index_presenter.html",
                            "reason": "발표자 원본을 명시적 폐기 결정 전까지 보존",
                        }
                    ]
                },
                session,
                errors,
            )
        self.assertEqual([], errors)

    def test_deck_parser_flags_unlabelled_block_code(self) -> None:
        deck = validate_site.ReportDeckTraceParser()
        deck.feed(
            '<main data-report-source="report.html"><section class="slide" '
            'aria-label="코드" data-report-refs="source-2-1">'
            '<pre><code>MATCH (n)</code></pre></section></main>'
        )
        self.assertEqual([False], deck.slides[0].code_blocks_with_language)

    def test_source_fidelity_requires_exactly_one_title_owner(self) -> None:
        missing = SYNTHETIC_DECK.replace(
            ' data-source-title="section:1.1"', "", 1
        )
        errors, _ = self.validate_synthetic_source_fidelity(deck_html=missing)
        self.assertTrue(
            any("exactly one data-source-title for section:1.1" in error for error in errors)
        )

        duplicate = SYNTHETIC_DECK.replace(
            "</main>",
            '<section class="slide" aria-label="중복 첫 절" '
            'data-report-refs="source-1-1" data-source-refs="section:1.1" '
            'data-source-title="section:1.1"><h1>1.1 첫 번째 절</h1></section>'
            "</main>",
        )
        errors, _ = self.validate_synthetic_source_fidelity(deck_html=duplicate)
        self.assertTrue(
            any("exactly one data-source-title for section:1.1" in error for error in errors)
        )

    def test_source_fidelity_rejects_chapter_title_mismatch(self) -> None:
        errors, _ = self.validate_synthetic_source_fidelity(
            metadata_title="다른 장 제목"
        )
        self.assertTrue(
            any("presentation title differs from source chapter title" in error for error in errors)
        )

    def test_source_fidelity_requires_every_required_figure(self) -> None:
        deck = SYNTHETIC_DECK.replace(" figure:1.2", "", 1)
        errors, _ = self.validate_synthetic_source_fidelity(deck_html=deck)
        self.assertTrue(
            any("deck does not cover required source figure" in error for error in errors)
        )

    def test_source_fidelity_marks_multi_figure_comparisons(self) -> None:
        deck = SYNTHETIC_DECK.replace(
            'data-source-refs="section:1.1 figure:1.1"',
            'data-source-refs="section:1.1 figure:1.1 figure:1.2"',
            1,
        ).replace("<p>그림 1.1</p>", "<p>그림 1.1과 그림 1.2</p>", 1)
        errors, _ = self.validate_synthetic_source_fidelity(deck_html=deck)
        self.assertTrue(
            any("without an intentional comparison marker" in error for error in errors)
        )

    def test_source_fidelity_requires_deck_code_language(self) -> None:
        deck = SYNTHETIC_DECK.replace(
            "<p>그림 1.1</p>",
            "<p>그림 1.1</p><pre><code>MATCH (n)</code></pre>",
            1,
        )
        errors, _ = self.validate_synthetic_source_fidelity(deck_html=deck)
        self.assertTrue(
            any("deck code block lacks a language marker" in error for error in errors)
        )

    def test_source_fidelity_warns_when_materials_are_unavailable(self) -> None:
        errors, warnings = self.validate_synthetic_source_fidelity(
            include_materials=False
        )
        self.assertEqual([], errors)
        self.assertTrue(
            any("source-fidelity comparison skipped" in warning for warning in warnings)
        )

    def test_distinct_source_figures_cannot_reuse_one_image_src(self) -> None:
        report = validate_site.ReportDeckTraceParser()
        report.feed(
            '<figure class="report-figure" id="fig-3-1" '
            'data-source-kind="figure" data-source-ref="3.1">'
            '<img src="assets/shared.svg" alt="first"></figure>'
            '<figure class="report-figure" id="fig-3-2" '
            'data-source-kind="figure" data-source-ref="3.2">'
            '<img src="assets/shared.svg" alt="second"></figure>'
        )
        errors: list[str] = []
        validate_site.validate_unique_source_figure_assets(
            report, Path("/tmp/session/report.html"), errors
        )
        self.assertTrue(any("reuse the same image src" in error for error in errors))

    def test_renamed_byte_identical_source_figures_are_rejected(self) -> None:
        report = validate_site.ReportDeckTraceParser()
        report.feed(
            '<figure class="report-figure" id="fig-3-1" '
            'data-source-kind="figure" data-source-ref="3.1">'
            '<img src="assets/first.svg" alt="first"></figure>'
            '<figure class="report-figure" id="fig-3-2" '
            'data-source-kind="figure" data-source-ref="3.2">'
            '<img src="assets/second.svg" alt="second"></figure>'
        )
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            assets = session / "assets"
            assets.mkdir()
            (assets / "first.svg").write_text("<svg/>", encoding="utf-8")
            (assets / "second.svg").write_text("<svg/>", encoding="utf-8")
            errors: list[str] = []
            validate_site.validate_unique_source_figure_assets(
                report, session / "report.html", errors
            )
        self.assertTrue(any("byte-identical" in error for error in errors))

    def test_marker_ended_svg_path_requires_explicit_no_fill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            figures = session / "assets/figs"
            figures.mkdir(parents=True)
            (figures / "bad.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg">'
                '<style>.line{stroke:#000;marker-end:url(#a)}</style>'
                '<path class="line" d="M0 0H10"/></svg>',
                encoding="utf-8",
            )
            errors: list[str] = []
            validate_site.validate_svg_connector_fill_contract(session, errors)
        self.assertTrue(any("fill:none" in error for error in errors))

    def test_marker_ended_svg_path_with_no_fill_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            figures = session / "assets/figs"
            figures.mkdir(parents=True)
            (figures / "good.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg">'
                '<style>.line{fill:none;stroke:#000;marker-end:url(#a)}</style>'
                '<path class="line" d="M0 0H10"/></svg>',
                encoding="utf-8",
            )
            errors: list[str] = []
            validate_site.validate_svg_connector_fill_contract(session, errors)
        self.assertEqual([], errors)

    def test_kg_source_fidelity_reports_keep_shared_css_contracts(self) -> None:
        for session_name in (
            "2026-07-25-ch01",
            "2026-07-25-ch02",
            "2026-08-01-ch03",
        ):
            with self.subTest(session=session_name):
                errors: list[str] = []
                validate_site.validate_source_fidelity_report_css(
                    KG_PRESENTATIONS / session_name, errors
                )
                self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
