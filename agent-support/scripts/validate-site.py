#!/usr/bin/env python3
"""Validate the AIML Quant GitHub Pages tree without dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "agent-support" / "studies.toml"
DEFAULT_SITE = REPO_ROOT / "html"
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_SESSION_BYTES = 30 * 1024 * 1024
SUPPORTED_ARTIFACTS = {"report", "slides"}
SOURCE_FIDELITY_VERSION = "source-structure-v1"
SOURCE_KINDS = {
    "section",
    "figure",
    "table",
    "listing",
    "example",
    "box",
    "exercise",
}
SOURCE_KIND_LABELS = {
    "section": "§",
    "figure": "그림",
    "table": "표",
    "listing": "Listing",
    "example": "예제",
    "box": "Box",
    "exercise": "연습문제",
}
CAPTION_NUMBER_RE = re.compile(r"^(그림|표)\s+([1-9][0-9]*)$")
CAPTION_REFERENCE_GROUP_RE = re.compile(
    r"(그림|표)\s*"
    r"([1-9][0-9]*(?!\.[0-9])"
    r"(?:\s*(?:[-–·,]\s*[1-9][0-9]*)*)?)"
)
EXTERNAL_CAPTION_REFERENCE_RE = re.compile(
    r"(?:교재|책|원문)\s+(?:그림|표)\s*"
    r"[1-9][0-9]*(?:\.[0-9]+)?"
    r"(?:\s*(?:[-–·,]\s*[1-9][0-9]*(?:\.[0-9]+)?)*)?"
)
MERGE_MARKER_RE = re.compile(r"(?m)^(?:<<<<<<<(?: .*)?|=======|>>>>>>>(?: .*)?)$")
STANDALONE_CSS_PLUS_RE = re.compile(r"(?m)^\s*\+\s*$")
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;}]+)", re.IGNORECASE)
FONT_ATTRIBUTE_RE = re.compile(r"""font-family\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_RULE_RE = re.compile(r"([^{}]*)\{([^{}]*)\}")
CJK_WRAP_DECLARATIONS = (
    ("word-break: keep-all", re.compile(r"word-break\s*:\s*keep-all", re.IGNORECASE)),
    (
        "overflow-wrap: break-word",
        re.compile(r"overflow-wrap\s*:\s*break-word", re.IGNORECASE),
    ),
)

FONT_STACK_DRIFT_ALLOWLIST: set[str] = set()


@dataclass
class FigureTrace:
    element_id: str
    required: bool
    image_sources: set[str] = field(default_factory=set)
    has_accessible_visual: bool = False
    caption_parts: list[str] = field(default_factory=list)
    note_parts: list[str] = field(default_factory=list)

    @property
    def caption(self) -> str:
        return " ".join(" ".join(self.caption_parts).split())

    @property
    def note(self) -> str:
        return " ".join(" ".join(self.note_parts).split())


@dataclass
class ReportReferenceTrace:
    target: str
    text_parts: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(" ".join(self.text_parts).split())


@dataclass
class SourceAnchorTrace:
    kind: str
    ref: str
    element_id: str
    tag: str
    text_parts: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(" ".join(self.text_parts).split())


@dataclass
class SlideTrace:
    label: str
    refs: list[str]
    source_refs: list[str]
    source_title_ref: str = ""
    figure_comparison: str = ""
    visual_adaptation: str = ""
    code_blocks_with_language: list[bool] = field(default_factory=list)
    image_sources: set[str] = field(default_factory=set)
    report_links: set[str] = field(default_factory=set)
    report_references: list[ReportReferenceTrace] = field(default_factory=list)
    text_parts: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(" ".join(self.text_parts).split())


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str, str]] = []
        self.images_without_alt = 0
        self.has_title = False
        self.has_viewport = False
        self.has_icon = False
        self.html_lang = ""
        self.forms = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value or "" for name, value in attrs}
        if tag == "html":
            self.html_lang = values.get("lang", "")
        elif tag == "title":
            self.has_title = True
        elif tag == "meta" and values.get("name", "").lower() == "viewport":
            self.has_viewport = True
        elif tag == "link" and "icon" in values.get("rel", "").lower().split():
            self.has_icon = True
        elif tag == "img" and "alt" not in values:
            self.images_without_alt += 1
        elif tag == "form":
            self.forms += 1

        for attribute in ("href", "src", "poster", "action"):
            if attribute in values and values[attribute]:
                self.references.append((tag, attribute, values[attribute]))


