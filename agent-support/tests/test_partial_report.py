import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('partial_v',ROOT/'agent-support/scripts/validate-site.py');v=importlib.util.module_from_spec(spec);sys.modules[spec.name]=v;spec.loader.exec_module(v)

class PartialReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        p=self.root/'materials/book/ch.md';p.parent.mkdir(parents=True);p.write_text('# 제목\n## 1.1 첫절\n그림 9.8: 첫그림\n\n### 박스 1.1: 상자설명\n\n## 1.2 다음절\n표 1.1: 다음표\n')
        self.source=p;self.report=self.root/'report.html'
        self.html='<p id="report-scope-notice">1.1까지 · 이후 작성 중</p><section id="intro">도입</section><section id="s1" data-source-kind="section" data-source-ref="1.1">첫절</section><figure id="f" data-source-kind="figure" data-source-ref="9.8">첫그림</figure><div id="b" data-source-kind="box" data-source-ref="1.1">상자설명</div>'
        self.meta=dict(source_fidelity='source-structure-v1',source_material='materials/book/ch.md',title='제목',report_scope=dict(version='sections-v1',sections=['1.1'],include_intro=True))
    def check(self):
        self.report.write_text(self.html);trace=v.ReportDeckTraceParser();trace.feed(self.html);errors=[]
        with patch.object(v,'REPO_ROOT',self.root):v.validate_source_fidelity(self.meta,{'materials_path':'materials/book'},trace,None,self.report,self.root/'index.html',errors,[])
        return errors
    def test_partial_scope_owns_coordinates_by_position_not_number(self):self.assertEqual([],self.check())
    def test_missing_in_scope_figure_fails(self):
        self.html=self.html.replace('<figure id="f" data-source-kind="figure" data-source-ref="9.8">첫그림</figure>','');self.assertTrue(any('missing coordinate' in e for e in self.check()))
    def test_out_of_scope_coordinate_fails(self):
        self.html+='<table id="t" data-source-kind="table" data-source-ref="1.1">다음표</table>';self.assertTrue(any('unknown coordinate' in e for e in self.check()))
    def test_unknown_section_fails(self):
        self.meta['report_scope']['sections']=['9.9'];self.assertTrue(self.check())
    def test_empty_or_duplicate_scope_fails(self):
        for refs in [[],['1.1','1.1']]:
            self.meta['report_scope']['sections']=refs;self.assertTrue(any('invalid report_scope' in e for e in self.check()))
    def test_without_scope_full_chapter_still_required(self):
        self.meta.pop('report_scope');self.assertTrue(any('missing coordinate' in e for e in self.check()))
    def test_scope_and_notice_checked_without_materials(self):
        self.source.parent.rename(self.root/'saved');self.assertEqual([],self.check())
        self.html=self.html.replace('report-scope-notice','removed-notice');self.assertTrue(any('notice' in e for e in self.check()))
    def test_review_scope_must_match(self):
        self.report.write_text(self.html);trace=v.ReportDeckTraceParser();trace.feed(self.html)
        name='agent-support/reviews/content.json';p=self.root/name;p.parent.mkdir(parents=True);p.write_text(json.dumps(dict(schema_version=1,report_sha256=hashlib.sha256(self.report.read_bytes()).hexdigest(),scope={})))
        self.meta.update(report_quality='source-learning-v1',content_review=name);errors=[]
        with patch.object(v,'REPO_ROOT',self.root):v.validate_content_review(self.meta,{'materials_path':'materials/book'},trace,self.report,errors,[])
        self.assertTrue(any('scope differs' in e for e in errors))

class NewGateDefaultsTests(unittest.TestCase):
    def scaffold(self,extra):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
        result=subprocess.run([sys.executable,str(ROOT/'agent-support/scripts/new-presentation.py'),'--study','kg-llm-in-action-2026','--session','test-new-defaults','--title','테스트','--date','2026-11-01','--presenter','테스트','--chapter','Chapter 1','--site',str(root),*extra],capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        target=root/'studies/knowledge-graphs-and-llms-in-action/presentations/test-new-defaults'
        import tomllib
        return target,tomllib.loads((target/'presentation.toml').read_text())
    def test_defaults_make_portable_empty_inventory(self):
        target,meta=self.scaffold([]);self.assertEqual('rich-v1',meta['figure_density']);self.assertEqual('visual-math-v1',meta['source_completeness']);self.assertEqual('source-inventory.json',meta['source_inventory'])
        self.assertEqual({'version':1,'scope':[],'sources':[]},json.loads((target/'source-inventory.json').read_text()))
        self.assertEqual([],list(target.parents[3].glob('agent-support/reviews/*')))
    def test_both_explicit_opt_outs(self):
        target,meta=self.scaffold(['--figure-density','none','--no-source-completeness']);self.assertNotIn('figure_density',meta);self.assertNotIn('source_completeness',meta);self.assertFalse((target/'source-inventory.json').exists())
    def test_empty_default_inventory_fails_even_without_materials(self):
        target,meta=self.scaffold([]);errors=[]
        with patch.object(v,'REPO_ROOT',target.parents[3]):v.validate_source_completeness(meta,target/'report.html',errors,[])
        self.assertTrue(any('scope missing' in e for e in errors))

class PublicPartialReportRejectionTests(unittest.TestCase):
    def test_any_report_scope_is_rejected_in_every_session_metadata(self):
        for value in ['false', '"sections-v1"', '{version="sections-v1",sections=["1.1"],include_intro=true}']:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                # Even malformed/unknown session metadata cannot evade the public prohibition.
                for slug in ('one', 'two'):
                    target = root/'studies'/slug/'presentations'/'session'/'presentation.toml'
                    target.parent.mkdir(parents=True)
                    target.write_text('study_id="unknown"\nreport_scope='+value+'\n')
                errors=[]
                v.validate_metadata(root, {}, errors, [])
                self.assertEqual(2, sum('partial report publication is disabled' in e for e in errors))

    def test_full_metadata_does_not_trigger_partial_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            target=root/'studies'/'one'/'presentations'/'session'/'presentation.toml'
            target.parent.mkdir(parents=True)
            target.write_text('study_id="unknown"\n')
            errors=[]
            v.validate_metadata(root, {}, errors, [])
            self.assertFalse(any('partial report publication is disabled' in e for e in errors))
