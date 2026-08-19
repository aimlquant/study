"""청중용 페이지가 브랜드 favicon 을 선언하는 계약을 고정한다.

`build_site.py` 가 생성하는 페이지(`page()`)는 favicon 을 항상 주입하지만,
회차 발표자료와 상세 리포트는 생성 대상이 아니라 템플릿 사본이다. 덱 템플릿에는
favicon 링크가 있었고 리포트 템플릿에는 없었으므로, 스캐폴더로 만든 리포트는
전부 favicon 없이 태어났다. 템플릿 쪽과 배포 페이지 쪽을 모두 게이트로 막는다.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPO_ROOT / "agent-support" / "scripts" / "validate-site.py"
SPEC = importlib.util.spec_from_file_location(
    "aimlquant_validate_site_favicon", VALIDATOR_PATH
)
assert SPEC and SPEC.loader
validate_site = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_site
SPEC.loader.exec_module(validate_site)

DECK_TEMPLATE = REPO_ROOT / "agent-support" / "templates" / "study-deck"
REPORT_TEMPLATE = REPO_ROOT / "agent-support" / "templates" / "study-report"
SITE = REPO_ROOT / "html"

PAGE = (
    '<!doctype html><html lang="ko"><head><title>t</title>'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    "{icon}</head><body></body></html>"
)
ICON = '<link rel="icon" href="favicon.svg" type="image/svg+xml">'


class FaviconTemplateContractTest(unittest.TestCase):
    def test_audience_templates_declare_a_favicon(self) -> None:
        for label, template in (("deck", DECK_TEMPLATE), ("report", REPORT_TEMPLATE)):
            with self.subTest(template=label):
                text = (template / "index.html").read_text(encoding="utf-8")
                self.assertRegex(text, r'<link[^>]*rel="icon"[^>]*>')


class FaviconSiteContractTest(unittest.TestCase):
    def test_every_published_page_declares_a_favicon(self) -> None:
        missing = []
        for path in sorted(SITE.rglob("*.html")):
            parser = validate_site.PageParser()
            parser.feed(path.read_text(encoding="utf-8", errors="replace"))
            if not parser.has_icon:
                missing.append(str(path.relative_to(SITE)))
        self.assertEqual(missing, [])


class FaviconValidatorGateTest(unittest.TestCase):
    def _validate(self, body: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            (site / "favicon.svg").write_text("<svg/>", encoding="utf-8")
            (site / "index.html").write_text(body, encoding="utf-8")
            errors: list[str] = []
            validate_site.validate_html(site, errors, [])
            return errors

    def test_validator_flags_a_page_without_a_favicon(self) -> None:
        errors = self._validate(PAGE.format(icon=""))
        self.assertTrue(
            any("favicon" in error for error in errors),
            f"validator did not flag the missing favicon: {errors}",
        )

    def test_validator_accepts_a_page_with_a_favicon(self) -> None:
        self.assertEqual(self._validate(PAGE.format(icon=ICON)), [])


if __name__ == "__main__":
    unittest.main()