class ReportDeckTraceParser(HTMLParser):
    """Collect report assets and the deck evidence that derives from them."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.report_sections: set[str] = set()
        self.required_figures: set[str] = set()
        self.required_figures_without_id = 0
        self.figures: dict[str, FigureTrace] = {}
        self.caption_numbers: dict[str, list[int]] = {"그림": [], "표": []}
        self.caption_labels_by_id: dict[str, tuple[str, int]] = {}
        self.invalid_caption_chips: list[str] = []
        self.internal_report_references: list[ReportReferenceTrace] = []
        self.unlinked_report_text_parts: list[str] = []
        self.slides: list[SlideTrace] = []
        self.source_anchors: dict[tuple[str, str], SourceAnchorTrace] = {}
        self.source_anchor_order: list[tuple[str, str]] = []
        self.duplicate_source_anchors: set[tuple[str, str]] = set()
        self.invalid_source_anchors: list[str] = []
        self.deck_report_source = ""
        self._current_figure: FigureTrace | None = None
        self._current_slide: SlideTrace | None = None
        self._section_depth = 0
        self._slide_section_depth = 0
        self._in_figure_caption = False
        self._in_asset_note = False
        self._caption_chip_parts: list[str] | None = None
        self._caption_owner_id = ""
        self._current_table_id = ""
        self._current_report_reference: ReportReferenceTrace | None = None
        self._active_source_anchors: list[tuple[str, SourceAnchorTrace]] = []
        self._report_text_section_depth = 0
        self._in_table_caption = False
        self._active_slide_pre_language: bool | None = None
        self._active_slide_pre_child_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value or "" for name, value in attrs}
        classes = set(values.get("class", "").split())
        element_id = values.get("id", "").strip()
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)

        source_kind = values.get("data-source-kind", "").strip()
        source_ref = values.get("data-source-ref", "").strip()
        if source_kind or source_ref:
            if source_kind not in SOURCE_KINDS or not source_ref or not element_id:
                self.invalid_source_anchors.append(
                    f"tag={tag!r}, id={element_id!r}, kind={source_kind!r}, "
                    f"ref={source_ref!r}"
                )
            else:
                key = (source_kind, source_ref)
                if key in self.source_anchors:
                    self.duplicate_source_anchors.add(key)
                trace = SourceAnchorTrace(
                    kind=source_kind,
                    ref=source_ref,
                    element_id=element_id,
                    tag=tag,
                )
                self.source_anchors[key] = trace
                self.source_anchor_order.append(key)
                self._active_source_anchors.append((tag, trace))

        if tag == "main" and values.get("data-report-source"):
            self.deck_report_source = values["data-report-source"].strip()
        if tag == "section":
            self._section_depth += 1
            if "slide" in classes:
                self._current_slide = SlideTrace(
                    label=values.get("aria-label", "").strip(),
                    refs=values.get("data-report-refs", "").split(),
                    source_refs=values.get("data-source-refs", "").split(),
                    source_title_ref=values.get("data-source-title", "").strip(),
                    figure_comparison=values.get(
                        "data-figure-comparison", ""
                    ).strip(),
                    visual_adaptation=values.get(
                        "data-report-visual-adaptation", ""
                    ).strip(),
                )
                self._slide_section_depth = self._section_depth
                self.slides.append(self._current_slide)
            if "report-section" in classes and element_id:
                self.report_sections.add(element_id)
                self._report_text_section_depth = self._section_depth

        if tag == "figure" and "report-figure" in classes:
            required = values.get("data-deck-use") == "required"
            if required and not element_id:
                self.required_figures_without_id += 1
            self._current_figure = FigureTrace(element_id, required)
            if element_id:
                self.figures[element_id] = self._current_figure
                if required:
                    self.required_figures.add(element_id)
        elif tag == "figcaption" and self._current_figure is not None:
            self._in_figure_caption = True
        elif tag == "small" and "asset-note" in classes and self._current_figure is not None:
            self._in_asset_note = True
        elif tag == "table":
            self._current_table_id = element_id
        elif tag == "caption":
            self._in_table_caption = True

        if tag == "span" and "asset-caption__chip" in classes:
            self._caption_chip_parts = []
            self._caption_owner_id = (
                self._current_figure.element_id
                if self._current_figure is not None
                else self._current_table_id
            )

        if tag == "img":
            source = values.get("src", "").strip()
            if self._current_figure is not None:
                if source:
                    self._current_figure.image_sources.add(source)
                if values.get("alt", "").strip():
                    self._current_figure.has_accessible_visual = True
            if self._current_slide is not None and source:
                self._current_slide.image_sources.add(source)
        elif (
            tag == "svg"
            and self._current_figure is not None
            and values.get("role") == "img"
            and values.get("aria-label", "").strip()
        ):
            self._current_figure.has_accessible_visual = True

        if tag == "pre" and self._current_slide is not None:
            self._active_slide_pre_language = bool(
                values.get("data-code-language", "").strip()
                or any(name.startswith("language-") for name in classes)
            )
            self._active_slide_pre_child_depth = 0
        elif self._active_slide_pre_language is not None:
            if tag == "code" and self._active_slide_pre_child_depth == 0:
                self._active_slide_pre_language = (
                    self._active_slide_pre_language
                    or bool(values.get("data-code-language", "").strip())
                    or any(name.startswith("language-") for name in classes)
                )
            self._active_slide_pre_child_depth += 1

        if tag == "a" and self._current_slide is not None:
            parsed = urlparse(values.get("href", "").strip())
            if parsed.path == "report.html" and parsed.fragment:
                target = unquote(parsed.fragment)
                self._current_slide.report_links.add(target)
                if "report-ref" in classes:
                    self._current_report_reference = ReportReferenceTrace(target=target)
                    self._current_slide.report_references.append(
                        self._current_report_reference
                    )
        elif tag == "a" and "asset-ref" in classes:
            parsed = urlparse(values.get("href", "").strip())
            if not parsed.path and parsed.fragment:
                self._current_report_reference = ReportReferenceTrace(
                    target=unquote(parsed.fragment)
                )
                self.internal_report_references.append(
                    self._current_report_reference
                )

    def handle_data(self, data: str) -> None:
        if self._caption_chip_parts is not None:
            self._caption_chip_parts.append(data)
        if self._in_figure_caption and self._current_figure is not None:
            self._current_figure.caption_parts.append(data)
        if self._in_asset_note and self._current_figure is not None:
            self._current_figure.note_parts.append(data)
        if self._current_report_reference is not None:
            self._current_report_reference.text_parts.append(data)
        for _, source_anchor in self._active_source_anchors:
            source_anchor.text_parts.append(data)
        if self._current_slide is not None:
            self._current_slide.text_parts.append(data)
        if (
            self._report_text_section_depth
            and not self._in_figure_caption
            and not self._in_table_caption
            and not self._in_asset_note
            and self._caption_chip_parts is None
            and self._current_report_reference is None
        ):
            self.unlinked_report_text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre" and self._active_slide_pre_language is not None:
            if self._current_slide is not None:
                self._current_slide.code_blocks_with_language.append(
                    self._active_slide_pre_language
                )
            self._active_slide_pre_language = None
            self._active_slide_pre_child_depth = 0
        elif self._active_slide_pre_language is not None:
            self._active_slide_pre_child_depth = max(
                0, self._active_slide_pre_child_depth - 1
            )

        if tag == "span" and self._caption_chip_parts is not None:
            chip = " ".join(" ".join(self._caption_chip_parts).split())
            match = CAPTION_NUMBER_RE.fullmatch(chip)
            if match:
                label = (match.group(1), int(match.group(2)))
                self.caption_numbers[label[0]].append(label[1])
                if self._caption_owner_id:
                    self.caption_labels_by_id[self._caption_owner_id] = label
            elif chip:
                self.invalid_caption_chips.append(chip)
            self._caption_chip_parts = None
            self._caption_owner_id = ""
        elif tag == "figcaption":
            self._in_figure_caption = False
        elif tag == "small":
            self._in_asset_note = False
        elif tag == "caption":
            self._in_table_caption = False
        elif tag == "figure":
            self._current_figure = None
            self._in_figure_caption = False
            self._in_asset_note = False
        elif tag == "table":
            self._current_table_id = ""
        elif tag == "a":
            self._current_report_reference = None
        elif tag == "section":
            if self._section_depth == self._report_text_section_depth:
                self._report_text_section_depth = 0
            if (
                self._current_slide is not None
                and self._section_depth == self._slide_section_depth
            ):
                self._current_slide = None
                self._slide_section_depth = 0
            self._section_depth = max(0, self._section_depth - 1)

        for index in range(len(self._active_source_anchors) - 1, -1, -1):
            source_tag, _ = self._active_source_anchors[index]
            if source_tag == tag:
                del self._active_source_anchors[index]
                break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--site", type=Path, default=DEFAULT_SITE)
    parser.add_argument(
        "--check-materials",
        action="store_true",
        help="Also require every registry materials_path to exist locally.",
    )
    parser.add_argument(
        "--print-source-outline",
        type=Path,
        metavar="PRESENTATION_TOML",
        help=(
            "Print the source coordinates (kind, ref, exact title) this validator "
            "expects for a session, in source order, then exit."
        ),
    )
    return parser.parse_args()


def load_toml(path: Path, errors: list[str]) -> dict:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except FileNotFoundError:
        errors.append(f"missing TOML file: {path}")
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"invalid TOML in {path}: {exc}")
    return {}


def normalize_source_title(value: str) -> str:
    """Normalize light Markdown used in source captions without rewriting it."""
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("\\_", "_")
    value = re.sub(r"[`*_]", "", value)
    return " ".join(value.strip().split())


def source_caption_title(value: str) -> str:
    """Return the exact caption title without its explanatory tail.

    Source captions can wrap across Markdown lines and continue for several
    sentences. The public artifact keeps the coordinate and first complete
    sentence verbatim; later sentences belong in independently written prose.
    """
    normalized = normalize_source_title(value)
    first_sentence = re.match(r"^(.+?[.!?])(?:\s|$)", normalized)
    return first_sentence.group(1) if first_sentence else normalized


def parse_source_outline(
    path: Path,
    outline_style: str | None = None,
    exercise_style: str | None = None,
) -> dict[tuple[str, str], str]:
    """Read learning coordinates from a translated/explained chapter.

    The default contract follows explicitly numbered headings. Some books use
    ordered prose headings instead, so ``ordered-headings-v1`` assigns stable
    chapter-derived coordinates while preserving the headings verbatim.
    """
    result: dict[tuple[str, str], str] = {}
    current_section = "chapter"
    exercise_counts: dict[str, int] = {}
    section_re = re.compile(r"^#{1,6}\s+(\d+(?:\.\d+)+)\s+(.+?)\s*$")
    named_re = re.compile(
        r"^(?:#{1,6}\s+)?(Listing|리스팅|목록|Example|예제|Box|상자)\s+"
        r"(\d+\.\d+)(?:\s*[:—-]\s*|\s+)(.+?)\s*$",
        re.IGNORECASE,
    )
    caption_re = re.compile(
        r"^(그림|Figure|표|Table)\s+(\d+\.\d+)\s+(.+?)\s*$",
        re.IGNORECASE,
    )
    exercise_re = re.compile(r"^#{1,6}\s+(?:Exercise\s*\(연습문제\)|연습문제)(?:\s*[—-]\s*)?(.+?)\s*$", re.IGNORECASE)
    bold_numbered_exercise_re = re.compile(
        r"^\*\*(\d+\.\d+)\.\*\*\s+(.+?)\s*$"
    )
    heading_re = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
    chapter_number_re = re.compile(r"^#\s+.*?\b(\d+)\b")
    explicit_h2_re = re.compile(r"^(\d+)[.)]\s+(.+)$")
    explicit_h3_re = re.compile(r"^(\d+)[-.)](\d+)\)?\s+(.+)$")
    appendix_titles = {"요약", "연습문제", "핵심 용어 정리"}

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    path_chapter_match = re.search(r"chapter[_ -]?0*(\d+)", str(path), re.IGNORECASE)
    chapter_number = path_chapter_match.group(1) if path_chapter_match else "1"
    for raw_line in lines:
        chapter_match = chapter_number_re.match(raw_line.strip())
        if chapter_match:
            chapter_number = chapter_match.group(1)
            break
    h2_index = 0
    h3_index = 0
    ordered_parent_section = f"{chapter_number}.0"
    skip_ordered_section = False
    in_numbered_exercises = False
    line_index = 0
    while line_index < len(lines):
        raw_line = lines[line_index]
        line = raw_line.strip()
        match = section_re.match(line)
        if match:
            current_section = match.group(1)
            result[("section", current_section)] = normalize_source_title(match.group(2))
            line_index += 1
            continue
        match = named_re.match(line)
        if match:
            raw_kind, source_ref, title = match.groups()
            kind = {
                "listing": "listing",
                "리스팅": "listing",
                "목록": "listing",
                "example": "example",
                "예제": "example",
                "box": "box",
                "상자": "box",
            }[raw_kind.lower() if raw_kind.isascii() else raw_kind]
            result[(kind, source_ref)] = normalize_source_title(title)
            line_index += 1
            continue
        match = caption_re.match(line)
        if match:
            raw_kind, source_ref, title = match.groups()
            kind = "figure" if raw_kind.lower() in {"그림", "figure"} else "table"
            caption_lines = [title]
            continuation_index = line_index + 1
            while continuation_index < len(lines):
                continuation = lines[continuation_index].strip()
                if not continuation:
                    break
                if (
                    continuation.startswith(
                        ("#", "![](", "```", "---", "|", "<table")
                    )
                    or section_re.match(continuation)
                    or named_re.match(continuation)
                    or caption_re.match(continuation)
                ):
                    break
                caption_lines.append(continuation)
                continuation_index += 1
            result[(kind, source_ref)] = source_caption_title(
                " ".join(caption_lines)
            )
            line_index = continuation_index
            continue
        match = exercise_re.match(line)
        if match:
            exercise_counts[current_section] = exercise_counts.get(current_section, 0) + 1
            source_ref = f"{current_section}-{exercise_counts[current_section]}"
            result[("exercise", source_ref)] = normalize_source_title(match.group(1))
            line_index += 1
            continue
        if exercise_style == "bold-numbered-v1" and in_numbered_exercises:
            match = bold_numbered_exercise_re.match(line)
            if match:
                source_ref = match.group(1)
                result[("exercise", source_ref)] = f"연습문제 {source_ref}"
                line_index += 1
                continue
        if outline_style == "ordered-headings-v1":
            match = heading_re.match(line)
            if match:
                hashes, raw_title = match.groups()
                title = normalize_source_title(raw_title)
                if len(hashes) == 2:
                    in_numbered_exercises = title == "연습문제"
                    skip_ordered_section = (
                        title in appendix_titles or title.startswith("주석")
                    )
                    if skip_ordered_section:
                        line_index += 1
                        continue
                    h3_index = 0
                    explicit = explicit_h2_re.match(title)
                    if title.startswith(("들어가며", "도입")):
                        source_ref = f"{chapter_number}.0"
                    elif explicit:
                        source_ref = f"{chapter_number}.{explicit.group(1)}"
                        title = normalize_source_title(explicit.group(2))
                    else:
                        h2_index += 1
                        source_ref = f"{chapter_number}.{h2_index}"
                    current_section = source_ref
                    ordered_parent_section = source_ref
                    result[("section", source_ref)] = title
                elif not skip_ordered_section:
                    # Boxes and examples are independently traceable named
                    # coordinates and must not be counted twice as sections.
                    if not named_re.match(line):
                        h3_index += 1
                        explicit = explicit_h3_re.match(title)
                        if explicit:
                            source_ref = (
                                f"{chapter_number}.{explicit.group(1)}.{explicit.group(2)}"
                            )
                            title = normalize_source_title(explicit.group(3))
                        else:
                            source_ref = f"{ordered_parent_section}.{h3_index}"
                        result[("section", source_ref)] = title
        line_index += 1
    return result


def parse_source_chapter_title(path: Path) -> str:
    """Return the exact translated chapter title without explainer suffixes."""
    heading_re = re.compile(r"^#\s+(.+?)\s*$")
    suffix_re = re.compile(
        r"(?:\s*[—-]\s*(?:쉬운\s+)?해설판|\s*\((?:쉬운\s+)?해설판\))\s*$"
    )
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = heading_re.match(raw_line.strip())
        if match:
            return normalize_source_title(suffix_re.sub("", match.group(1)))
    return ""


def print_source_outline(metadata_path: Path, stream=None) -> int:
    """Print the coordinates this validator expects, in source order.

    Authors run this before writing a source-fidelity report so the section,
    figure, table and exercise coordinates come from the same parser the gate
    uses instead of from a guess. Output is one ``kind\tref\ttitle`` row per
    coordinate followed by a ``total\tN`` row.
    """
    stream = sys.stdout if stream is None else stream
    errors: list[str] = []
    metadata = load_toml(metadata_path, errors)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1

    source_material = metadata.get("source_material")
    if not isinstance(source_material, str) or not source_material:
        print(f"ERROR: source_material is required in {metadata_path}", file=sys.stderr)
        return 1

    outline_style = metadata.get("source_outline_style")
    if outline_style not in (None, "ordered-headings-v1"):
        print(
            f"ERROR: unknown source_outline_style in {metadata_path}: {outline_style!r}",
            file=sys.stderr,
        )
        return 1
    exercise_style = metadata.get("source_exercise_style")
    if exercise_style not in (None, "bold-numbered-v1"):
        print(
            f"ERROR: unknown source_exercise_style in {metadata_path}: {exercise_style!r}",
            file=sys.stderr,
        )
        return 1

    source_path = (REPO_ROOT / source_material).resolve()
    if not source_path.is_file():
        print(
            f"ERROR: source_material does not exist for {metadata_path}: {source_material}",
            file=sys.stderr,
        )
        return 1

    outline = parse_source_outline(source_path, outline_style, exercise_style)
    for (kind, source_ref), title in outline.items():
        print(f"{kind}\t{source_ref}\t{title}", file=stream)
    print(f"total\t{len(outline)}", file=stream)
    return 0


def validate_source_fidelity(
    metadata: dict,
    study: dict,
    report_trace: ReportDeckTraceParser,
    deck_trace: ReportDeckTraceParser,
    report_html: Path,
    deck_html: Path,
    errors: list[str],
    warnings: list[str] | None = None,
) -> None:
    fidelity = metadata.get("source_fidelity")
    source_material = metadata.get("source_material")
    if not fidelity and not source_material:
        return
    if fidelity != SOURCE_FIDELITY_VERSION:
        errors.append(
            f"source_fidelity must be {SOURCE_FIDELITY_VERSION!r} in "
            f"{report_html.parent / 'presentation.toml'}"
        )
        return
    if not isinstance(source_material, str) or not source_material:
        errors.append(f"source_material is required for source fidelity in {report_html}")
        return

    relative = Path(source_material)
    source_path = (REPO_ROOT / relative).resolve()
    materials_root = (REPO_ROOT / str(study.get("materials_path", ""))).resolve()
    if relative.is_absolute() or not within(source_path, materials_root):
        errors.append(
            f"source_material must remain under the study materials_path in "
            f"{report_html}: {source_material!r}"
        )
        return
    if not materials_root.is_dir():
        # 교재는 참가자 공개 저장소에 있다. 그 저장소를 함께 체크아웃하지
        # 않은 환경에서는 좌표 대조를 할 수 없으므로 경로 형식만 확인한다.
        # 교재를 실제로 요구하려면 --check-materials 를 쓴다.
        if warnings is not None:
            warnings.append(
                f"source-fidelity comparison skipped because materials_path is "
                f"not available for {report_html}: {materials_root}"
            )
        return
    if not source_path.is_file():
        errors.append(f"source_material does not exist for {report_html}: {source_material}")
        return

    outline_style = metadata.get("source_outline_style")
    if outline_style not in (None, "ordered-headings-v1"):
        errors.append(
            f"unknown source_outline_style in {report_html.parent / 'presentation.toml'}: "
            f"{outline_style!r}"
        )
        return
    exercise_style = metadata.get("source_exercise_style")
    if exercise_style not in (None, "bold-numbered-v1"):
        errors.append(
            f"unknown source_exercise_style in {report_html.parent / 'presentation.toml'}: "
            f"{exercise_style!r}"
        )
        return
    expected = parse_source_outline(source_path, outline_style, exercise_style)
    expected_chapter_title = parse_source_chapter_title(source_path)
    actual = report_trace.source_anchors
    if not expected:
        errors.append(f"source_material has no traceable learning coordinates: {source_path}")
        return
    metadata_title = normalize_source_title(str(metadata.get("title", "")))
    metadata_title = re.sub(
        r"^Chapter\s+\d+(?:\.\d+)*\.\s*", "", metadata_title, flags=re.IGNORECASE
    )
    if not expected_chapter_title:
        errors.append(f"source_material has no chapter title: {source_path}")
    elif metadata_title != expected_chapter_title:
        errors.append(
            f"presentation title differs from source chapter title in "
            f"{report_html.parent / 'presentation.toml'}: "
            f"expects {expected_chapter_title!r}, found {metadata_title!r}"
        )
    for item in report_trace.invalid_source_anchors:
        errors.append(f"invalid source anchor in {report_html}: {item}")
    for key in sorted(report_trace.duplicate_source_anchors):
        errors.append(f"duplicate source anchor in {report_html}: {key[0]}:{key[1]}")

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing:
        errors.append(
            f"report structure is missing coordinate(s) in {report_html}: "
            f"{[f'{kind}:{ref}' for kind, ref in missing]}"
        )
    if extra:
        errors.append(
            f"report structure has unknown coordinate(s) in {report_html}: "
            f"{[f'{kind}:{ref}' for kind, ref in extra]}"
        )

    for key in sorted(set(expected) & set(actual)):
        item = actual[key]
        expected_title = expected[key]
        if expected_title not in normalize_source_title(item.text):
            errors.append(
                f"source anchor title differs from source in {report_html}: "
                f"{key[0]}:{key[1]} expects {expected_title!r}, found {item.text!r}"
            )

    expected_order = list(expected)
    actual_order = [key for key in report_trace.source_anchor_order if key in expected]
    if not missing and not extra and actual_order != expected_order:
        errors.append(
            f"report source coordinates are out of source order in {report_html}: "
            f"{[f'{kind}:{ref}' for kind, ref in actual_order]}"
        )

    deck_refs: set[tuple[str, str]] = set()
    title_slides: dict[tuple[str, str], list[SlideTrace]] = {}
    for slide in deck_trace.slides:
        for token in slide.source_refs:
            if ":" not in token:
                errors.append(
                    f"invalid data-source-refs token in {deck_html} "
                    f"({slide.label or 'unnamed slide'}): {token!r}"
                )
                continue
            kind, source_ref = token.split(":", 1)
            key = (kind, source_ref)
            if key not in expected:
                errors.append(
                    f"deck references unknown source coordinate in {deck_html} "
                    f"({slide.label or 'unnamed slide'}): {token}"
                )
                continue
            deck_refs.add(key)
            expected_title = expected[key]
            coordinate_is_visible = source_ref in slide.text
            if outline_style == "ordered-headings-v1" and kind == "section":
                coordinate_is_visible = (
                    coordinate_is_visible
                    or expected_title in normalize_source_title(slide.text)
                )
            if not coordinate_is_visible:
                errors.append(
                    f"deck source coordinate must be visible in {deck_html} "
                    f"({slide.label or 'unnamed slide'}): {token}"
                )

        if slide.source_title_ref:
            if ":" not in slide.source_title_ref:
                errors.append(
                    f"invalid data-source-title token in {deck_html} "
                    f"({slide.label or 'unnamed slide'}): "
                    f"{slide.source_title_ref!r}"
                )
            else:
                kind, source_ref = slide.source_title_ref.split(":", 1)
                key = (kind, source_ref)
                if kind != "section" or key not in expected:
                    errors.append(
                        f"data-source-title must name a source section in "
                        f"{deck_html} ({slide.label or 'unnamed slide'}): "
                        f"{slide.source_title_ref}"
                    )
                else:
                    title_slides.setdefault(key, []).append(slide)
                    if slide.source_title_ref not in slide.source_refs:
                        errors.append(
                            f"data-source-title must also appear in data-source-refs "
                            f"in {deck_html} ({slide.label or 'unnamed slide'}): "
                            f"{slide.source_title_ref}"
                        )

        figure_refs = {
            token for token in slide.source_refs if token.startswith("figure:")
        }
        if (
            len(figure_refs) > 1
            and slide.figure_comparison != "intentional"
        ):
            errors.append(
                f"slide references multiple source figures without an intentional "
                f"comparison marker in {deck_html} "
                f"({slide.label or 'unnamed slide'}): {sorted(figure_refs)}"
            )
        for has_language in slide.code_blocks_with_language:
            if not has_language:
                errors.append(
                    f"deck code block lacks a language marker on <pre> or its "
                    f"direct <code> in {deck_html} "
                    f"({slide.label or 'unnamed slide'})"
                )

    expected_sections = {key for key in expected if key[0] == "section"}
    missing_deck_sections = sorted(expected_sections - deck_refs)
    if missing_deck_sections:
        errors.append(
            f"deck does not cover source section coordinate(s) in {deck_html}: "
            f"{[f'{kind}:{ref}' for kind, ref in missing_deck_sections]}"
        )

    for key in sorted(expected_sections):
        slides = title_slides.get(key, [])
        if len(slides) != 1:
            errors.append(
                f"deck must declare exactly one data-source-title for "
                f"{key[0]}:{key[1]} in {deck_html}: found {len(slides)}"
            )
            continue
        expected_title = expected[key]
        if expected_title not in normalize_source_title(slides[0].text):
            errors.append(
                f"deck source title differs from source in {deck_html} "
                f"({slides[0].label or 'unnamed slide'}): {key[0]}:{key[1]} "
                f"expects {expected_title!r}, found {slides[0].text!r}"
            )

    required_source_figures = {
        key
        for key, anchor in report_trace.source_anchors.items()
        if key[0] == "figure" and anchor.element_id in report_trace.required_figures
    }
    missing_required_source_figures = sorted(required_source_figures - deck_refs)
    if missing_required_source_figures:
        errors.append(
            f"deck does not cover required source figure coordinate(s) in "
            f"{deck_html}: "
            f"{[f'{kind}:{ref}' for kind, ref in missing_required_source_figures]}"
        )


def within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def normalize_font_stack(value: str) -> tuple[str, ...]:
    return tuple(
        part.strip().strip("\"'").lower()
        for part in value.replace("\n", " ").split(",")
        if part.strip()
    )


def report_font_stack(css_text: str) -> tuple[str, ...]:
    variable = re.search(r"--font-sans-ko\s*:\s*([^;]+);", css_text, re.IGNORECASE)
    if variable:
        return normalize_font_stack(variable.group(1))
    body = re.search(
        r"\bbody\s*\{[^}]*font-family\s*:\s*([^;]+);",
        css_text,
        re.IGNORECASE | re.DOTALL,
    )
    return normalize_font_stack(body.group(1)) if body else ()


def svg_primary_font_stack(svg_text: str) -> tuple[str, ...]:
    for pattern in (
        r"\.t\s*\{[^}]*font-family\s*:\s*([^;}]+)",
        r"\.text\s*\{[^}]*font-family\s*:\s*([^;}]+)",
        r"\btext\s*\{[^}]*font-family\s*:\s*([^;}]+)",
    ):
        match = re.search(pattern, svg_text, re.IGNORECASE | re.DOTALL)
        if match:
            return normalize_font_stack(match.group(1))
    for declaration in FONT_FAMILY_RE.finditer(svg_text):
        stack = normalize_font_stack(declaration.group(1))
        # A code-label class can legitimately use a mono face before the
        # diagram's default text class is declared. It is not the SVG's
        # primary Korean font contract, so continue to the next declaration.
        if "monospace" not in stack:
            return stack
    attribute = FONT_ATTRIBUTE_RE.search(svg_text)
    return normalize_font_stack(attribute.group(1)) if attribute else ()


def validate_caption_sequence(
    trace: ReportDeckTraceParser, report_html: Path, errors: list[str]
) -> None:
    for chip in trace.invalid_caption_chips:
        errors.append(f"invalid report caption number in {report_html}: {chip!r}")
    for kind, numbers in trace.caption_numbers.items():
        expected = list(range(1, len(numbers) + 1))
        if numbers != expected:
            errors.append(
                f"report {kind} caption numbers must be consecutive 1..N in "
                f"{report_html}: found {numbers}, expected {expected}"
            )


def extract_caption_references(text: str) -> set[tuple[str, int]]:
    """Expand visible report labels such as '그림 1–3' and '표 2·4'.

    Decimal source labels such as '교재 표 3.3' are deliberately ignored because
    they identify the book's assets, not this report's caption sequence.
    """
    references: set[tuple[str, int]] = set()
    report_text = EXTERNAL_CAPTION_REFERENCE_RE.sub("", text)
    for match in CAPTION_REFERENCE_GROUP_RE.finditer(report_text):
        kind, specification = match.groups()
        for part in re.split(r"\s*[·,]\s*", specification):
            bounds = re.split(r"\s*[-–]\s*", part)
            if len(bounds) == 1:
                references.add((kind, int(bounds[0])))
                continue
            if len(bounds) == 2:
                start, end = (int(value) for value in bounds)
                step = 1 if end >= start else -1
                references.update(
                    (kind, number) for number in range(start, end + step, step)
                )
    return references


def validate_internal_report_references(
    trace: ReportDeckTraceParser, report_html: Path, errors: list[str]
) -> None:
    for report_reference in trace.internal_report_references:
        expected = trace.caption_labels_by_id.get(report_reference.target)
        if expected is None:
            errors.append(
                f"internal report asset reference targets an id without a caption "
                f"label in {report_html}: #{report_reference.target}"
            )
            continue
        visible = extract_caption_references(report_reference.text)
        if visible != {expected}:
            expected_text = f"{expected[0]} {expected[1]}"
            found_text = (
                ", ".join(f"{kind} {number}" for kind, number in sorted(visible))
                if visible
                else "<missing>"
            )
            errors.append(
                f"internal report caption reference is stale in {report_html}: "
                f"#{report_reference.target} expects {expected_text}, found "
                f"{found_text} in {report_reference.text!r}"
            )
    unlinked = extract_caption_references(" ".join(trace.unlinked_report_text_parts))
    if unlinked:
        found_text = ", ".join(
            f"{kind} {number}" for kind, number in sorted(unlinked)
        )
        errors.append(
            f"internal report caption reference must use an asset-ref anchor in "
            f"{report_html}: {found_text}"
        )


def validate_unique_source_figure_assets(
    trace: ReportDeckTraceParser, report_html: Path, errors: list[str]
) -> None:
    """Distinct textbook figures must not be caption-only aliases of one image.

    A source-aligned report can legitimately redraw an original figure, but every
    source coordinate still represents a distinct learning asset. Reusing one
    ``src`` (or copying the same bytes under another name) hides semantic
    differences such as stage highlighting, process versus result, or a changed
    graph state while the captions misleadingly claim that the visuals differ.
    """
    source_uses: dict[str, list[str]] = {}
    content_uses: dict[str, list[tuple[str, str]]] = {}
    session_root = report_html.parent.resolve()

    for (kind, source_ref), anchor in trace.source_anchors.items():
        if kind != "figure":
            continue
        figure = trace.figures.get(anchor.element_id)
        if figure is None:
            continue
        for source in sorted(figure.image_sources):
            source_uses.setdefault(source, []).append(source_ref)
            parsed = urlparse(source)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            asset_path = (report_html.parent / unquote(parsed.path)).resolve()
            if not within(asset_path, session_root) or not asset_path.is_file():
                continue
            digest = hashlib.sha256(asset_path.read_bytes()).hexdigest()
            content_uses.setdefault(digest, []).append((source_ref, source))

    for source, refs in sorted(source_uses.items()):
        unique_refs = sorted(set(refs))
        if len(unique_refs) > 1:
            errors.append(
                f"distinct source figures reuse the same image src in {report_html}: "
                f"{source} -> {[f'figure:{ref}' for ref in unique_refs]}"
            )

    for uses in content_uses.values():
        refs = sorted({source_ref for source_ref, _ in uses})
        sources = sorted({source for _, source in uses})
        if len(refs) > 1 and len(sources) > 1:
            errors.append(
                f"distinct source figures use byte-identical image files in "
                f"{report_html}: {sources} -> {[f'figure:{ref}' for ref in refs]}"
            )


def validate_deck_visual_provenance(
    report_trace: ReportDeckTraceParser,
    deck_trace: ReportDeckTraceParser,
    deck_html: Path,
    errors: list[str],
) -> None:
    """Require every deck image to exist in the report or name its adaptation source."""
    report_sources = {
        source
        for figure in report_trace.figures.values()
        for source in figure.image_sources
    }
    report_figure_ids = set(report_trace.figures)

    for slide in deck_trace.slides:
        deck_only = sorted(slide.image_sources - report_sources)
        if not deck_only:
            continue
        source_figures = set(slide.refs) & report_figure_ids
        linked_source_figures = slide.report_links & source_figures
        if (
            slide.visual_adaptation == "intentional"
            and source_figures
            and linked_source_figures
        ):
            continue
        errors.append(
            f"deck image must first appear in the report or declare an intentional "
            f"adaptation linked to a report figure in {deck_html} "
            f"({slide.label or 'unnamed slide'}): {deck_only}"
        )


def normalize_session_asset_source(source: str) -> str | None:
    parsed = urlparse(source)
    if parsed.scheme or parsed.netloc or parsed.path.startswith("/"):
        return None
    path = Path(unquote(parsed.path))
    if not path.parts or ".." in path.parts:
        return None
    return path.as_posix()


def validate_retained_unreferenced_assets(
    metadata: dict,
    session_dir: Path,
    report_trace: ReportDeckTraceParser,
    deck_trace: ReportDeckTraceParser,
    errors: list[str],
) -> None:
    """Require every dormant public SVG to have an explicit retention record."""
    records = metadata.get("retained_unreferenced_assets", [])
    if not isinstance(records, list):
        errors.append(
            f"retained_unreferenced_assets must be an array of tables in "
            f"{session_dir / 'presentation.toml'}"
        )
        records = []

    referenced: set[str] = set()
    sources = {
        item
        for figure in report_trace.figures.values()
        for item in figure.image_sources
    } | {
        item
        for slide in deck_trace.slides
        for item in slide.image_sources
    }
    for source in sources:
        normalized = normalize_session_asset_source(source)
        if normalized:
            referenced.add(normalized)

    figures_dir = session_dir / "assets/figs"
    public_svgs = {
        path.relative_to(session_dir).as_posix()
        for path in figures_dir.glob("*.svg")
        if path.is_file()
    }
    actual_unreferenced = public_svgs - referenced
    declared: set[str] = set()

    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            errors.append(
                f"retained_unreferenced_assets entry {index} must be a table in "
                f"{session_dir / 'presentation.toml'}"
            )
            continue
        path_value = record.get("path")
        reason = record.get("reason")
        normalized = (
            normalize_session_asset_source(path_value)
            if isinstance(path_value, str)
            else None
        )
        if (
            not normalized
            or not normalized.startswith("assets/figs/")
            or not normalized.endswith(".svg")
        ):
            errors.append(
                f"invalid retained unreferenced SVG path in "
                f"{session_dir / 'presentation.toml'}: {path_value!r}"
            )
            continue
        if normalized in declared:
            errors.append(
                f"duplicate retained unreferenced SVG in "
                f"{session_dir / 'presentation.toml'}: {normalized}"
            )
            continue
        declared.add(normalized)
        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                f"retained unreferenced SVG needs a reason in "
                f"{session_dir / 'presentation.toml'}: {normalized}"
            )
        if normalized not in public_svgs:
            errors.append(
                f"retained unreferenced SVG does not exist in {session_dir}: "
                f"{normalized}"
            )
        elif normalized in referenced:
            errors.append(
                f"retention record is stale because the SVG is now referenced in "
                f"{session_dir}: {normalized}"
            )

    undeclared = sorted(actual_unreferenced - declared)
    if undeclared:
        errors.append(
            f"unreferenced public SVG(s) must be removed with user approval or "
            f"declared with a retention reason in {session_dir / 'presentation.toml'}: "
            f"{undeclared}"
        )


def validate_retained_alternate_html(
    metadata: dict,
    session_dir: Path,
    errors: list[str],
) -> None:
    """Require every non-canonical public session HTML file to be auditable."""
    records = metadata.get("retained_alternate_html", [])
    if not isinstance(records, list):
        errors.append(
            f"retained_alternate_html must be an array of tables in "
            f"{session_dir / 'presentation.toml'}"
        )
        records = []

    canonical = {"index.html", "report.html"}
    public_alternates = {
        path.name
        for path in session_dir.glob("*.html")
        if path.is_file() and path.name not in canonical
    }
    declared: set[str] = set()

    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            errors.append(
                f"retained_alternate_html entry {index} must be a table in "
                f"{session_dir / 'presentation.toml'}"
            )
            continue
        path_value = record.get("path")
        reason = record.get("reason")
        normalized = (
            normalize_session_asset_source(path_value)
            if isinstance(path_value, str)
            else None
        )
        if (
            not normalized
            or Path(normalized).name != normalized
            or not normalized.endswith(".html")
            or normalized in canonical
        ):
            errors.append(
                f"invalid retained alternate HTML path in "
                f"{session_dir / 'presentation.toml'}: {path_value!r}"
            )
            continue
        if normalized in declared:
            errors.append(
                f"duplicate retained alternate HTML in "
                f"{session_dir / 'presentation.toml'}: {normalized}"
            )
            continue
        declared.add(normalized)
        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                f"retained alternate HTML needs a reason in "
                f"{session_dir / 'presentation.toml'}: {normalized}"
            )
        if normalized not in public_alternates:
            errors.append(
                f"retained alternate HTML does not exist in {session_dir}: "
                f"{normalized}"
            )

    undeclared = sorted(public_alternates - declared)
    if undeclared:
        errors.append(
            f"non-canonical public session HTML must be removed with user approval or "
            f"declared with a retention reason in {session_dir / 'presentation.toml'}: "
            f"{undeclared}"
        )


def parse_css_declarations(block: str) -> dict[str, str]:
    declarations: dict[str, str] = {}
    for declaration in block.split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        declarations[name.strip().lower()] = value.strip().lower()
    return declarations


def validate_svg_connector_fill_contract(
    session_dir: Path,
    errors: list[str],
) -> None:
    """A marker-ended SVG path is a connector and must not use SVG's black fill."""
    figures_dir = session_dir / "assets" / "figs"
    if not figures_dir.is_dir():
        return

    for svg_path in sorted(figures_dir.glob("*.svg")):
        svg_text = svg_path.read_text(encoding="utf-8", errors="replace")
        class_rules = {
            name: parse_css_declarations(block)
            for name, block in re.findall(
                r"\.([A-Za-z_][\w-]*)\s*\{([^{}]*)\}", svg_text
            )
        }
        try:
            root = ET.fromstring(svg_text)
        except ET.ParseError as exc:
            errors.append(f"invalid SVG XML in {svg_path}: {exc}")
            continue

        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] != "path":
                continue
            declarations: dict[str, str] = {}
            for class_name in element.attrib.get("class", "").split():
                declarations.update(class_rules.get(class_name, {}))
            declarations.update(
                parse_css_declarations(element.attrib.get("style", ""))
            )
            for name in ("stroke", "fill", "marker-end"):
                if name in element.attrib:
                    declarations[name] = element.attrib[name].strip().lower()

            stroke = declarations.get("stroke", "")
            marker_end = declarations.get("marker-end", "")
            fill = declarations.get("fill", "")
            if stroke and stroke != "none" and marker_end and fill != "none":
                element_id = element.attrib.get("id", "<unnamed>")
                errors.append(
                    f"marker-ended SVG path must declare fill:none in {svg_path}: "
                    f"path {element_id} has fill={fill or '<implicit black>'}"
                )


