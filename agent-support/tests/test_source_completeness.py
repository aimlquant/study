import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('completeness',Path(__file__).resolve().parents[1]/'scripts/validate-site.py')
v=importlib.util.module_from_spec(spec);sys.modules[spec.name]=v;spec.loader.exec_module(v)

class SourceCompletenessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'materials').mkdir();(self.root/'agent-support/reviews').mkdir(parents=True)
        self.report=self.root/'report.html'
        self.report.write_text(r'<figure id="fig" data-source-kind="figure" data-source-ref="1.1"><img src="fig.svg"><figcaption>원본 판독값</figcaption></figure><p id="eq">\(a=b\)</p><p id="purpose">계산 대상</p><p id="symbols">기호</p><p id="example">1=1</p>')
        (self.root/'fig.svg').write_text('<svg/>')
        source='Figure 1.1: test\n$a=b$ ![source](figure.jpg)\n'
        self.sources=[]
        for name in ['original','explainer']:
            path=self.root/f'materials/{name}.md';path.write_text(source)
            self.sources.append(dict(id=name,path=f'materials/{name}.md',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),lines=[1,2],math=[dict(offset=source.index('$'),tex='$a=b$',report_id='eq',purpose_id='purpose',symbols_id='symbols',example_id='example')],images=[dict(offset=source.index('!['),path='figure.jpg',classification='correspondence',report_id='fig')],visuals=[dict(kind='figure',ref='1.1',report_id='fig',method='source-reading')]))
        self.inventory=dict(version=1,scope=['1.1'],sources=self.sources)
        self.meta=dict(source_completeness='visual-math-v1',source_inventory='agent-support/reviews/inventory.json')
    def check_inventory(self):
        (self.root/self.meta['source_inventory']).write_text(json.dumps(self.inventory))
        errors=[]
        with patch.object(v,'REPO_ROOT',self.root):v.validate_source_completeness(self.meta,self.report,errors)
        return errors
    def test_two_source_occurrences_map_to_one_equation(self):self.assertEqual([],self.check_inventory())
    def test_uncaptioned_image_cannot_be_omitted(self):
        self.sources[0]['images']=[];self.assertIn('image occurrence coverage mismatch',self.check_inventory()[0])
    def test_linked_thumbnail_is_also_extracted(self):
        text='[![thumbnail](thumb.png)](large.png)'
        self.assertEqual(['thumb.png'],[m[1] for m in v.SOURCE_IMAGE_RE.finditer(text)])
    def test_decoration_needs_reason(self):
        self.sources[0]['images'][0].update(classification='decoration');self.assertIn('reason',self.check_inventory()[0])
    def test_missing_math_occurrence(self):
        self.sources[0]['math']=[];self.assertIn('coverage mismatch',self.check_inventory()[0])
    def test_missing_visual(self):
        self.sources[0]['visuals']=[];self.assertIn('coverage mismatch',self.check_inventory()[0])
    def test_stale_source(self):
        self.sources[0]['sha256']='0'*64;self.assertIn('stale',self.check_inventory()[0])
    def test_missing_explanation(self):
        self.sources[0]['math'][0]['example_id']='missing';self.assertIn('explanation',self.check_inventory()[0])
    def test_unrelated_text_cannot_be_equation(self):
        self.report.write_text(self.report.read_text().replace(r'\(a=b\)','text'));self.assertIn('missing report equation',self.check_inventory()[0])
    def test_expression_cannot_be_excluded_as_symbol(self):
        self.sources[0]['math'][0].update(classification='symbol',reason='symbol');self.assertIn('cannot be excluded',self.check_inventory()[0])
    def test_reading_caption_required(self):
        self.report.write_text(self.report.read_text().replace('원본 판독값',''));self.assertIn('caption',self.check_inventory()[0])
    def test_legacy_noop_and_unknown_rejected(self):
        errors=[];v.validate_source_completeness({},self.report,errors);self.assertEqual([],errors)
        v.validate_source_completeness({'source_completeness':'bad'},self.report,errors);self.assertTrue(errors)
