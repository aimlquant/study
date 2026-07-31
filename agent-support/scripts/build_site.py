#!/usr/bin/env python3
"""Build and validate the AI Odyssey Study static site."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tomllib
from datetime import date
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SITE_CONFIG = REPO_ROOT / "agent-support" / "site.toml"
DEFAULT_STUDIES = REPO_ROOT / "agent-support" / "studies.toml"
DEFAULT_SESSIONS = REPO_ROOT / "agent-support" / "sessions.toml"
DEFAULT_OUTPUT = REPO_ROOT / "html"
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SESSION_STATES = {
    "scheduled",
    "materials-published",
    "video-public",
    "cancelled",
}
ARTIFACT_KINDS = {"report", "slides", "notebook", "code", "other"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--studies", type=Path, default=DEFAULT_STUDIES)
    parser.add_argument("--sessions", type=Path, default=DEFAULT_SESSIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except FileNotFoundError as exc:
        raise ValueError(f"metadata file not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid TOML in {path}: {exc}") from exc


def require_schema(data: dict, path: Path) -> None:
    if data.get("schema_version") != 1:
        raise ValueError(f"unsupported schema_version in {path}")


def require_slug(value: object, label: str) -> str:
    if not isinstance(value, str) or not SLUG_RE.fullmatch(value):
        raise ValueError(
            f"{label} must be a lowercase ASCII slug: {value!r}"
        )
    return value


def validate_relative_url(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith("/")
        or "://" in value
    ):
        raise ValueError(
            f"{label} must be a site-root relative URL: {value!r}"
        )
    path = PurePosixPath(value.rstrip("/"))
    if ".." in path.parts or "." in path.parts:
        raise ValueError(f"{label} must not traverse directories: {value!r}")
    return value


def load_model(
    site_path: Path,
    studies_path: Path,
    sessions_path: Path,
) -> tuple[dict, list[dict], list[dict]]:
    site_data = load_toml(site_path)
    studies_data = load_toml(studies_path)
    sessions_data = load_toml(sessions_path)
    for data, path in (
        (site_data, site_path),
        (studies_data, studies_path),
        (sessions_data, sessions_path),
    ):
        require_schema(data, path)

    site = site_data.get("site")
    if not isinstance(site, dict):
        raise ValueError("site.toml must contain [site]")
    for field in (
        "name",
        "name_ko",
        "repository",
        "pages_url",
        "youtube_channel_id",
        "youtube_handle",
        "youtube_url",
    ):
        if not isinstance(site.get(field), str) or not site[field].strip():
            raise ValueError(f"site field is missing or empty: {field}")
    if not site["pages_url"].endswith("/"):
        raise ValueError("pages_url must end with '/'")

    studies = studies_data.get("studies")
    if not isinstance(studies, list) or not studies:
        raise ValueError(
            "studies.toml must contain at least one [[studies]] entry"
        )
    by_id: dict[str, dict] = {}
    seen_slugs: set[str] = set()
    for study in studies:
        study_id = require_slug(study.get("id"), "study id")
        slug = require_slug(study.get("slug"), "study slug")
        if study_id in by_id or slug in seen_slugs:
            raise ValueError(
                f"duplicate study id or slug: {study_id}/{slug}"
            )
        for field in (
            "track",
            "title",
            "title_ko",
            "materials_path",
            "archive_path",
            "presentation_path",
            "source_repository",
            "source_commit",
        ):
            if (
                not isinstance(study.get(field), str)
                or not study[field].strip()
            ):
                raise ValueError(
                    f"study {study_id} field is missing or empty: {field}"
                )
        if study.get("status") not in {"active", "archived"}:
            raise ValueError(
                f"invalid study status for {study_id}: "
                f"{study.get('status')}"
            )
        if study["track"] not in {"aiml", "quant"}:
            raise ValueError(
                f"invalid study track for {study_id}: {study['track']}"
            )
        expected_active = (
            f"materials/{study['track']}/active/{slug}"
        )
        expected_archive = (
            f"materials/{study['track']}/archive/{slug}"
        )
        if study["archive_path"] != expected_archive:
            raise ValueError(
                f"archive_path for {study_id} must be {expected_archive}"
            )
        expected_materials = (
            expected_active
            if study["status"] == "active"
            else expected_archive
        )
        if study["materials_path"] != expected_materials:
            raise ValueError(
                f"materials_path for {study_id} must be "
                f"{expected_materials}"
            )
        expected_public = f"html/studies/{slug}"
        if study["presentation_path"] != expected_public:
            raise ValueError(
                f"presentation_path for {study_id} must be "
                f"{expected_public}"
            )
        if not COMMIT_RE.fullmatch(study["source_commit"]):
            raise ValueError(
                f"invalid source_commit for {study_id}"
            )
        by_id[study_id] = study
        seen_slugs.add(slug)

    sessions = sessions_data.get("sessions", [])
    if not isinstance(sessions, list):
        raise ValueError("sessions must be an array of tables")
    seen_sessions: set[str] = set()
    for session in sessions:
        session_id = require_slug(session.get("id"), "session id")
        if session_id in seen_sessions:
            raise ValueError(f"duplicate session id: {session_id}")
        seen_sessions.add(session_id)
        study_id = session.get("study_id")
        if study_id not in by_id:
            raise ValueError(
                f"unknown study_id for {session_id}: {study_id}"
            )
        try:
            date.fromisoformat(str(session.get("date")))
        except ValueError as exc:
            raise ValueError(
                f"invalid date for {session_id}: {session.get('date')}"
            ) from exc
        if (
            not isinstance(session.get("title"), str)
            or not session["title"].strip()
        ):
            raise ValueError(f"session title is missing: {session_id}")
        for field in ("presenters", "chapters"):
            values = session.get(field)
            if not isinstance(values, list) or any(
                not isinstance(item, str) or not item.strip()
                for item in values
            ):
                raise ValueError(
                    f"{field} must be a string array for {session_id}"
                )
        status = session.get("status")
        if status not in SESSION_STATES:
            raise ValueError(
                f"invalid session status for {session_id}: {status}"
            )
        artifacts = session.get("artifacts", [])
        if not isinstance(artifacts, list):
            raise ValueError(
                f"artifacts must be an array for {session_id}"
            )
        for artifact in artifacts:
            if (
                not isinstance(artifact, dict)
                or artifact.get("kind") not in ARTIFACT_KINDS
            ):
                raise ValueError(
                    f"invalid artifact kind for {session_id}: {artifact!r}"
                )
            if (
                not isinstance(artifact.get("label"), str)
                or not artifact["label"].strip()
            ):
                raise ValueError(
                    f"artifact label is missing for {session_id}"
                )
            artifact["url"] = validate_relative_url(
                artifact.get("url"),
                f"artifact URL for {session_id}",
            )
        if (
            status in {"materials-published", "video-public"}
            and not artifacts
        ):
            raise ValueError(
                f"{status} requires at least one artifact for {session_id}"
            )
        video_id = session.get("youtube_video_id")
        if status == "video-public":
            if (
                not isinstance(video_id, str)
                or not VIDEO_ID_RE.fullmatch(video_id)
            ):
                raise ValueError(
                    "video-public requires an 11-character YouTube "
                    f"video ID for {session_id}"
                )
        elif video_id is not None:
            raise ValueError(
                "non-public session must not store youtube_video_id: "
                f"{session_id}"
            )

    sessions.sort(
        key=lambda item: (str(item["date"]), item["id"]),
        reverse=True,
    )
    return site, studies, sessions


def page(
    title: str,
    stylesheet: str,
    body: str,
    canonical: str,
) -> str:
    favicon = stylesheet.rsplit("/", 1)[0] + "/favicon.svg"
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="canonical" href="{html.escape(canonical)}">
  <link rel="icon" href="{html.escape(favicon)}" type="image/svg+xml">
  <link rel="stylesheet" href="{stylesheet}">
</head>
<body>
  <main class="shell">
{body}
  </main>
</body>
</html>
"""


