import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/report-paragraphs.py"
spec = importlib.util.spec_from_file_location("report_paragraphs", SCRIPT)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class ReportParagraphTests(unittest.TestCase):
    def test_semantic_units_and_exclusions(self):
        source = r'''<nav><p>navigation text</p></nav>
        <section class="report-cover"><p>cover text</p></section>
        <section class="report-section" data-source-ref="9.1" id="s91">
        <p id="a">앞 <strong>강조</strong>와 <code>x</code>를<br>설명합니다.</p>
        <figure><p>figure text</p></figure><table><tr><td><p>table text</p></td></tr></table>
        <pre><code>code text</code></pre><p>\[x=1\]</p>
        <p>계산은 \(x=1\)처럼 표시합니다.</p><p hidden>hidden text</p>
        <div aria-hidden="true"><p>hidden child</p></div>
        <ul><li>바깥<ul><li>안쪽 항목</li></ul></li></ul>
        <aside class="verification-note"><p>검증 기록 문단</p></aside></section>'''
        items = p.extract_paragraphs(source, 1)
        self.assertEqual([x["text"] for x in items], [
            "앞 강조와 x를 설명합니다.", r"계산은 \(x=1\)처럼 표시합니다.", "안쪽 항목", "검증 기록 문단"])
        self.assertEqual([x["kind"] for x in items], ["body", "body", "body", "note"])
        self.assertEqual({x["section"] for x in items}, {"9.1"})
        self.assertEqual(items[0]["id"], "a")

    def test_character_count_and_document_order(self):
        source = '<section class="report-section" id="summary"><p>가 나</p><p>두 번째 문단</p></section>'
        items = p.extract_paragraphs(source, 4)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["section"], "summary")
        self.assertEqual(items[0]["number"], 1)

    def test_sample_is_reproducible_stratified_and_excludes_notes(self):
        items = [{"number": i, "section": str(i // 10), "kind": "body"} for i in range(1, 40)]
        items.append({"number": 40, "section": "note-only", "kind": "note"})
        a = p.cross_sample(items, 12, 16341)
        self.assertEqual(a, p.cross_sample(items, 12, 16341))
        self.assertNotEqual(a, p.cross_sample(items, 12, 16342))
        self.assertEqual(len(a), 12)
        self.assertEqual({x["section"] for x in items if x["number"] in a}, {"0", "1", "2", "3"})
        self.assertNotIn(40, a)

    def test_short_sample_and_invalid_requests(self):
        items = [{"number": i, "section": str(i), "kind": "body"} for i in range(1, 4)]
        self.assertEqual(p.cross_sample(items, 30, 1), [1, 2, 3])
        self.assertEqual(p.cross_sample(items, 0, None), [])
        for count, seed in [(2, 1), (1, None), (-1, 1)]:
            with self.assertRaises(ValueError):
                p.cross_sample(items, count, seed)

    def test_cli_hash_scope_no_approval_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.html"
            report.write_text('<section class="report-section" data-source-ref="9.1"><p>첫 절입니다.</p></section>'
                              '<section class="report-section" data-source-ref="9.2"><p>다음 절입니다.</p></section>')
            raw = report.read_bytes()
            args = [sys.executable, str(SCRIPT), str(report), "--min-chars", "1", "--seed", "7", "--sections", "9.2"]
            result = subprocess.run(args, check=True, capture_output=True, text=True)
            data = json.loads(result.stdout)
            self.assertEqual(data["sample_numbers"], [2])
            self.assertEqual(data["report_sha256"], p.hashlib.sha256(raw).hexdigest())
            self.assertFalse({"status", "verdict", "remaining_blockers"} & data.keys())
            self.assertEqual(report.read_bytes(), raw)
            for extra in [["--output", str(report)], ["--sections", "9.3"]]:
                self.assertNotEqual(subprocess.run(args + extra, capture_output=True).returncode, 0)
            self.assertEqual(report.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
