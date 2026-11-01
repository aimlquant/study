#!/usr/bin/env node
// Narrow DOM-only exception: no screenshots, PDF, video or remote requests.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
export function geometryFindings(boxes, frame) {
  const findings = [];
  for (const a of boxes) {
    if (!(a.width > 0 && a.height > 0)) {
      findings.push({type:'empty_text_box', text:a.text}); continue;
    }
    if (a.x < frame.x-1 || a.y < frame.y-1 || a.x+a.width > frame.x+frame.width+1 || a.y+a.height > frame.y+frame.height+1)
      findings.push({type:'text_outside_svg', text:a.text, box:a});
  }
  for (let i=0; i<boxes.length; i++) for (let j=i+1; j<boxes.length; j++) {
    const a=boxes[i], b=boxes[j];
    const x=Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x);
    const y=Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y);
    if(x>1 && y>1) findings.push({type:'text_overlap', texts:[a.text,b.text], overlap:{width:x,height:y}});
  }
  return findings;
}
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
async function main() {
  const args=process.argv.slice(2), options={};
  for(let i=0;i<args.length;i+=2) {
    if(!['--report','--width','--output'].includes(args[i]) || !args[i+1]) throw Error('expected --report PATH --width 1440|390 --output JSON');
    options[args[i]]=args[i+1];
  }
  const report=fs.realpathSync(options['--report']), root=path.dirname(report);
  const output=path.resolve(options['--output']), width=Number(options['--width']);
  fs.writeFileSync(output,JSON.stringify({passed:false,status:'inspection_not_finished'})+'\n');
  if(![1440,390].includes(width)) throw Error('width must be 1440 or 390');
  if(output===report || output.startsWith(root+path.sep)) throw Error('write QA evidence outside the session');
  const cg=fs.readFileSync('/proc/self/cgroup','utf8').trim().split('\n').find(x=>x.startsWith('0::'))?.slice(3);
  if(!cg || !/\/h1-run-[^/]+\.scope/.test(cg)) throw Error('run through h1-run --mem 4G --timeout 120');
  const cap=fs.readFileSync('/sys/fs/cgroup'+cg+'/memory.max','utf8').trim();
  if(cap==='max' || Number(cap)>4*1024**3) throw Error('h1-run MemoryMax must be <=4G');
  const safe=path.join(process.env.HOME,'.local/libexec/aimlquant-safe-browser-shot/safe-browser-shot.sh');
  execFileSync(safe,['--check'],{timeout:10000,stdio:'pipe'});
  const puppeteer=require('puppeteer');
  let browser, deadline;
  const result={schema_version:1,tool:'svg-text-bbox',viewport:width,report_sha256:hash(fs.readFileSync(report)),css:[],figures:[],passed:false};
  try {
    deadline=setTimeout(()=>{ if(browser) browser.close().catch(()=>{}); },90000);
    browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome-stable',headless:true,timeout:15000,args:['--no-sandbox','--disable-dev-shm-usage','--disable-background-networking']});
    const page=await browser.newPage();
    await page.setViewport({width,height:1200});
    await page.setJavaScriptEnabled(false);
    await page.setRequestInterception(true);
    page.on('request',req=>{
      try {
        const u=new URL(req.url());
        if(u.protocol==='file:' && fileURLToPath(u).startsWith(root+path.sep)) return req.continue();
      } catch {}
      req.abort();
    });
    await page.goto(pathToFileURL(report).href,{waitUntil:'load',timeout:15000});
    if(width===390) await page.addStyleTag({content:'html,body{width:390px!important;min-width:0!important}'});
    await page.evaluate(()=>document.fonts.ready);
    // Load only the session's known KaTeX assets, after the inert report load.
    // No application JS runs; network requests remain blocked outside the session.
    await page.setJavaScriptEnabled(true);
    for(const name of ['katex.min.js','auto-render.min.js']) {
      const asset=path.join(root,'assets/katex',name);
      if(!fs.existsSync(asset)) throw Error('missing local KaTeX asset: '+name);
      await page.addScriptTag({content:fs.readFileSync(asset,'utf8')});
    }
    result.math=await page.evaluate(async()=>{
      const body=document.querySelector('article') || document.body;
      const errors=[];
      renderMathInElement(body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'\\[',right:'\\]',display:true},{left:'\\(',right:'\\)',display:false},{left:'$',right:'$',display:false}],throwOnError:false,errorCallback:message=>errors.push(message),ignoredTags:['script','noscript','style','textarea','pre','code','option']});
      await document.fonts.ready;
      const findings=errors.map(message=>({type:'katex_parse_error',message}));
      for(const e of body.querySelectorAll('.katex-error')) findings.push({type:'katex_error_node',text:e.textContent});
      const walker=document.createTreeWalker(body,NodeFilter.SHOW_TEXT);
      while(walker.nextNode()) {
        const n=walker.currentNode;
        if(n.parentElement.closest('.katex,script,style,pre,code')) continue;
        if(/\\[()[\]]|\$\$/.test(n.textContent)) findings.push({type:'unrendered_math',text:n.textContent});
      }
      const equations=[...body.querySelectorAll('.katex')].map(e=>{
        const r=e.getBoundingClientRect();
        if(!r.width || !r.height) findings.push({type:'empty_equation',text:e.textContent});
        for(const svg of e.querySelectorAll('svg')) {
          const b=svg.getBoundingClientRect();
          if(!b.width || !b.height) findings.push({type:'empty_math_svg',text:e.textContent});
        }
        return {tex:e.querySelector('annotation')?.textContent,width:r.width,height:r.height};
      });
      return {equations,findings};
    });
    const inputs=await page.evaluate(()=>({
      css:[...document.querySelectorAll('link[rel="stylesheet"]')].map(x=>x.href),
      figs:[...document.querySelectorAll('figure img')].filter(x=>new URL(x.src).pathname.endsWith('.svg')).map(x=>({src:x.src,width:x.getBoundingClientRect().width,id:x.closest('figure').id}))
    }));
    if(!inputs.figs.length) throw Error('no local SVG figures to inspect');
    for(const href of inputs.css) {
      const p=fileURLToPath(href); if(!p.startsWith(root+path.sep)) throw Error('nonlocal CSS');
      result.css.push({path:path.relative(root,p),sha256:hash(fs.readFileSync(p))});
    }
    for(const fig of inputs.figs) {
      const p=fileURLToPath(fig.src); if(!p.startsWith(root+path.sep)) throw Error('nonlocal SVG');
      const source=fs.readFileSync(p,'utf8');
      const geometry=await page.evaluate(async ({source,width})=>{
        const holder=document.createElement('div'); holder.style.cssText=`position:absolute;left:-10000px;top:0;width:${width}px`;
        holder.className='report-section';
        const svg=new DOMParser().parseFromString(source,'image/svg+xml').documentElement;
        if(svg.localName!=='svg' || svg.querySelector('parsererror')) throw Error('invalid SVG');
        holder.append(document.importNode(svg,true)); document.body.append(holder);
        const element=holder.firstElementChild;
        element.style.setProperty('width',`${width}px`,'important');
        element.style.setProperty('max-width','none','important');
        await document.fonts.ready;
        const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};};
        const data={frame:rect(element),boxes:[...element.querySelectorAll('text')].map(t=>({text:t.textContent.trim(),...rect(t)})).filter(t=>t.text)};
        holder.remove(); return data;
      },{source,width:fig.width});
      result.figures.push({id:fig.id,path:path.relative(root,p),sha256:hash(source),display_width:fig.width,...geometry,findings:geometryFindings(geometry.boxes,geometry.frame)});
    }
    result.passed=result.figures.every(x=>!x.findings.length) && !result.math.findings.length;
  } finally {
    clearTimeout(deadline);
    if(browser) await browser.close();
    fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
  }
  console.log(JSON.stringify({passed:result.passed,figures:result.figures.length,output}));
  if(!result.passed) process.exitCode=1;
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) main().catch(e=>{console.error(e.message);process.exitCode=1;});
