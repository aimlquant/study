#!/usr/bin/env python3
"""Extract report paragraphs and a seeded cross-sample, without judging prose."""

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import random
import re


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
EXCLUDED = {"figure", "table", "pre", "script", "style", "nav", "header", "footer", "noscript", "template"}
MATH = re.compile(r"\\\[.*?\\\]|\\\(.*?\\\)|\$\$.*?\$\$", re.S)


class ParagraphParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.candidates = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        parent = self.stack[-1] if self.stack else {}
        classes = attrs.get("class", "").split()
        section = parent.get("section")
        if tag == "section" and "report-section" in classes:
            section = attrs.get("data-source-ref") or attrs.get("id")
        excluded = (parent.get("excluded", False) or tag in EXCLUDED
                    or "hidden" in attrs or attrs.get("aria-hidden") == "true"
                    or "katex" in classes)
        note = parent.get("note", False) or "verification-note" in classes
        node = {"tag": tag, "section": section, "excluded": excluded, "note": note}
        if tag == "br" and not excluded:
            self.handle_data(" ")
        if tag in {"p", "li"}:
            for ancestor in self.stack:
                if "paragraph" in ancestor:
                    ancestor["paragraph"]["has_child"] = True
            paragraph = {"section": section, "id": attrs.get("id"), "tag": tag,
                         "kind": "note" if note else "body", "parts": [],
                         "has_child": False, "excluded": excluded}
            self.candidates.append(paragraph)
            node["paragraph"] = paragraph
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, text):
        if not self.stack or self.stack[-1]["excluded"]:
            return
        for node in self.stack:
            if "paragraph" in node:
                node["paragraph"]["parts"].append(text)


def extract_paragraphs(source, min_chars=25):
    parser = ParagraphParser()
    parser.feed(source)
    paragraphs = []
    for p in parser.candidates:
        text = " ".join("".join(p["parts"]).split())
        if (not p["section"] or p["excluded"] or p["has_child"]
                or len(text) < min_chars or not MATH.sub("", text).strip()):
            continue
        paragraphs.append({"number": len(paragraphs) + 1, "section": p["section"],
                           "id": p["id"], "tag": p["tag"], "kind": p["kind"],
                           "text": text})
    return paragraphs


def cross_sample(paragraphs, count, seed):
    if count < 0:
        raise ValueError("sample must be nonnegative")
    body = [p for p in paragraphs if p["kind"] == "body"]
    if count == 0:
        return []
    if seed is None:
        raise ValueError("--seed is required when sampling")
    sections = list(dict.fromkeys(p["section"] for p in body))
    if min(count, len(body)) < len(sections):
        raise ValueError("sample must cover at least one paragraph per section; select fewer --sections or increase --sample")
    rng = random.Random(seed)
    selected = [rng.choice([p["number"] for p in body if p["section"] == section])
                for section in sections]
    remaining = [p["number"] for p in body if p["number"] not in selected]
    selected += rng.sample(remaining, min(count, len(body)) - len(selected))
    return sorted(selected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--min-chars", type=int, default=25)
    parser.add_argument("--sample", type=int, default=30)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--sections", nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.min_chars < 1:
        parser.error("--min-chars must be positive")
    if args.output and args.output.resolve() == args.report.resolve():
        parser.error("--output must not overwrite the report")
    raw = args.report.read_bytes()
    paragraphs = extract_paragraphs(raw.decode("utf-8"), args.min_chars)
    if args.sections:
        unknown = set(args.sections) - {p["section"] for p in paragraphs}
        if unknown:
            parser.error(f"unknown or empty sections: {sorted(unknown)}")
        paragraphs = [p for p in paragraphs if p["section"] in args.sections]
    try:
        sample = cross_sample(paragraphs, args.sample, args.seed)
    except ValueError as exc:
        parser.error(str(exc))
    result = {"schema_version": 1, "report_sha256": hashlib.sha256(raw).hexdigest(),
              "extraction": {"min_chars": args.min_chars, "units": "leaf p/li inside report-section",
                             "sections": args.sections, "notes_sampled": False},
              "sampling": {"seed": args.seed, "requested": args.sample,
                           "method": "one random paragraph per section, then random remaining body"},
              "counts": {"body": sum(p["kind"] == "body" for p in paragraphs),
                         "note": sum(p["kind"] == "note" for p in paragraphs)},
              "paragraphs": paragraphs, "sample_numbers": sample}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