def status_label(status: str) -> str:
    return {
        "scheduled": "예정",
        "materials-published": "교안 공개",
        "video-public": "영상 공개",
        "cancelled": "취소",
    }[status]


def render_session_card(session: dict, prefix: str = "") -> str:
    return (
        f'<a class="card" href="{prefix}sessions/{session["id"]}/">'
        f'<span class="badge badge--{session["status"]}">'
        f'{status_label(session["status"])}</span>'
        f'<p class="eyebrow">{html.escape(str(session["date"]))}</p>'
        f'<h3>{html.escape(session["title"])}</h3>'
        f'<p>{html.escape(" · ".join(session.get("chapters", [])))}</p>'
        "</a>"
    )


def render_files(
    site: dict,
    studies: list[dict],
    sessions: list[dict],
) -> dict[Path, str]:
    files: dict[Path, str] = {}
    study_by_id = {study["id"]: study for study in studies}
    cards = "\n".join(
        '<a class="card" href="studies/{slug}/">'
        '<span class="badge">{track}</span>'
        "<h2>{title_ko}</h2><p>{title}</p></a>".format(
            slug=study["slug"],
            track=html.escape(study["track"].upper()),
            title_ko=html.escape(study["title_ko"]),
            title=html.escape(study["title"]),
        )
        for study in studies
    )
    recent = (
        "\n".join(render_session_card(item) for item in sessions[:8])
        or '<p class="empty">등록된 회차가 없습니다.</p>'
    )
    root_body = f"""    <header class="hero">
      <p class="eyebrow">GITHUB PAGES × YOUTUBE</p>
      <h1>{html.escape(site["name_ko"])}</h1>
      <p class="lead">교안을 먼저 공개하고, 스터디 영상이 공개되면 같은 회차 페이지에서 연결합니다.</p>
      <a class="button" href="{html.escape(site["youtube_url"])}">YouTube 채널</a>
    </header>
    <section>
      <h2>진행 중인 스터디</h2>
      <div class="grid">{cards}</div>
    </section>
    <section>
      <h2>최근 회차</h2>
      <div class="grid">{recent}</div>
    </section>"""
    files[Path("index.html")] = page(
        site["name_ko"],
        "assets/site.css",
        root_body,
        site["pages_url"],
    )

    for study in studies:
        matching = [
            item for item in sessions if item["study_id"] == study["id"]
        ]
        materials_url = (
            f"https://github.com/{site['repository']}/tree/main/"
            f"{study['materials_path']}"
        )
        session_cards = (
            "\n".join(
                render_session_card(item, "../../") for item in matching
            )
            or '<p class="empty">등록된 회차가 없습니다.</p>'
        )
        body = f"""    <a class="back" href="../../">← 전체 스터디</a>
    <header class="page-header">
      <p class="eyebrow">{html.escape(study["track"].upper())}</p>
      <h1>{html.escape(study["title_ko"])}</h1>
      <p class="lead">{html.escape(study["title"])}</p>
      <div class="actions">
        <a class="button" href="{html.escape(materials_url)}">교재 자료</a>
        <a class="button button--secondary" href="{html.escape(study["source_repository"])}">이전 저장소</a>
      </div>
    </header>
    <section>
      <h2>회차</h2>
      <div class="grid">{session_cards}</div>
    </section>"""
        canonical = (
            site["pages_url"] + f"studies/{study['slug']}/"
        )
        files[
            Path("studies") / study["slug"] / "index.html"
        ] = page(
            study["title_ko"],
            "../../assets/site.css",
            body,
            canonical,
        )

    for session in sessions:
        study = study_by_id[session["study_id"]]
        artifacts = (
            "".join(
                '<a class="button button--secondary" '
                f'href="../../{html.escape(item["url"])}">'
                f'{html.escape(item["label"])}</a>'
                for item in session.get("artifacts", [])
            )
            or '<p class="empty">교안 준비 중입니다.</p>'
        )
        video_id = session.get("youtube_video_id")
        if video_id:
            watch_url = (
                f"https://www.youtube.com/watch?v={video_id}"
            )
            video = f"""<div class="video">
        <iframe src="https://www.youtube.com/embed/{video_id}" title="{html.escape(session["title"])}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
      </div>
      <a class="button" href="{watch_url}">YouTube에서 보기·댓글 참여</a>"""
        else:
            video = """<div class="pending">
        <strong>영상 준비 중</strong>
        <p>교안을 먼저 공개했습니다. 영상이 공개되면 이 페이지에서 연결합니다.</p>
      </div>"""
        presenters = (
            ", ".join(session.get("presenters", [])) or "미정"
        )
        body = f"""    <a class="back" href="../../studies/{study["slug"]}/">← {html.escape(study["title_ko"])}</a>
    <header class="page-header">
      <p class="eyebrow">{html.escape(str(session["date"]))} · {html.escape(study["track"].upper())}</p>
      <h1>{html.escape(session["title"])}</h1>
      <p class="lead">발표: {html.escape(presenters)}</p>
    </header>
    <section>
      <h2>발표자료</h2>
      <div class="actions">{artifacts}</div>
    </section>
    <section>
      <h2>스터디 영상</h2>
      {video}
    </section>"""
        canonical = (
            site["pages_url"] + f"sessions/{session['id']}/"
        )
        files[
            Path("sessions") / session["id"] / "index.html"
        ] = page(
            session["title"],
            "../../assets/site.css",
            body,
            canonical,
        )

    catalog_sessions = []
    for session in sessions:
        public = {
            "id": session["id"],
            "study_id": session["study_id"],
            "date": str(session["date"]),
            "title": session["title"],
            "status": session["status"],
            "page_url": (
                site["pages_url"]
                + f"sessions/{session['id']}/"
            ),
            "artifacts": session.get("artifacts", []),
        }
        if session.get("youtube_video_id"):
            video_id = session["youtube_video_id"]
            public["youtube_video_id"] = video_id
            public["youtube_url"] = (
                f"https://www.youtube.com/watch?v={video_id}"
            )
        catalog_sessions.append(public)
    catalog = {
        "schema_version": 1,
        "site": site,
        "studies": studies,
        "sessions": catalog_sessions,
    }
    files[Path("data") / "catalog.json"] = (
        json.dumps(
            catalog,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return files


def write_or_check(
    output: Path,
    files: dict[Path, str],
    check: bool,
) -> bool:
    changed = False
    for relative, content in sorted(
        files.items(),
        key=lambda item: str(item[0]),
    ):
        target = output / relative
        current = (
            target.read_text(encoding="utf-8")
            if target.exists()
            else None
        )
        if current == content:
            continue
        if check:
            raise ValueError(
                f"generated file is stale or missing: {target}"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        display = (
            target.relative_to(REPO_ROOT)
            if target.is_relative_to(REPO_ROOT)
            else target
        )
        print(f"updated {display}")
        changed = True
    return changed


def main() -> int:
    args = parse_args()
    try:
        site, studies, sessions = load_model(
            args.site_config.resolve(),
            args.studies.resolve(),
            args.sessions.resolve(),
        )
        files = render_files(site, studies, sessions)
        changed = write_or_check(
            args.output.resolve(),
            files,
            args.check,
        )
        if not (
            args.output.resolve() / "assets" / "site.css"
        ).is_file():
            raise ValueError("html/assets/site.css is missing")
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.check:
        print("generated site is up to date")
    elif not changed:
        print("generated site already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
