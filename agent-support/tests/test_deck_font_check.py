from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CHECK = REPO_ROOT / "agent-support" / "scripts" / "deck-font-check.py"

# Stands in for the browser runner: posts a chosen result, or writes nothing when rendering.
FAKE_RUNNER = r"""#!/usr/bin/env python3
import json, os, struct, sys, urllib.parse, urllib.request, zlib

args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
url = urllib.parse.urlparse(args["--url"])
case = os.environ["FONT_CHECK_CASE"]
good = [{"n": n, "measured": 3, "issues": []} for n in (1, 2)]
rows = {
    "empty": [],
    "partial": good[:1],
    "duplicate": [good[0], good[0]],
    "unmeasured": [{"n": 1, "measured": 0, "issues": []}, good[1]],
    "issue": [good[0], {"n": 2, "measured": 3, "issues": ["본문 넘침"]}],
}.get(case, good)
if url.query:
    font = urllib.parse.parse_qs(url.query)["font"][0]
    report = urllib.parse.urlunparse(url._replace(path="/report", query="font=" + font))
    urllib.request.urlopen(urllib.request.Request(report, data=json.dumps(rows).encode(), method="POST"))
    sys.exit(17 if case == "post_then_fail" else 0)
if case == "render_writes_nothing":
    sys.exit(0)
def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
w, h = int(args["--width"]), int(args["--height"])
raw = b"".join(b"\0" + os.urandom(w * 3) for _ in range(h))
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
open(args["--output"], "wb").write(png)
"""

FAKE_FC_LIST = """#!/bin/sh
echo "Noto Sans CJK KR"
echo "NanumGothic"
"""

DECK = """<!doctype html><html><head></head><body><div class="stage">
<section class="slide slide--teaching"><h1>하나</h1></section>
<section class="slide slide--teaching"><h1>둘</h1></section>
</div></body></html>"""


class DeckFontCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.deck = root / "deck" / "index.html"
        self.deck.parent.mkdir()
        self.deck.write_text(DECK, encoding="utf-8")
        self.bin = root / "bin"
        self.bin.mkdir()
        for path, text in ((self.bin / "fc-list", FAKE_FC_LIST), (root / "runner.py", FAKE_RUNNER)):
            path.write_text(text, encoding="utf-8")
            path.chmod(path.stat().st_mode | stat.S_IEXEC)
        self.runner = root / "runner.sh"
        self.runner.write_text(f'#!/bin/bash\nexec {sys.executable} "{root / "runner.py"}" "$@"\n', encoding="utf-8")
        self.runner.chmod(0o755)
        self.render = root / "render"

    def run_check(self, case: str, *extra: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "FONT_CHECK_CASE": case, "PATH": f"{self.bin}:{os.environ['PATH']}"}
        return subprocess.run(
            [sys.executable, str(CHECK), str(self.deck), "--runner", str(self.runner), *extra],
            capture_output=True, text=True, env=env, timeout=120,
        )

    def test_complete_clean_result_passes(self):
        self.assertEqual(self.run_check("good").returncode, 0)

    def test_reported_issue_fails(self):
        self.assertEqual(self.run_check("issue").returncode, 1)

    def test_runner_failure_after_result_fails(self):
        self.assertEqual(self.run_check("post_then_fail").returncode, 2)

    def test_incomplete_results_fail(self):
        for case in ("empty", "partial", "duplicate", "unmeasured"):
            with self.subTest(case=case):
                self.assertEqual(self.run_check(case).returncode, 2)

    def test_deck_without_slides_fails(self):
        self.deck.write_text('<div class="stage"></div>', encoding="utf-8")
        self.assertEqual(self.run_check("empty").returncode, 2)

    def test_render_writes_new_files(self):
        self.assertEqual(self.run_check("good", "--render", str(self.render)).returncode, 0)
        self.assertEqual(len(list(self.render.glob("*.png"))), 4)

    def test_old_png_is_not_a_new_capture(self):
        self.assertEqual(self.run_check("good", "--render", str(self.render)).returncode, 0)
        old = self.render / "noto-01.png"
        os.utime(old, (946684800, 946684800))
        result = self.run_check("render_writes_nothing", "--render", str(self.render))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(int(old.stat().st_mtime), 946684800)


if __name__ == "__main__":
    unittest.main()
