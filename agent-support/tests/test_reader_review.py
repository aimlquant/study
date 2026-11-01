import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('reader_validator', ROOT/'agent-support/scripts/validate-site.py')
v = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v
spec.loader.exec_module(v)


class ReaderReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root/'materials/book/chapter_01.md'
        self.source.parent.mkdir(parents=True)
        self.source.write_text('# Chapter 1\n## 1.1 First\n## 1.2 Second\n')
        self.report = self.root/'report.html'
        self.html = '<section id="intro">Introduction</section><section id="a" data-source-kind="section" data-source-ref="1.1">First</section><section id="b" data-source-kind="section" data-source-ref="1.2">Second</section>'
        self.report.write_text(self.html)
        self.trace = v.ReportDeckTraceParser()
        self.trace.feed(self.html)
        self.name = 'agent-support/reviews/test-reader-check.json'
        self.path = self.root/self.name
        self.path.parent.mkdir(parents=True)
        self.meta = dict(reader_review='full-v1', reader_review_record=self.name,
                         source_fidelity='source-structure-v1', source_material='materials/book/chapter_01.md')
        complete = dict(status='complete', remaining_blockers=0)
        self.record = dict(schema_version=1, report_sha256=hashlib.sha256(self.report.read_bytes()).hexdigest(),
                           **complete, introduction=complete.copy(),
                           sections=[dict(ref=ref, **complete) for ref in ('1.1', '1.2')])

    def check(self, write=True):
        if write:
            self.path.write_text(json.dumps(self.record))
        errors, warnings = [], []
        with patch.object(v, 'REPO_ROOT', self.root):
            v.validate_reader_review(self.meta, dict(materials_path='materials/book'), self.trace, self.report, errors, warnings)
        return errors, warnings

    def test_completed_full_read_passes(self):
        self.assertEqual(([], []), self.check())

    def test_old_session_without_flag_is_unchanged(self):
        self.meta.pop('reader_review')
        self.assertEqual(([], []), self.check(write=False))
        self.assertFalse(self.path.exists())

    def test_flag_without_record_fails_and_creates_nothing(self):
        self.assertTrue(self.check(write=False)[0])
        self.assertFalse(self.path.exists())

    def test_changed_report_rejects_stale_record(self):
        self.report.write_text(self.html+'<p>Changed prose</p>')
        self.assertIn('hash is stale', self.check()[0][0])

    def test_missing_or_extra_or_duplicate_section_fails(self):
        original = copy.deepcopy(self.record)
        for sections in [original['sections'][:1], original['sections']+[dict(ref='1.3', status='complete', remaining_blockers=0)], original['sections']+[original['sections'][0]]]:
            with self.subTest(sections=sections):
                self.record['sections'] = sections
                self.assertTrue(self.check()[0])

    def test_source_section_not_in_report_cannot_be_omitted(self):
        self.source.write_text(self.source.read_text()+'## 1.3 Third\n')
        self.assertIn('report/source section coverage differs', self.check()[0][0])

    def test_materials_absent_keeps_hash_scope_and_completion_checks(self):
        self.source.parent.rename(self.root/'book-saved')
        errors, warnings = self.check()
        self.assertEqual([], errors)
        self.assertTrue(any('materials unavailable' in x for x in warnings))
        self.record['sections'].pop()
        self.assertTrue(self.check()[0])
        self.record['report_sha256'] = '0'*64
        self.assertIn('hash is stale', self.check()[0][0])

    def test_unfinished_total_introduction_or_section_fails(self):
        for target in [self.record, self.record['introduction'], self.record['sections'][0]]:
            for key, bad in [('status', 'pending'), ('remaining_blockers', 1), ('remaining_blockers', False), ('remaining_blockers', '0'), ('remaining_blockers', -1)]:
                with self.subTest(key=key, value=bad):
                    saved = target[key]
                    target[key] = bad
                    self.assertTrue(self.check()[0])
                    target[key] = saved

    def test_empty_malformed_and_unknown_schema_fail(self):
        for record in [{}, [], {'schema_version': True}]:
            self.record = record
            self.assertTrue(self.check()[0])
        self.path.write_text('{')
        self.assertTrue(self.check(write=False)[0])

    def test_unsupported_gate_and_outside_record_fail(self):
        self.meta['reader_review'] = 'full-v2'
        self.assertTrue(self.check()[0])
        self.meta['reader_review'] = 'full-v1'
        for name in ['../outside.json', str(self.path.resolve())]:
            self.meta['reader_review_record'] = name
            self.assertTrue(self.check()[0])

    def test_record_path_symlink_cannot_escape_reviews(self):
        outside = self.root/'outside.json'
        outside.write_text(json.dumps(self.record))
        self.path.symlink_to(outside)
        self.assertTrue(self.check(write=False)[0])

    def test_new_scaffold_declares_gate_but_does_not_create_review(self):
        result = subprocess.run([sys.executable, str(ROOT/'agent-support/scripts/new-presentation.py'),
                                 '--study', 'kg-llm-in-action-2026', '--session', 'reader-gate-test',
                                 '--title', 'Test', '--date', '2026-11-01', '--presenter', 'Test',
                                 '--chapter', 'Chapter 1', '--artifacts', 'report', '--site', str(self.root/'site')],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        path = self.root/'site/studies/knowledge-graphs-and-llms-in-action/presentations/reader-gate-test/presentation.toml'
        meta = tomllib.loads(path.read_text())
        self.assertEqual('full-v1', meta['reader_review'])
        self.assertEqual('agent-support/reviews/reader-gate-test-reader-check.json', meta['reader_review_record'])
        self.assertFalse((ROOT/meta['reader_review_record']).exists())
        self.assertEqual([], list((self.root/'site').rglob('*reader-check.json')))
