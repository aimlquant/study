#!/usr/bin/env python3
"""Measure every deck slide for text overflow in two fonts.

The deck uses system fonts, so a render on one machine does not show how text
wraps on another. Malgun Gothic on Windows runs about 10% wider than the Noto
font on the render host. This copies the deck, swaps the font, and measures
text boxes in the owner-installed browser runner. Text inside SVG images is
not measured; use --render and look at the captures for that.
"""

from __future__ import annotations

import argparse
import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from functools import partial
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DEFAULT_RUNNER = Path.home() / ".local/libexec/aimlquant-safe-browser-shot/safe-browser-shot.sh"
MANIFEST_DRIVER = Path(__file__).with_name("render-shot-manifest.py")
FACE = (
    "@font-face{{font-family:WideCheck;src:local('NanumGothic');font-weight:400;size-adjust:{a}%}}"
    "@font-face{{font-family:WideCheck;src:local('NanumGothic Bold'),local('NanumGothicBold');"
    "font-weight:700 900;size-adjust:{a}%}}"
)
MEASURE = r"""
(async()=>{
const font=new URLSearchParams(location.search).get('font');
await document.fonts.ready;await new Promise(r=>setTimeout(r,2500));
// The runner's window is shorter than requested, so fix the scale to read CSS pixels.
document.documentElement.style.setProperty('--deck-scale','1');
const stage=document.querySelector('.stage');const slides=[...document.querySelectorAll('.slide')];
const rects=root=>{const out=[];const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;
 while(n=w.nextNode()){if(!n.textContent.trim()||n.parentElement.closest('.katex,script,style'))continue;
  const g=document.createRange();g.selectNodeContents(n);
  for(const r of g.getClientRects())if(r.width>0&&r.height>0)out.push({r,t:n.textContent.trim().slice(0,24),el:n.parentElement});}
 // Math keeps its intended inner overlaps, so measure each formula by its outer box.
 for(const e of root.querySelectorAll('.katex')){const r=e.getBoundingClientRect();if(r.width>0&&r.height>0)out.push({r,t:'수식',el:e.parentElement});}
 return out};
const hit=(a,b,m)=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>m&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>m;
const res=slides.map((s,i)=>{
 slides.forEach(x=>x.classList.toggle('is-active',x===s));
 const issues=[],S=stage.getBoundingClientRect(),kids=[...s.children].filter(k=>getComputedStyle(k).display!=='none');
 const tr=kids.map(rects);
 for(let x=0;x<kids.length;x++)for(let y=x+1;y<kids.length;y++)for(const p of tr[x])for(const q of tr[y])
  if(hit(p.r,q.r,.5))issues.push(`글자 겹침: ${p.t} / ${q.t}`);
 const body=s.querySelector('.slide-body'),take=s.querySelector('.takeaway'),foot=s.querySelector('.slide-footer');
 for(const {r,t,el} of rects(s)){
  if(r.right>S.right+.5||r.left<S.left-.5||r.bottom>S.bottom+.5||r.top<S.top-.5)issues.push(`무대 밖: ${t}`);
  const c=el.closest('article,td,th,figcaption,.takeaway,.lead');
  if(c){const b=c.getBoundingClientRect();if(r.bottom>b.bottom+1||r.right>b.right+1)issues.push(`칸 넘침: ${t}`)}
  if(body&&body.contains(el)){const b=body.getBoundingClientRect();
   if(r.bottom>b.bottom+.5||r.right>b.right+.5)issues.push(`본문 넘침: ${t}`);
   for(const e of [take,foot])if(e&&hit(r,e.getBoundingClientRect(),.5))issues.push(`본문이 ${e===take?'정리':'꼬리'}에 닿음: ${t}`)}
 }
 if(body){
  // Same-body text in different blocks, with a margin for font metric boxes that overlap without ink.
  const t=rects(body);for(let a=0;a<t.length;a++)for(let b=a+1;b<t.length;b++)
   if(t[a].el!==t[b].el&&!t[a].el.contains(t[b].el)&&!t[b].el.contains(t[a].el)&&hit(t[a].r,t[b].r,3))issues.push(`본문 글자 겹침: ${t[a].t} / ${t[b].t}`);
  const x=body.getBoundingClientRect();
  for(const e of body.querySelectorAll('article,table,img,figure')){const r=e.getBoundingClientRect();
   if(r.bottom>x.bottom+1||r.right>x.right+1)issues.push(`요소 넘침: ${e.tagName}`)}
 }
 return {n:i+1,measured:rects(s).length,issues:[...new Set(issues)]};
});
await fetch('/report?font='+font,{method:'POST',body:JSON.stringify(res)});
})();
"""


def make_variant(deck: Path, out: Path, adjust: float | None, measure: bool) -> None:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(deck, out)
    page = out / "index.html"
    text = page.read_text(encoding="utf-8")
    if adjust is not None:
        face = FACE.format(a=adjust)
        style = f"<style>{face}:root{{--font-sans-ko:WideCheck,sans-serif}}*{{font-kerning:none;text-rendering:auto}}body{{word-spacing:.05em}}</style>"
        text = text.replace("</head>", style + "</head>", 1)
        for svg in out.rglob("*.svg"):
            body = svg.read_text(encoding="utf-8")
            body = re.sub(r"font-family\s*:\s*'Noto Sans CJK KR'[^;\"}]*", "font-family:WideCheck", body)
            body = re.sub(r'font-family="[^"]*Noto Sans CJK KR[^"]*"', 'font-family="WideCheck"', body)
            body = re.sub(r"(<svg\b[^>]*>)", lambda m: f"{m.group(1)}<style>{face}text{{font-kerning:none}}</style>", body, count=1)
            svg.write_text(body, encoding="utf-8")
    if measure:
        text = text.replace("</body>", f"<script>{MEASURE}</script></body>", 1)
    page.write_text(text, encoding="utf-8")


