from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DRIVER = REPO_ROOT / "agent-support" / "scripts" / "render-shot-manifest.py"


FAKE_RUNNER = """#!/usr/bin/env python3
import json
import os
import struct
import sys
from pathlib import Path

args = sys.argv[1:]
value = {args[index][2:]: args[index + 1] for index in range(0, len(args), 2)}
with Path(os.environ["FAKE_RUNNER_LOG"]).open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(value, ensure_ascii=False) + "\\n")
if "fail" in value["url"]:
    raise SystemExit(7)
if "flaky" in value["url"]:
    rows = Path(os.environ["FAKE_RUNNER_LOG"]).read_text(encoding="utf-8").splitlines()
    if sum('"url": "' + value["url"] + '"' in row for row in rows) == 1:
        raise SystemExit(8)
output = Path(value["output"])
if value["format"] == "pdf":
    output.write_bytes(b"%PDF-test")
else:
    width = int(value["width"])
    height = int(value["height"])
    if "wrong-size" in value["url"]:
        width += 1
    header = (
        b"\\x89PNG\\r\\n\\x1a\\n"
        + b"\\x00\\x00\\x00\\rIHDR"
        + struct.pack(">II", width, height)
    )
    if "blank" in value["url"]:
        output.write_bytes(header)
    else:
        required = max(1024, min(8192, (width * height) // 100))
        output.write_bytes(header.ljust(required, b"\\x00"))
"""


class ShotManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.output_root = self.root / "tmp" / "browser-shots"
        self.output_root.mkdir(parents=True)
        self.runner = self.root / "fake-runner.py"
        self.runner.write_text(FAKE_RUNNER, encoding="utf-8")
        self.runner.chmod(0o700)
        self.log = self.root / "runner.log"

    def run_driver(
        self,
        captures: list[dict[str, object]],
        *extra_args: str,
    ) -> subprocess.CompletedProcess[str]:
        manifest = self.root / "manifest.json"
        manifest.write_text(
            json.dumps({"version": 1, "captures": captures}),
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["FAKE_RUNNER_LOG"] = str(self.log)
        return subprocess.run(
            [
                sys.executable,
                str(DRIVER),
                "--manifest",
                str(manifest),
                "--runner",
                str(self.runner),
                "--output-root",
                str(self.output_root),
                "--retry-delay",
                "0",
                *extra_args,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    @staticmethod
    def fake_png(width: int = 1600, height: int = 900) -> bytes:
        header = (
            b"\x89PNG\r\n\x1a\n"
            + b"\x00\x00\x00\rIHDR"
            + width.to_bytes(4, "big")
            + height.to_bytes(4, "big")
        )
        required = max(1024, min(8192, (width * height) // 100))
        return header.ljust(required, b"\x00")

    def test_runs_png_and_pdf_serially(self) -> None:
        png = self.output_root / "deck.png"
        pdf = self.output_root / "report.pdf"

        result = self.run_driver(
            [
                {"url": "http://localhost:8000/deck", "output": str(png)},
                {
                    "url": "http://localhost:8000/report",
                    "output": str(pdf),
                    "format": "pdf",
                },
            ]
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual([row["format"] for row in rows], ["png", "pdf"])
        self.assertEqual([row["output"] for row in rows], [str(png), str(pdf)])
        self.assertTrue(png.is_file())
        self.assertTrue(pdf.is_file())

    def test_retries_failure_and_continues_the_batch(self) -> None:
        result = self.run_driver(
            [
                {
                    "url": "http://localhost:8000/first",
                    "output": str(self.output_root / "first.png"),
                },
                {
                    "url": "http://localhost:8000/fail",
                    "output": str(self.output_root / "failed.png"),
                },
                {
                    "url": "http://localhost:8000/third",
                    "output": str(self.output_root / "third.png"),
                },
            ]
        )

        self.assertEqual(result.returncode, 7)
        rows = self.log.read_text().splitlines()
        self.assertEqual(len(rows), 6)
        self.assertEqual(sum('"url": "http://localhost:8000/fail"' in row for row in rows), 4)
        self.assertTrue((self.output_root / "third.png").exists())
        self.assertIn("completed=2 skipped=0 failed=1", result.stdout)

    def test_retries_a_transient_failure_until_it_succeeds(self) -> None:
        output = self.output_root / "flaky.png"

        result = self.run_driver(
            [{"url": "http://localhost:8000/flaky", "output": str(output)}]
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.log.read_text().splitlines()), 2)
        self.assertTrue(output.is_file())

    def test_skip_existing_resumes_only_complete_outputs(self) -> None:
        complete = self.output_root / "complete.png"
        incomplete = self.output_root / "incomplete.png"
        complete.write_bytes(self.fake_png())
        incomplete.write_bytes(b"partial")

        result = self.run_driver(
            [
                {"url": "http://localhost:8000/complete", "output": str(complete)},
                {"url": "http://localhost:8000/incomplete", "output": str(incomplete)},
            ],
            "--skip-existing",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual([row["url"] for row in rows], ["http://localhost:8000/incomplete"])
        self.assertIn("completed=1 skipped=1 failed=0", result.stdout)

    def test_retries_successful_but_blank_or_wrong_size_pngs(self) -> None:
        result = self.run_driver(
            [
                {
                    "url": "http://localhost:8000/blank",
                    "output": str(self.output_root / "blank.png"),
                },
                {
                    "url": "http://localhost:8000/wrong-size",
                    "output": str(self.output_root / "wrong-size.png"),
                },
                {
                    "url": "http://localhost:8000/valid",
                    "output": str(self.output_root / "valid.png"),
                },
            ]
        )

        self.assertEqual(result.returncode, 65)
        rows = self.log.read_text().splitlines()
        self.assertEqual(len(rows), 9)
        self.assertIn("implausibly small", result.stderr)
        self.assertIn("expected 1600x900", result.stderr)
        self.assertTrue((self.output_root / "valid.png").exists())
        self.assertIn("completed=1 skipped=0 failed=2", result.stdout)

    def test_rejects_output_outside_browser_shots(self) -> None:
        result = self.run_driver(
            [
                {
                    "url": "http://localhost:8000/deck",
                    "output": str(self.root / "outside.png"),
                }
            ]
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("must stay under", result.stderr)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
