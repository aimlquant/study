import {test} from 'node:test';
import assert from 'node:assert/strict';
import {geometryFindings} from '../scripts/check-svg-bboxes.mjs';
const frame={x:0,y:0,width:200,height:100};
const a={text:'A',x:10,y:10,width:50,height:20};
test('separate labels pass',()=>assert.deepEqual(geometryFindings([a,{...a,text:'B',x:80}],frame),[]));
test('actual overlapping labels fail',()=>assert.equal(geometryFindings([a,{...a,text:'B',x:30}],frame)[0].type,'text_overlap'));
test('outside viewbox fails',()=>assert.equal(geometryFindings([{...a,x:190}],frame)[0].type,'text_outside_svg'));
test('empty bbox fails',()=>assert.equal(geometryFindings([{...a,width:0}],frame)[0].type,'empty_text_box'));