SVG_PROSE_MAX_CHARS = 28
SVG_PROSE_RUN_GAP = 24.0
SVG_PROSE_BASELINE_PATH = (
    REPO_ROOT / "agent-support" / "reviews" / "svg-prose-baseline.json"
)
TRANSLATE_RE = re.compile(r"translate\(\s*(-?[\d.]+)[\s,]+(-?[\d.]+)\s*\)")


def svg_prose_digest(text: str) -> str:
    """Baseline key for one offending string, so a rewrite is a new violation."""
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()[:16]


def load_svg_prose_baseline() -> dict[str, list[str]]:
    if not SVG_PROSE_BASELINE_PATH.is_file():
        return {}
    raw = json.loads(SVG_PROSE_BASELINE_PATH.read_text(encoding="utf-8"))
    return {key: list(value) for key, value in raw.get("allowed", raw).items()}


def _svg_geometry(
    root: ET.Element,
) -> tuple[list[tuple[float, float, float, float]], list[tuple[float, float, str]], bool]:
    """Shape boxes, text anchors, and whether a foreignObject carries text.

    Group `transform="translate(...)"` is composed so text hidden in a shifted
    `<g>` is judged at its rendered position. A `rotate` on text moves no anchor.
    """
    shapes: list[tuple[float, float, float, float]] = []
    texts: list[tuple[float, float, str]] = []
    foreign_text = False

    def number(element: ET.Element, name: str) -> float | None:
        try:
            return float(element.attrib[name])
        except (KeyError, ValueError):
            return None

    def walk(element: ET.Element, dx: float, dy: float) -> None:
        nonlocal foreign_text
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "g":
            match = TRANSLATE_RE.search(element.attrib.get("transform", ""))
            if match:
                dx += float(match.group(1))
                dy += float(match.group(2))
        elif tag == "rect":
            x, y = number(element, "x"), number(element, "y")
            w, h = number(element, "width"), number(element, "height")
            if None not in (x, y, w, h):
                shapes.append((x + dx, y + dy, x + dx + w, y + dy + h))
        elif tag in {"circle", "ellipse"}:
            cx, cy = number(element, "cx"), number(element, "cy")
            rx = number(element, "r") or number(element, "rx")
            ry = number(element, "r") or number(element, "ry")
            if None not in (cx, cy, rx, ry):
                shapes.append((cx + dx - rx, cy + dy - ry, cx + dx + rx, cy + dy + ry))
        elif tag == "foreignObject":
            if "".join(element.itertext()).strip():
                foreign_text = True
            return
        elif tag == "text":
            x, y = number(element, "x"), number(element, "y")
            body = " ".join("".join(element.itertext()).split())
            if body and None not in (x, y):
                texts.append((x + dx, y + dy, body))
            return
        for child in element:
            walk(child, dx, dy)

    walk(root, 0.0, 0.0)
    return shapes, texts, foreign_text


