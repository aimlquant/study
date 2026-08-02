"""원본 학습 좌표 추출과 report/deck 추적 계약을 검증한다."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


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


class SourceFidelityTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
