"""공용 리포트·덱 템플릿의 청중용 출판 계약을 고정한다."""

from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "agent-support" / "scripts" / "new-presentation.py"
SPEC = importlib.util.spec_from_file_location("new_presentation", SCRIPT)
assert SPEC and SPEC.loader
new_presentation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(new_presentation)

DECK_TEMPLATE = REPO_ROOT / "agent-support" / "templates" / "study-deck"
REPORT_TEMPLATE = REPO_ROOT / "agent-support" / "templates" / "study-report"


class PresentationTemplateContractTest(unittest.TestCase):
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