def validate_svg_prose_contract(
    session_dir: Path,
    errors: list[str],
    baseline: dict[str, list[str]] | None = None,
) -> None:
    """A diagram carries decode labels; explanatory prose belongs in the report.

    Axis, tick, legend, node-identity and data-point labels stay inside the SVG
    because a reader cannot decode the figure without them. Titles, footer
    commentary, summary or result panels laid over the diagram, and conclusions
    belong in the adjacent caption or prose. Length is the proxy for that split:
    once ch04 was cleaned, its longest text outside any shape was 27 characters.
    """
    figures_dir = session_dir / "assets" / "figs"
    if not figures_dir.is_dir():
        return
    allowed = load_svg_prose_baseline() if baseline is None else baseline

    for svg_path in sorted(figures_dir.glob("*.svg")):
        svg_text = svg_path.read_text(encoding="utf-8", errors="replace")
        try:
            root = ET.fromstring(svg_text)
        except ET.ParseError:
            continue  # the connector check already reports unparsable SVG
        shapes, texts, foreign_text = _svg_geometry(root)
        key = f"{session_dir.name}/{svg_path.name}"
        excused = set(allowed.get(key, ()))

        if foreign_text:
            errors.append(
                f"SVG must not carry text in a foreignObject in {svg_path}; "
                f"move the prose into the report caption"
            )

        outside = [
            (x, y, body)
            for x, y, body in texts
            if not any(
                left <= x <= right and top - 4 <= y <= bottom + 4
                for left, top, right, bottom in shapes
            )
        ]

        reported: set[str] = set()
        for _, _, body in outside:
            if len(body) < SVG_PROSE_MAX_CHARS or svg_prose_digest(body) in excused:
                continue
            reported.add(body)
            errors.append(
                f"SVG text outside any shape is explanatory prose in {svg_path} "
                f"({len(body)} chars): {body[:60]!r}; keep decode labels only and "
                f"move this into the report caption or prose"
            )

        columns: dict[int, list[tuple[float, str]]] = {}
        for x, y, body in outside:
            columns.setdefault(round(x), []).append((y, body))
        for _, column in sorted(columns.items()):
            column.sort()
            run: list[tuple[float, str]] = []
            for entry in column + [(float("inf"), "")]:
                if run and entry[0] - run[-1][0] > SVG_PROSE_RUN_GAP:
                    total = sum(len(body) for _, body in run)
                    bodies = [body for _, body in run]
                    if (
                        len(run) > 1
                        and total >= SVG_PROSE_MAX_CHARS
                        and not any(body in reported for body in bodies)
                        and not all(svg_prose_digest(b) in excused for b in bodies)
                    ):
                        errors.append(
                            f"SVG 텍스트 묶음이 설명 패널이다 in {svg_path} "
                            f"({len(run)}줄 {total}자): {' / '.join(bodies)[:80]!r}; "
                            f"move it into the report caption or prose"
                        )
                    run = []
                if entry[1]:
                    run.append(entry)


