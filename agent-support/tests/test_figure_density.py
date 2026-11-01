import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('density_validator', ROOT/'agent-support/scripts/validate-site.py')
v = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v
spec.loader.exec_module(v)

class FigureDensityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for i in range(3):
            (self.root/f'{i}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg"><rect/><circle/><text>{i}</text></svg>')
        self.report = self.root/'report.html'
    def check(self, content, metadata=None):
        self.report.write_text(content)
        errors=[]
        v.validate_figure_density({'figure_density':'rich-v1'} if metadata is None else metadata,self.report,errors)
        return errors
    def figure(self, i):
        return f'<figure id="f{i}"><img src="{i}.svg"></figure>'
    def section(self, body):
        return '<section id="s1" data-source-kind="section">'+body+'</section>'
    def test_legacy_does_nothing(self):
        self.assertEqual([],self.check('',{}))
    def test_unknown_mode_rejected(self):
        self.assertIn('unknown',self.check('',{'figure_density':'rich-v9'})[0])
    def test_source_section_needs_two(self):
        self.assertTrue(self.check(self.section(self.figure(0))))
    def test_each_unit_needs_a_figure(self):
        html=self.section('<h3 id="a">A</h3>'+self.figure(0)+self.figure(1)+'<h3 id="b">B</h3>')
        self.assertTrue(any('H3' in e for e in self.check(html)))
    def test_two_units_with_distinct_figures_pass(self):
        self.assertEqual([],self.check(self.section('<h3 id="a">A</h3>'+self.figure(0)+'<h3 id="b">B</h3>'+self.figure(1))))
    def test_duplicate_bytes_fail(self):
        (self.root/'1.svg').write_bytes((self.root/'0.svg').read_bytes())
        self.assertTrue(any('duplicate' in e for e in self.check(self.section(self.figure(0)+self.figure(1)))))
    def test_missing_file_fails(self):
        self.assertTrue(any('missing' in e for e in self.check(self.section(self.figure(9)))))
    def test_decoration_does_not_count(self):
        (self.root/'1.svg').write_text('<svg><defs><rect/><circle/></defs><text>icon</text></svg>')
        self.assertTrue(any('shapes' in e for e in self.check(self.section(self.figure(0)+self.figure(1)))))
    def test_reference_only_explicit_exemption(self):
        self.assertEqual([],self.check(self.section(self.figure(0)+self.figure(1)+'<h3 data-visual-exempt="참고 링크 목록">참고</h3>')))
