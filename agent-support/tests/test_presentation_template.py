"""공용 리포트·덱 템플릿의 청중용 출판 계약을 고정한다."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from html.parser import HTMLParser
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "agent-support" / "scripts" / "new-presentation.py"
SPEC = importlib.util.spec_from_file_location("new_presentation", SCRIPT)
assert SPEC and SPEC.loader
new_presentation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(new_presentation)

DECK_TEMPLATE = REPO_ROOT / "agent-support" / "templates" / "study-deck"
REPORT_TEMPLATE = REPO_ROOT / "agent-support" / "templates" / "study-report"


class TemplateDOM(HTMLParser):
    """Small DOM for checking relationships, not whitespace or source line counts."""

    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
                 "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, source: str) -> None:
        super().__init__()
        self.root = Element("document")
        self.stack = [self.root]
        self.feed(source)

    def handle_starttag(self, tag, attrs) -> None:
        node = SubElement(self.stack[-1], tag, {k: v or "" for k, v in attrs})
        if tag not in self.VOID_TAGS:
            self.stack.append(node)

    def handle_endtag(self, tag) -> None:
        if self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_data(self, data) -> None:
        node = self.stack[-1]
        node.text = (node.text or "") + data


def with_class(nodes, name):
    return [node for node in nodes if name in node.get("class", "").split()]


class PresentationTemplateContractTest(unittest.TestCase):
    def test_paired_scaffold_preserves_every_slide_shell_and_report_target(self) -> None:
        """A valid scaffold must not silently lose the presentation's common frame."""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT),
                 "--study", "kg-llm-in-action-2026",
                 "--session", "test-deck-format", "--title", "템플릿 형식 검증",
                 "--date", "2026-09-10", "--presenter", "테스트 발표자",
                 "--chapter", "Chapter 3", "--site", directory],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            target = Path(directory) / "studies/knowledge-graphs-and-llms-in-action/presentations/test-deck-format"
            source = (target / "index.html").read_text()
            self.assertNotRegex(source, new_presentation.TOKEN_RE)
            deck = TemplateDOM(source).root
            report = TemplateDOM((target / "report.html").read_text()).root
            report_ids = {node.get("id") for node in report.iter() if node.get("id")}
            report_images = {node.get("src") for node in report.iter("img")}
            main = deck.find(".//main[@id='deck']")
            self.assertIsNotNone(main)
            self.assertEqual(main.get("data-report-source"), "report.html")
            self.assertEqual(main.get("data-caption-scope"), "deck")
            slides = with_class(main, "slide")
            self.assertGreater(len(slides), 1)
            slide_ids = [slide.get("id") for slide in slides]
            self.assertTrue(all(slide_ids))
            self.assertEqual(len(slide_ids), len(set(slide_ids)))
            self.assertEqual(len({slide.get("aria-label") for slide in slides}), len(slides))
            self.assertEqual(len(with_class(slides, "slide--cover")), 1)
            for slide in slides:
                with self.subTest(slide=slide.get("id")):
                    self.assertTrue(slide.get("aria-label"))
                    refs = set(slide.get("data-report-refs", "").split())
                    self.assertTrue(refs)
                    self.assertLessEqual(refs, report_ids)
                    if "slide--cover" in slide.get("class", "").split():
                        self.assertIsNotNone(slide.find(".//h1"))
                        self.assertEqual(len(with_class(slide, "cover-meta")), 1)
                        continue
                    self.assertIn("slide--teaching", slide.get("class", "").split())
                    children = list(slide)
                    self.assertEqual([node.tag for node in children],
                                     ["header", "h1", "p", "div", "p", "footer"])
                    for index, name in [(0, "slide-header"), (2, "lead"),
                                        (3, "slide-body"), (4, "takeaway"), (5, "slide-footer")]:
                        self.assertIn(name, children[index].get("class", "").split())
                    for name in ("brand-name", "section-tag"):
                        labels = with_class(children[0], name)
                        self.assertEqual(len(labels), 1)
                        self.assertTrue("".join(labels[0].itertext()).strip())
                    footer = children[-1]
                    for attr in ("data-slide-number", "data-slide-total"):
                        self.assertEqual(len([node for node in footer.iter() if attr in node.attrib]), 1)
                    links = with_class(footer.iter("a"), "report-ref")
                    self.assertEqual(len(links), 1)
                    href = links[0].get("href", "")
                    self.assertTrue(href.startswith("report.html#"))
                    self.assertIn(href.split("#", 1)[1], refs)
            for image in deck.iter("img"):
                self.assertIn(image.get("src"), report_images)
                self.assertTrue(image.get("alt"))
            for node in deck.iter():
                asset = node.get("src", "")
                if asset.startswith("assets/"):
                    self.assertTrue((target / asset).is_file(), asset)
            # Cover the reusable layout families without fixing a talk's slide count.
            for name in ("teaching-rows", "teaching-columns", "teaching-visual",
                         "teaching-wide-visual", "teaching-table", "formula-main"):
                self.assertTrue(with_class(main.iter(), name), name)
            self.assertIsNotNone(main.find(".//pre[@data-code-language]"))

    def test_report_only_scaffold_enables_report_gates_without_a_deck(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT),
                 "--study", "machine-learning-for-trading-3e-2026",
                 "--session", "test-report-only", "--title", "시험 리포트",
                 "--date", "2026-09-12", "--presenter", "태영",
                 "--chapter", "Chapter 1", "--artifacts", "report",
                 "--source-material", "materials/quant/active/example/ch01.md",
                 "--site", directory],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            target = Path(directory) / "studies/machine-learning-for-trading-3e/presentations/test-report-only"
            metadata = tomllib.loads((target / "presentation.toml").read_text())
            self.assertEqual(metadata["artifacts"], ["report"])
            self.assertEqual(metadata["source_fidelity"], "source-structure-v1")
            self.assertEqual(metadata["report_quality"], "source-learning-v1")
            self.assertEqual(metadata["source_material"], "materials/quant/active/example/ch01.md")
            self.assertFalse((target / "index.html").exists())
            self.assertFalse((target / "assets/deck.js").exists())
            self.assertTrue((target / "assets/report.js").is_file())
            self.assertNotIn('<a href="./">Slides</a>', (target / "report.html").read_text())
            self.assertNotIn("derive index.html", result.stdout)

    def test_current_templates_pass_the_scaffolder_contract(self) -> None:
        new_presentation.validate_template_sources(DECK_TEMPLATE, REPORT_TEMPLATE)

    def test_deck_runtime_numbers_the_active_mode_before_lightbox_setup(self) -> None:
        deck_html = (DECK_TEMPLATE / "index.html").read_text(encoding="utf-8")
        deck_js = (DECK_TEMPLATE / "assets" / "deck.js").read_text(encoding="utf-8")
        lightbox_js = (DECK_TEMPLATE / "assets" / "deck-lightbox.js").read_text(
            encoding="utf-8"
        )

        self.assertLess(
            deck_html.index('src="assets/deck.js"'),
            deck_html.index('src="assets/deck-lightbox.js"'),
        )
        self.assertIn("slide.dataset.deckAppendix", deck_js)
        self.assertIn("function numberFigures()", deck_js)
        self.assertIn("figure.dataset.deckFigureNumber", deck_js)
        self.assertIn("figure?.dataset.deckFigureNumber", lightbox_js)

    def test_audience_templates_do_not_restore_authoring_boilerplate(self) -> None:
        audience_html = "\n".join(
            (
                (DECK_TEMPLATE / "index.html").read_text(encoding="utf-8"),
                (REPORT_TEMPLATE / "index.html").read_text(encoding="utf-8"),
            )
        )
        for phrase in new_presentation.AUDIENCE_TEMPLATE_BANNED:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, audience_html)

    def test_scaffolder_rejects_lightbox_before_dynamic_numbering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deck = root / "deck"
            report = root / "report"
            shutil.copytree(DECK_TEMPLATE, deck)
            shutil.copytree(REPORT_TEMPLATE, report)
            deck_html_path = deck / "index.html"
            deck_html = deck_html_path.read_text(encoding="utf-8")
            first = '  <script src="assets/deck.js"></script>\n'
            second = '  <script src="assets/deck-lightbox.js"></script>\n'
            deck_html_path.write_text(
                deck_html.replace(first + second, second + first), encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "deck.js must run before"):
                new_presentation.validate_template_sources(deck, report)

    def test_default_projector_type_is_not_the_old_small_scale(self) -> None:
        deck_css = (DECK_TEMPLATE / "assets" / "deck.css").read_text(encoding="utf-8")
        self.assertIn("font-size: 21px;", deck_css)
        self.assertIn("font-size: 18px;", deck_css)
        self.assertIn(".slide.is-deck-omitted", deck_css)
        self.assertIn(".slide--figure-table", deck_css)

    def test_guarded_mobile_capture_can_request_the_exact_layout_width(self) -> None:
        deck_js = (DECK_TEMPLATE / "assets" / "deck.js").read_text(encoding="utf-8")
        report_js = (REPORT_TEMPLATE / "assets" / "report.js").read_text(
            encoding="utf-8"
        )
        deck_css = (DECK_TEMPLATE / "assets" / "deck.css").read_text(encoding="utf-8")
        report_css = (REPORT_TEMPLATE / "assets" / "report.css").read_text(
            encoding="utf-8"
        )

        for runtime in (deck_js, report_js):
            self.assertIn("qa-width", runtime)
            self.assertIn("qaViewportWidth", runtime)
            self.assertIn("--qa-viewport-width", runtime)
        for stylesheet in (deck_css, report_css):
            self.assertIn("html[data-qa-viewport-width]", stylesheet)
            self.assertIn("var(--qa-viewport-width)", stylesheet)


if __name__ == "__main__":
    unittest.main()