def css_rule_has_contract(
    css_text: str,
    selectors: set[str],
    declarations: tuple[re.Pattern[str], ...],
) -> bool:
    stripped = CSS_COMMENT_RE.sub(" ", css_text)
    for match in CSS_RULE_RE.finditer(stripped):
        actual_selectors = {
            " ".join(selector.split()).lower()
            for selector in match.group(1).split(",")
        }
        if not selectors.issubset(actual_selectors):
            continue
        if all(pattern.search(match.group(2)) for pattern in declarations):
            return True
    return False


def validate_source_fidelity_report_css(
    session_dir: Path,
    errors: list[str],
) -> None:
    """Protect shared report-template contracts while allowing session labels."""
    css_path = session_dir / "assets" / "report.css"
    template_path = (
        REPO_ROOT / "agent-support/templates/study-report/assets/report.css"
    )
    if not css_path.is_file() or not template_path.is_file():
        return
    css_text = css_path.read_text(encoding="utf-8", errors="replace")
    template_text = template_path.read_text(encoding="utf-8", errors="replace")
    expected_font = report_font_stack(template_text)
    actual_font = report_font_stack(css_text)
    if not expected_font or actual_font != expected_font:
        errors.append(
            f"source-fidelity report CSS must retain the template Korean font "
            f"stack in {css_path}: expected {','.join(expected_font) or '<missing>'}, "
            f"found {','.join(actual_font) or '<missing>'}"
        )

    contracts = (
        (
            {
                ".continuous-mode .report-section:not(.s0)",
                ".continuous-mode .report-appendix",
            },
            (
                re.compile(r"break-before\s*:\s*page\s*!important", re.I),
                re.compile(r"page-break-before\s*:\s*always\s*!important", re.I),
            ),
            "print section page breaks",
        ),
        (
            {"h1", "h2", "h3", "h4", "h5", "h6"},
            (
                re.compile(r"break-inside\s*:\s*avoid", re.I),
                re.compile(r"page-break-inside\s*:\s*avoid", re.I),
            ),
            "heading page integrity",
        ),
        (
            {".continuous-mode .report-cover__subtitle"},
            (re.compile(r"word-break\s*:\s*keep-all", re.I),),
            "cover subtitle Korean wrapping",
        ),
    )
    for selectors, declarations, label in contracts:
        if not css_rule_has_contract(css_text, selectors, declarations):
            errors.append(
                f"source-fidelity report CSS is missing the shared {label} "
                f"contract in {css_path}"
            )