def result_problem(rows: object, expected: int) -> str | None:
    """Return why a measurement cannot count as a complete check, or None."""
    if not isinstance(rows, list) or len(rows) != expected:
        return f"expected {expected} slides, got {len(rows) if isinstance(rows, list) else type(rows).__name__}"
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict) or row.get("n") != number:
            return f"slide {number}: wrong number or shape"
        if not isinstance(row.get("issues"), list):
            return f"slide {number}: issues missing"
        if not isinstance(row.get("measured"), int) or row["measured"] < 1:
            return f"slide {number}: nothing measured"
    return None


def serve(root: Path, results: dict) -> http.server.ThreadingHTTPServer:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_POST(self):
            size = int(self.headers.get("Content-Length", 0))
            font = parse_qs(urlparse(self.path).query)["font"][0]
            results[font] = json.loads(self.rfile.read(size))
            self.send_response(204)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def render_all(args: argparse.Namespace, deck: Path, root: Path, base: str, total: int) -> bool:
    """Capture into an empty directory first, so an old PNG can never pass as a new capture."""
    fresh = root / "render"
    fresh.mkdir()
    for font in ("noto", "wide"):
        make_variant(deck, root / font, None if font == "noto" else args.wide_adjust, False)
        captures = [
            {"url": f"{base}/{font}/index.html#/{n}", "output": str(fresh / f"{font}-{n:02d}.png"), "width": 1280, "height": 720}
            for n in range(1, total + 1)
        ]
        manifest = root / f"manifest-{font}.json"
        manifest.write_text(json.dumps({"version": 1, "captures": captures}), encoding="utf-8")
        done = subprocess.run(
            [sys.executable, str(MANIFEST_DRIVER), "--manifest", str(manifest),
             "--runner", str(args.runner), "--output-root", str(fresh)],
        )
        if done.returncode:
            print(f"ERROR: render failed for {font}", file=sys.stderr)
            return False
    wanted = [f"{font}-{n:02d}.png" for font in ("noto", "wide") for n in range(1, total + 1)]
    missing = [name for name in wanted if not (fresh / name).is_file()]
    if missing:
        print(f"ERROR: render left out {len(missing)} files", file=sys.stderr)
        return False
    args.render.mkdir(parents=True, exist_ok=True)
    for name in wanted:
        shutil.move(str(fresh / name), str(args.render / name))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("deck", type=Path, help="deck index.html")
    parser.add_argument("--runner", type=Path, default=DEFAULT_RUNNER)
    parser.add_argument("--wide-adjust", type=float, default=107, help="size-adjust %% for the wide font (default 107)")
    parser.add_argument("--render", type=Path, help="also capture every slide in both fonts into this absolute directory")
    args = parser.parse_args()

    fonts = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True, check=True).stdout
    for family in ("Noto Sans CJK KR", "NanumGothic"):
        if family not in fonts:
            print(f"ERROR: font not installed: {family}", file=sys.stderr)
            return 2

    expected = len(re.findall(r"<section\b[^>]*\bclass=\"[^\"]*\bslide\b", args.deck.read_text(encoding="utf-8")))
    if not expected:
        print("ERROR: no slides found in the deck", file=sys.stderr)
        return 2
    if args.render and expected > 100:
        print("ERROR: --render handles at most 100 slides per font", file=sys.stderr)
        return 2

    results: dict = {}
    with tempfile.TemporaryDirectory(prefix="deck-font-check-") as tmp:
        root = Path(tmp)
        deck = args.deck.resolve().parent
        make_variant(deck, root / "noto", None, True)
        make_variant(deck, root / "wide", args.wide_adjust, True)
        server = serve(root, results)
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            for font in ("noto", "wide"):
                problem = "not run"
                for _ in range(3):
                    results.pop(font, None)
                    done = subprocess.run(
                        ["bash", str(args.runner), "--url", f"{base}/{font}/index.html?font={font}",
                         "--output", str(root / f"{font}.png"), "--width", "1280", "--height", "720",
                         "--virtual-time-budget", "9000"],
                        capture_output=True, text=True,
                    )
                    problem = f"runner exit {done.returncode}" if done.returncode else result_problem(results.get(font), expected)
                    if not problem:
                        break
                if problem:
                    print(f"ERROR: {font}: {problem} after three attempts", file=sys.stderr)
                    return 2

            failed = 0
            for font, label in (("noto", "Noto Sans CJK KR"), ("wide", f"넓은 글꼴 {args.wide_adjust:g}%")):
                bad = [row for row in results[font] if row["issues"]]
                failed += len(bad)
                print(f"{label}: {len(results[font])}장 중 문제 {len(bad)}장")
                for row in bad:
                    print(f"  {row['n']}장: " + "; ".join(row["issues"][:3]))

            if args.render and not render_all(args, deck, root, base, expected):
                return 2
            return 1 if failed else 0
        finally:
            server.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
