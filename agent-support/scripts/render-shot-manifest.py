#!/usr/bin/env python3
"""Run guarded browser captures serially from a strict JSON manifest."""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNNER = (
    Path.home()
    / ".local"
    / "libexec"
    / "aimlquant-safe-browser-shot"
    / "safe-browser-shot.sh"
)
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "tmp" / "browser-shots"
ALLOWED_KEYS = {
    "url",
    "output",
    "format",
    "width",
    "height",
    "virtual_time_budget",
    "timeout",
}


@dataclass(frozen=True)
class Capture:
    url: str
    output: Path
    output_format: str
    width: int
    height: int
    virtual_time_budget: int | None
    timeout: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--runner", type=Path, default=DEFAULT_RUNNER)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="retry each failed capture this many times (default: 3)",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="initial retry and runner handoff delay in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="resume a batch by skipping outputs that pass artifact validation",
    )
    return parser.parse_args()


def require_integer(
    item: dict[str, object], key: str, default: int | None, minimum: int, maximum: int
) -> int | None:
    value = item.get(key, default)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return value


def load_manifest(path: Path, output_root: Path) -> list[Capture]:
    if not path.is_absolute():
        raise ValueError("--manifest must be an absolute path")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON manifest: {exc}") from exc

    if not isinstance(data, dict) or set(data) != {"version", "captures"}:
        raise ValueError("manifest must contain exactly version and captures")
    if data["version"] != 1:
        raise ValueError("manifest version must be 1")
    rows = data["captures"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("captures must be a list with 1..100 entries")

    root = output_root.resolve()
    if not root.is_dir():
        raise ValueError(f"output root must already exist: {root}")
    captures: list[Capture] = []
    seen_outputs: set[Path] = set()
    for index, item in enumerate(rows, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"capture {index} must be an object")
        unknown = sorted(set(item) - ALLOWED_KEYS)
        missing = sorted({"url", "output"} - set(item))
        if unknown or missing:
            raise ValueError(
                f"capture {index} has unknown keys {unknown} or missing keys {missing}"
            )

        url = item["url"]
        output_value = item["output"]
        if not isinstance(url, str) or urlparse(url).scheme not in {"http", "https"}:
            raise ValueError(f"capture {index} url must use http:// or https://")
        if not isinstance(output_value, str):
            raise ValueError(f"capture {index} output must be a string")
        output = Path(output_value)
        if not output.is_absolute():
            raise ValueError(f"capture {index} output must be absolute")
        output_resolved = output.resolve(strict=False)
        try:
            output_resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(
                f"capture {index} output must stay under {root}: {output}"
            ) from exc
        if output_resolved in seen_outputs:
            raise ValueError(f"duplicate capture output: {output}")
        seen_outputs.add(output_resolved)
        if not output.parent.is_dir():
            raise ValueError(f"capture {index} output directory does not exist: {output.parent}")

        output_format = item.get("format", "png")
        if output_format not in {"png", "pdf"}:
            raise ValueError(f"capture {index} format must be png or pdf")
        if output.suffix.lower() != f".{output_format}":
            raise ValueError(
                f"capture {index} output extension must match format {output_format}"
            )

        width = require_integer(item, "width", 1600, 320, 4096)
        height = require_integer(item, "height", 900, 180, 32000)
        virtual_time_budget = require_integer(
            item, "virtual_time_budget", None, 1, 60000
        )
        timeout = require_integer(item, "timeout", 120, 5, 120)
        assert width is not None and height is not None and timeout is not None
        captures.append(
            Capture(
                url=url,
                output=output,
                output_format=output_format,
                width=width,
                height=height,
                virtual_time_budget=virtual_time_budget,
                timeout=timeout,
            )
        )
    return captures


def runner_command(runner: Path, capture: Capture) -> list[str]:
    command = [
        str(runner),
        "--format",
        capture.output_format,
        "--url",
        capture.url,
        "--output",
        str(capture.output),
        "--width",
        str(capture.width),
        "--height",
        str(capture.height),
        "--timeout",
        str(capture.timeout),
    ]
    if capture.virtual_time_budget is not None:
        command.extend(
            ["--virtual-time-budget", str(capture.virtual_time_budget)]
        )
    return command


def minimum_png_bytes(capture: Capture) -> int:
    """Reject implausibly empty screenshots without penalizing small viewports."""

    return max(1024, min(8192, (capture.width * capture.height) // 100))


def output_problem(capture: Capture) -> str | None:
    """Return a concise validation failure, or ``None`` for a usable artifact."""

    try:
        data = capture.output.read_bytes()
    except OSError:
        return "output file is missing or unreadable"
    if capture.output_format == "png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "PNG signature is missing"
        if len(data) < 24 or data[12:16] != b"IHDR":
            return "PNG IHDR is missing"
        width, height = struct.unpack(">II", data[16:24])
        if (width, height) != (capture.width, capture.height):
            return (
                f"PNG dimensions are {width}x{height}, expected "
                f"{capture.width}x{capture.height}"
            )
        required = minimum_png_bytes(capture)
        if len(data) < required:
            return (
                f"PNG is implausibly small ({len(data)} bytes; "
                f"minimum {required})"
            )
        return None
    if not data.startswith(b"%PDF-"):
        return "PDF signature is missing"
    return None


def output_looks_complete(capture: Capture) -> bool:
    return output_problem(capture) is None


def main() -> int:
    args = parse_args()
    try:
        if not 0 <= args.retries <= 10:
            raise ValueError("--retries must be between 0 and 10")
        if not 0 <= args.retry_delay <= 60:
            raise ValueError("--retry-delay must be between 0 and 60")
        runner = args.runner.resolve(strict=True)
        if not runner.is_file():
            raise ValueError(f"runner is not a regular file: {runner}")
        captures = load_manifest(args.manifest, args.output_root)
        completed = 0
        skipped = 0
        failures: list[tuple[int, Capture, int]] = []
        launched = False
        for index, capture in enumerate(captures, start=1):
            if args.skip_existing and output_looks_complete(capture):
                skipped += 1
                print(
                    f"[{index}/{len(captures)}] skip complete {capture.output}",
                    flush=True,
                )
                continue
            print(
                f"[{index}/{len(captures)}] {capture.output_format} "
                f"{capture.width}x{capture.height} -> {capture.output}",
                flush=True,
            )
            final_status = 1
            for attempt in range(1, args.retries + 2):
                # The guarded runner uses a transient user service. Give
                # systemd a handoff window before reusing its fixed service
                # name; retries use exponential backoff for slower teardown.
                if launched and args.retry_delay:
                    delay = min(args.retry_delay * (2 ** (attempt - 1)), 30.0)
                    time.sleep(delay)
                launched = True
                result = subprocess.run(
                    runner_command(runner, capture),
                    check=False,
                    text=True,
                    capture_output=True,
                )
                if result.stdout:
                    print(result.stdout.rstrip())
                if result.stderr:
                    print(result.stderr.rstrip(), file=sys.stderr)
                final_status = result.returncode
                if not final_status:
                    problem = output_problem(capture)
                    if problem:
                        final_status = 65
                        print(
                            f"capture {index} attempt {attempt}/{args.retries + 1} "
                            f"produced an invalid artifact: {problem}",
                            file=sys.stderr,
                        )
                    else:
                        completed += 1
                        break
                else:
                    print(
                        f"capture {index} attempt {attempt}/{args.retries + 1} "
                        f"failed with exit status {final_status}",
                        file=sys.stderr,
                    )
            else:
                failures.append((index, capture, final_status))

        print(
            "capture summary: "
            f"completed={completed} skipped={skipped} failed={len(failures)}"
        )
        if failures:
            for index, capture, status in failures:
                print(
                    f"FAILED [{index}/{len(captures)}] status={status} "
                    f"output={capture.output}",
                    file=sys.stderr,
                )
            return failures[0][2] or 1
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