def validate_font_stack_contract(
    session_dir: Path,
    session_key: str,
    errors: list[str],
) -> None:
    css_path = session_dir / "assets" / "report.css"
    figures_dir = session_dir / "assets" / "figs"
    if not css_path.is_file() or not figures_dir.is_dir():
        return
    expected = report_font_stack(css_path.read_text(encoding="utf-8", errors="replace"))
    if not expected:
        errors.append(f"report CSS has no readable body font stack: {css_path}")
        return

    drift: list[str] = []
    for svg_path in sorted(figures_dir.glob("*.svg")):
        svg_text = svg_path.read_text(encoding="utf-8", errors="replace")
        if "<text" not in svg_text:
            continue
        actual = svg_primary_font_stack(svg_text)
        if not actual:
            drift.append(f"{svg_path.name}=<missing>")
        elif actual != expected:
            drift.append(f"{svg_path.name}={','.join(actual)}")

    if drift and session_key not in FONT_STACK_DRIFT_ALLOWLIST:
        errors.append(
            f"SVG/report.css font stack mismatch in {session_dir}; expected "
            f"{','.join(expected)}; drift: {drift}"
        )


def body_rule_blocks(css_text: str) -> list[str]:
    """Declaration blocks of every rule whose selector is exactly `body`.

    The rule regex cannot nest, so a `body` rule wrapped in `@media ... { }` is
    reached the same way a top-level one is.
    """
    stripped = CSS_COMMENT_RE.sub(" ", css_text)
    return [
        match.group(2)
        for match in CSS_RULE_RE.finditer(stripped)
        if " ".join(match.group(1).split()).lower() == "body"
    ]


def validate_cjk_wrap_contract(session_dir: Path, errors: list[str]) -> None:
    """Both CJK wrap declarations must sit on `body` so they inherit everywhere.

    Declaring them only on table cells or the cover title leaves section
    headings and paragraphs on the browser default, which breaks Korean
    mid-어절. Declaring `keep-all` without `overflow-wrap: break-word` is the
    banned solo form: it then lets long Latin tokens and URLs overflow.
    """
    for name in ("report.css", "deck.css"):
        css_path = session_dir / "assets" / name
        if not css_path.is_file():
            continue
        blocks = body_rule_blocks(css_path.read_text(encoding="utf-8", errors="replace"))
        missing = [
            declaration
            for declaration, pattern in CJK_WRAP_DECLARATIONS
            if not any(pattern.search(block) for block in blocks)
        ]
        if missing:
            errors.append(
                f"the `body` rule must declare {' and '.join(missing)} in {css_path}"
            )


def validate_registry(
    registry: Path, site: Path, check_materials: bool, errors: list[str]
) -> dict[str, dict]:
    data = load_toml(registry, errors)
    if data.get("schema_version") != 1:
        errors.append(f"unsupported registry schema_version: {registry}")

    studies = data.get("studies", [])
    if not studies:
        errors.append("study registry has no entries")
        return {}

    result: dict[str, dict] = {}
    seen_slugs: set[str] = set()
    for study in studies:
        study_id = study.get("id")
        slug = study.get("slug")
        if not isinstance(study_id, str) or not SLUG_RE.fullmatch(study_id):
            errors.append(f"invalid study id: {study_id!r}")
            continue
        if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
            errors.append(f"invalid study slug for {study_id}: {slug!r}")
            continue
        if study_id in result:
            errors.append(f"duplicate study id: {study_id}")
        if slug in seen_slugs:
            errors.append(f"duplicate study slug: {slug}")
        if study.get("status") not in {"active", "archived"}:
            errors.append(f"invalid status for {study_id}: {study.get('status')!r}")

        track = study.get("track")
        if track not in {"aiml", "quant"}:
            errors.append(f"invalid track for {study_id}: {track!r}")
            continue

        expected_public = f"html/studies/{slug}"
        if study.get("presentation_path") != expected_public:
            errors.append(
                f"presentation_path for {study_id} must remain {expected_public}"
            )

        materials = study.get("materials_path", "")
        archive_path = study.get("archive_path", "")
        if not isinstance(materials, str) or Path(materials).is_absolute() or ".." in Path(materials).parts:
            errors.append(f"invalid materials_path for {study_id}: {materials!r}")
        expected_archive = f"materials/{track}/archive/{slug}"
        if archive_path != expected_archive:
            errors.append(f"invalid archive_path for {study_id}: {archive_path!r}")
        expected_active = f"materials/{track}/active/{slug}"
        if study.get("status") == "active" and materials != expected_active:
            errors.append(
                f"active study {study_id} materials_path must be "
                f"{expected_active}"
            )
        if study.get("status") == "archived" and materials != archive_path:
            errors.append(
                f"archived study {study_id} materials_path must equal archive_path"
            )
        if check_materials and materials and not (REPO_ROOT / materials).is_dir():
            errors.append(f"materials_path does not exist for {study_id}: {materials}")

        public_dir = site / "studies" / slug
        if not (public_dir / "index.html").is_file():
            errors.append(f"missing generated study index: {public_dir / 'index.html'}")
        result[study_id] = study
        seen_slugs.add(slug)
    return result


RAW_MATERIALS_LINK_RE = re.compile(
    r"https://github\.com/[^\"'\s]+/(?:blob|tree)/[^\"'\s]+/materials/"
)


def validate_materials_links(site: Path, errors: list[str]) -> None:
    """교재는 참가자 공개 저장소에 있으므로 raw GitHub 링크는 외부 방문자에게
    404가 된다. 발표자료는 안내 페이지(`/materials/?p=...`)를 거쳐야 한다."""
    for html_path in sorted(site.glob("studies/*/presentations/*/*.html")):
        text = html_path.read_text(encoding="utf-8", errors="replace")
        for match in RAW_MATERIALS_LINK_RE.findall(text):
            errors.append(
                f"textbook link must go through the invitation page "
                f"(../../../../materials/?p=...) in {html_path}: {match}"
            )


def validate_metadata(
    site: Path,
    studies: dict[str, dict],
    errors: list[str],
    warnings: list[str],
) -> None:
    seen: set[tuple[str, str]] = set()
    for metadata_path in sorted(
        site.glob("studies/*/presentations/*/presentation.toml")
    ):
        metadata = load_toml(metadata_path, errors)
        study_id = metadata.get("study_id")
        session_id = metadata.get("session_id")
        if study_id not in studies:
            errors.append(f"unknown study_id in {metadata_path}: {study_id!r}")
            continue
        if not isinstance(session_id, str) or not SLUG_RE.fullmatch(session_id):
            errors.append(f"invalid session_id in {metadata_path}: {session_id!r}")
            continue
        if metadata_path.parent.name != session_id:
            errors.append(
                f"session_id does not match directory in {metadata_path}: {session_id}"
            )
        if metadata_path.parents[2].name != studies[study_id]["slug"]:
            errors.append(f"presentation is under the wrong study: {metadata_path}")
        for field in ("title", "date"):
            if not metadata.get(field):
                errors.append(f"missing {field} in {metadata_path}")
        for field in ("presenters", "chapters"):
            if not isinstance(metadata.get(field), list) or not metadata[field]:
                errors.append(f"{field} must be a non-empty list in {metadata_path}")
        artifacts = metadata.get("artifacts")
        if (
            not isinstance(artifacts, list)
            or not artifacts
            or len(artifacts) != len(set(artifacts))
            or not set(artifacts).issubset(SUPPORTED_ARTIFACTS)
        ):
            errors.append(
                f"artifacts must be a unique non-empty subset of "
                f"{sorted(SUPPORTED_ARTIFACTS)} in {metadata_path}"
            )
            artifacts = []

        deck_html = metadata_path.parent / "index.html"
        report_html = metadata_path.parent / "report.html"
        if "slides" in artifacts and not deck_html.is_file():
            errors.append(f"slides artifact is missing index.html: {metadata_path.parent}")
        if "report" in artifacts and not report_html.is_file():
            errors.append(f"report artifact is missing report.html: {metadata_path.parent}")

        template_id = metadata.get("template")
        if "slides" in artifacts and template_id == "study-deck-v1" and deck_html.is_file():
            deck_text = deck_html.read_text(encoding="utf-8", errors="replace")
            if 'data-deck-template="study-deck-v1"' not in deck_text:
                errors.append(f"study-deck-v1 marker is missing in {deck_html}")
            for asset in ("assets/deck.css", "assets/deck.js"):
                if not (metadata_path.parent / asset).is_file():
                    errors.append(
                        f"study-deck-v1 asset is missing in {metadata_path.parent}: {asset}"
                    )

        report_template_id = metadata.get("report_template")
        if (
            "report" in artifacts
            and report_template_id == "study-report-v1"
            and report_html.is_file()
        ):
            report_text = report_html.read_text(encoding="utf-8", errors="replace")
            if 'data-report-template="study-report-v1"' not in report_text:
                errors.append(f"study-report-v1 marker is missing in {report_html}")
            for asset in ("assets/report.css", "assets/report.js"):
                if not (metadata_path.parent / asset).is_file():
                    errors.append(
                        f"study-report-v1 asset is missing in {metadata_path.parent}: {asset}"
                    )

        validate_cjk_wrap_contract(metadata_path.parent, errors)
        validate_svg_prose_contract(metadata_path.parent, errors)

        if (
            {"report", "slides"}.issubset(artifacts)
            and template_id == "study-deck-v1"
            and report_template_id == "study-report-v1"
            and deck_html.is_file()
            and report_html.is_file()
        ):
            expected_workflow = "raw-report-deck-v1"
            if metadata.get("workflow") != expected_workflow:
                errors.append(
                    f"paired study artifacts must use workflow={expected_workflow!r} "
                    f"in {metadata_path}"
                )
            if metadata.get("report_source") != "report.html":
                errors.append(
                    f"paired study artifacts must use report_source='report.html' "
                    f"in {metadata_path}"
                )

            report_trace = ReportDeckTraceParser()
            report_trace.feed(report_html.read_text(encoding="utf-8", errors="replace"))
            deck_trace = ReportDeckTraceParser()
            deck_trace.feed(deck_html.read_text(encoding="utf-8", errors="replace"))

            validate_source_fidelity(
                metadata,
                studies[study_id],
                report_trace,
                deck_trace,
                report_html,
                deck_html,
                errors,
                warnings,
            )
            if metadata.get("source_fidelity") == SOURCE_FIDELITY_VERSION:
                validate_source_fidelity_report_css(metadata_path.parent, errors)
                validate_svg_connector_fill_contract(metadata_path.parent, errors)
            validate_deck_visual_provenance(
                report_trace,
                deck_trace,
                deck_html,
                errors,
            )
            validate_retained_unreferenced_assets(
                metadata,
                metadata_path.parent,
                report_trace,
                deck_trace,
                errors,
            )
            validate_retained_alternate_html(
                metadata,
                metadata_path.parent,
                errors,
            )

            for duplicate in sorted(report_trace.duplicate_ids):
                errors.append(f"duplicate report id in {report_html}: {duplicate}")
            for duplicate in sorted(deck_trace.duplicate_ids):
                errors.append(f"duplicate deck id in {deck_html}: {duplicate}")
            validate_caption_sequence(report_trace, report_html, errors)
            validate_internal_report_references(report_trace, report_html, errors)
            validate_unique_source_figure_assets(report_trace, report_html, errors)
            if report_trace.required_figures_without_id:
                errors.append(
                    f"{report_trace.required_figures_without_id} required report figure(s) "
                    f"lack a stable id in {report_html}"
                )
            for figure_id, figure in sorted(report_trace.figures.items()):
                if not figure.caption:
                    errors.append(
                        f"report figure lacks a non-empty figcaption in "
                        f"{report_html}: {figure_id}"
                    )
                if not figure.note:
                    errors.append(
                        f"report figure lacks a non-empty asset note in "
                        f"{report_html}: {figure_id}"
                    )
                if not figure.has_accessible_visual:
                    errors.append(
                        f"report figure lacks non-empty image alt text or an accessible "
                        f"inline SVG in {report_html}: {figure_id}"
                    )
            if deck_trace.deck_report_source != "report.html":
                errors.append(
                    f"deck must declare data-report-source='report.html' on its main "
                    f"element: {deck_html}"
                )
            if not deck_trace.slides:
                errors.append(f"deck has no traceable slides: {deck_html}")

            labels = [slide.label for slide in deck_trace.slides]
            for index, label in enumerate(labels, start=1):
                if not label:
                    errors.append(
                        f"slide {index} lacks a non-empty aria-label in {deck_html}"
                    )
            duplicates = sorted(
                label for label in set(labels) if label and labels.count(label) > 1
            )
            if duplicates:
                errors.append(
                    f"deck slide aria-label values must be unique in {deck_html}: "
                    f"{duplicates}"
                )

            referenced: set[str] = set()
            deck_image_sources: set[str] = set()
            for slide in deck_trace.slides:
                label = slide.label or "unnamed slide"
                if not slide.refs:
                    errors.append(
                        f"slide lacks data-report-refs in {deck_html}: {label}"
                    )
                    continue
                referenced.update(slide.refs)
                deck_image_sources.update(slide.image_sources)
                unknown = sorted(set(slide.refs) - report_trace.ids)
                if unknown:
                    errors.append(
                        f"slide references unknown report id(s) in {deck_html} "
                        f"({label}): {unknown}"
                    )
                untraced_links = sorted(slide.report_links - set(slide.refs))
                if untraced_links:
                    errors.append(
                        f"slide report.html anchor is absent from data-report-refs in "
                        f"{deck_html} ({label}): {untraced_links}"
                    )
                for report_reference in slide.report_references:
                    expected = report_trace.caption_labels_by_id.get(
                        report_reference.target
                    )
                    if expected is None:
                        continue
                    visible = extract_caption_references(report_reference.text)
                    if visible and visible != {expected}:
                        expected_text = f"{expected[0]} {expected[1]}"
                        found_text = ", ".join(
                            f"{kind} {number}" for kind, number in sorted(visible)
                        )
                        errors.append(
                            f"deck report reference caption label is stale in "
                            f"{deck_html} ({label}): report.html#"
                            f"{report_reference.target} expects {expected_text}, "
                            f"found {found_text} in {report_reference.text!r}"
                        )
                visible_slide_labels = extract_caption_references(slide.text)
                expected_slide_labels = {
                    report_trace.caption_labels_by_id[report_id]
                    for report_id in slide.refs
                    if report_id in report_trace.caption_labels_by_id
                }
                stale_slide_labels = visible_slide_labels - expected_slide_labels
                if stale_slide_labels:
                    found_text = ", ".join(
                        f"{kind} {number}"
                        for kind, number in sorted(stale_slide_labels)
                    )
                    expected_text = (
                        ", ".join(
                            f"{kind} {number}"
                            for kind, number in sorted(expected_slide_labels)
                        )
                        if expected_slide_labels
                        else "<none>"
                    )
                    errors.append(
                        f"deck slide contains caption label(s) not backed by "
                        f"data-report-refs in {deck_html} ({label}): "
                        f"{found_text}; expected one of {expected_text}"
                    )

            missing_sections = sorted(report_trace.report_sections - referenced)
            if missing_sections:
                errors.append(
                    f"deck does not cover report section id(s) in {deck_html}: "
                    f"{missing_sections}"
                )
            missing_figures = sorted(report_trace.required_figures - referenced)
            if missing_figures:
                errors.append(
                    f"deck does not reuse required report figure id(s) in {deck_html}: "
                    f"{missing_figures}"
                )
            for figure_id in sorted(report_trace.required_figures):
                figure = report_trace.figures[figure_id]
                if not figure.image_sources:
                    errors.append(
                        f"required report figure must use a reusable img src in "
                        f"{report_html}: {figure_id}"
                    )
                    continue
                if not (figure.image_sources & deck_image_sources):
                    errors.append(
                        f"deck does not visually reuse required report figure src in "
                        f"{deck_html}: {figure_id} -> {sorted(figure.image_sources)}"
                    )

            validate_font_stack_contract(
                metadata_path.parent,
                f"{study_id}/{session_id}",
                errors,
            )

        key = (study_id, session_id)
        if key in seen:
            errors.append(f"duplicate presentation id: {study_id}/{session_id}")
        seen.add(key)

        session_size = sum(
            path.stat().st_size for path in metadata_path.parent.rglob("*") if path.is_file()
        )
        if session_size > MAX_SESSION_BYTES:
            errors.append(
                f"session artifacts exceed {MAX_SESSION_BYTES // 1024 // 1024} MiB: "
                f"{metadata_path.parent} ({session_size} bytes)"
            )


def validate_reference(
    html_path: Path,
    site: Path,
    tag: str,
    attribute: str,
    value: str,
    errors: list[str],
    warnings: list[str],
    check_local_targets: bool = True,
) -> None:
    stripped = value.strip()
    if not stripped or stripped.startswith("#"):
        return
    if stripped.startswith("//"):
        errors.append(f"protocol-relative URL in {html_path}: {value}")
        return

    parsed = urlparse(stripped)
    scheme = parsed.scheme.lower()
    if scheme in {"mailto", "tel"}:
        return
    if scheme == "data":
        if len(stripped) > 1_000_000:
            errors.append(f"embedded data URL is too large in {html_path}")
        return
    if scheme:
        if scheme != "https":
            errors.append(f"non-HTTPS external URL in {html_path}: {value}")
        elif tag in {"script", "iframe"}:
            warnings.append(f"review external {tag} in {html_path}: {value}")
        return
    if stripped.startswith("/"):
        errors.append(f"root-relative Pages URL in {html_path}: {value}")
        return

    local_part = unquote(parsed.path)
    if not local_part:
        return
    target = (html_path.parent / local_part).resolve()
    site_root = site.resolve()
    if not within(target, site_root):
        errors.append(f"reference escapes html/ in {html_path}: {value}")
        return
    if target.is_dir():
        target = target / "index.html"
    if check_local_targets and not target.exists():
        errors.append(f"broken local reference in {html_path}: {value}")


def validate_html(site: Path, errors: list[str], warnings: list[str]) -> None:
    # html/archive/ 아래는 과거 공개 스냅샷이다.
    # 저작 시점 기준이 다르므로 품질 규칙(title/viewport/lang/alt/링크 무결성)은
    # 면제하고, 안전 규칙(form, protocol-relative, 비HTTPS, html 이탈)은 유지한다.
    archive_root = site / "archive"
    for html_path in sorted(site.rglob("*.html")):
        legacy = archive_root in html_path.parents
        text = html_path.read_text(encoding="utf-8", errors="replace")
        parser = PageParser()
        parser.feed(text)
        if not legacy:
            if not parser.has_title:
                errors.append(f"missing <title> in {html_path}")
            if not parser.has_viewport:
                errors.append(f"missing viewport meta tag in {html_path}")
            if not parser.has_icon:
                errors.append(f"missing favicon link in {html_path}")
            if parser.html_lang not in {"ko", "en"}:
                errors.append(f"missing or unsupported html lang in {html_path}")
            if parser.images_without_alt:
                errors.append(
                    f"{parser.images_without_alt} image(s) without alt text in {html_path}"
                )
        if parser.forms:
            errors.append(f"forms are not allowed on the public study site: {html_path}")
        for tag, attribute, value in parser.references:
            validate_reference(
                html_path, site, tag, attribute, value, errors, warnings,
                check_local_targets=not legacy,
            )


def validate_files(site: Path, errors: list[str]) -> None:
    if not site.is_dir():
        errors.append(f"site directory does not exist: {site}")
        return
    for required in (site / ".nojekyll", site / "index.html", site / "assets" / "site.css"):
        if not required.exists():
            errors.append(f"missing required site file: {required}")
    for path in site.rglob("*"):
        if path.is_symlink() and not within(path.resolve(), site.resolve()):
            errors.append(f"site symlink escapes html/: {path}")
        if path.is_file() and path.stat().st_size > MAX_FILE_BYTES:
            errors.append(
                f"file exceeds {MAX_FILE_BYTES // 1024 // 1024} MiB: {path}"
            )
        if not path.is_file() or path.suffix.lower() not in {".css", ".html", ".js", ".svg"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if MERGE_MARKER_RE.search(text):
            errors.append(f"unresolved merge marker in public asset: {path}")
        if path.suffix.lower() == ".css" and STANDALONE_CSS_PLUS_RE.search(text):
            errors.append(f"standalone '+' diff artifact in public CSS: {path}")


def main() -> int:
    args = parse_args()
    if args.print_source_outline:
        return print_source_outline(args.print_source_outline.resolve())
    registry = args.registry.resolve()
    site = args.site.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    validate_files(site, errors)
    studies = validate_registry(
        registry, site, args.check_materials, errors
    )
    validate_metadata(site, studies, errors, warnings)
    validate_materials_links(site, errors)
    validate_html(site, errors, warnings)

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"site validation failed with {len(errors)} error(s)", file=sys.stderr)
        return 1

    html_count = sum(1 for _ in site.rglob("*.html"))
    print(f"site validation passed ({html_count} HTML file(s), {len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
