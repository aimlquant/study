#!/usr/bin/env python3
"""Build and validate the AIML Quant static site."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tomllib
from collections import Counter
from datetime import date, time
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SITE_CONFIG = REPO_ROOT / "agent-support" / "site.toml"
DEFAULT_STUDIES = REPO_ROOT / "agent-support" / "studies.toml"
DEFAULT_SESSIONS = REPO_ROOT / "agent-support" / "sessions.toml"
DEFAULT_OUTPUT = REPO_ROOT / "html"
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
WEBEX_MTID_RE = re.compile(r"^m[0-9a-f]{32}$")
ISBN13_RE = re.compile(r"^97[89][0-9]{10}$")
SESSION_STATES = {
    "scheduled",
    "materials-published",
    "video-public",
    "cancelled",
}
ARTIFACT_KINDS = {"report", "slides", "notebook", "code", "other"}
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
WEEKDAY_LABELS = {
    "monday": "월요일",
    "tuesday": "화요일",
    "wednesday": "수요일",
    "thursday": "목요일",
    "friday": "금요일",
    "saturday": "토요일",
    "sunday": "일요일",
}


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


def validate_meeting_url(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty URL")
    parsed = urlsplit(value)
    hostname = (parsed.hostname or "").lower()
    meeting_ids = parse_qs(parsed.query).get("MTID", [])
    if (
        parsed.scheme != "https"
        or not hostname.endswith(".webex.com")
        or not parsed.path.endswith("/j.php")
        or len(meeting_ids) != 1
        or not WEBEX_MTID_RE.fullmatch(meeting_ids[0])
        or parsed.fragment
    ):
        raise ValueError(
            f"{label} must be an HTTPS Webex join URL with a valid MTID"
        )
    return value


def validate_book(book: object, study_id: str) -> None:
    """스터디마다 원본 교재를 반드시 밝힌다. 발표자료만 보고 온 방문자가
    무슨 책인지, 어디서 사는지 알 수 없으면 참가 여부를 정할 수 없다."""
    if not isinstance(book, dict):
        raise ValueError(f"study {study_id} must declare [studies.book]")
    for field in (
        "title",
        "publisher",
        "year",
        "isbn13",
        "language_ko",
        "summary_ko",
        "store_label",
        "store_url",
        "publisher_url",
    ):
        if not isinstance(book.get(field), str) or not book[field].strip():
            raise ValueError(
                f"study {study_id} book field is missing or empty: {field}"
            )
    authors = book.get("authors")
    if (
        not isinstance(authors, list)
        or not authors
        or any(
            not isinstance(author, str) or not author.strip()
            for author in authors
        )
    ):
        raise ValueError(
            f"study {study_id} book authors must be a non-empty string array"
        )
    if not ISBN13_RE.fullmatch(book["isbn13"]):
        raise ValueError(
            f"study {study_id} book isbn13 must be 13 digits: {book['isbn13']}"
        )
    for field in ("store_url", "publisher_url"):
        if not book[field].startswith("https://"):
            raise ValueError(
                f"study {study_id} book {field} must be an HTTPS URL"
            )


def validate_site(site: object) -> None:
    if not isinstance(site, dict):
        raise ValueError("site.toml must contain [site]")
    for field in (
        "name",
        "name_ko",
        "space_ko",
        "repository",
        "pages_url",
        "landing_url",
        "youtube_channel_id",
        "youtube_handle",
        "youtube_url",
        "kakao_openchat_url",
        "contact_email",
        "materials_repository",
    ):
        if not isinstance(site.get(field), str) or not site[field].strip():
            raise ValueError(f"site field is missing or empty: {field}")
    if not site["pages_url"].endswith("/"):
        raise ValueError("pages_url must end with '/'")


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
    validate_site(site)

    studies = studies_data.get("studies")
    if not isinstance(studies, list) or not studies:
        raise ValueError(
            "studies.toml must contain at least one [[studies]] entry"
        )
    by_id: dict[str, dict] = {}
    seen_slugs: set[str] = set()
    study_dates: dict[str, tuple[date, date]] = {}
    planned_chapters: dict[str, list[str]] = {}
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
            "description_ko",
            "start_date",
            "end_date",
            "weekday",
            "start_time",
            "end_time",
            "timezone",
            "venue",
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
        try:
            start_date = date.fromisoformat(study["start_date"])
            end_date = date.fromisoformat(study["end_date"])
        except ValueError as exc:
            raise ValueError(
                f"invalid study date range for {study_id}"
            ) from exc
        if start_date > end_date:
            raise ValueError(
                f"study start_date must not exceed end_date: {study_id}"
            )
        weekday = study["weekday"]
        if weekday not in WEEKDAYS:
            raise ValueError(
                f"invalid weekday for {study_id}: {weekday}"
            )
        try:
            start_time = time.fromisoformat(study["start_time"])
            end_time = time.fromisoformat(study["end_time"])
        except ValueError as exc:
            raise ValueError(
                f"invalid study time range for {study_id}"
            ) from exc
        if start_time >= end_time:
            raise ValueError(
                f"study start_time must precede end_time: {study_id}"
            )
        try:
            ZoneInfo(study["timezone"])
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"invalid timezone for {study_id}: {study['timezone']}"
            ) from exc
        chapters = study.get("planned_chapters")
        if (
            not isinstance(chapters, list)
            or not chapters
            or any(
                not isinstance(chapter, str) or not chapter.strip()
                for chapter in chapters
            )
            or len(set(chapters)) != len(chapters)
        ):
            raise ValueError(
                f"planned_chapters must be a unique string array: {study_id}"
            )
        validate_book(study.get("book"), study_id)
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
        study_dates[study_id] = (start_date, end_date)
        planned_chapters[study_id] = chapters
        seen_slugs.add(slug)

    sessions = sessions_data.get("sessions", [])
    if not isinstance(sessions, list):
        raise ValueError("sessions must be an array of tables")
    seen_sessions: set[str] = set()
    covered_chapters: dict[str, Counter[str]] = {
        study_id: Counter() for study_id in by_id
    }
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
            session_date = date.fromisoformat(str(session.get("date")))
        except ValueError as exc:
            raise ValueError(
                f"invalid date for {session_id}: {session.get('date')}"
            ) from exc
        if not session_id.startswith(f"{session_date.isoformat()}-"):
            raise ValueError(
                f"session id must start with its date: {session_id}"
            )
        # 운영 회차(kind = "operations")는 교재 일정에서 빠지고 허브의 운영 기록에 실린다.
        kind = session.get("kind", "study")
        if kind not in {"study", "operations"}:
            raise ValueError(
                f"invalid session kind for {session_id}: {kind!r}"
            )
        session["kind"] = kind
        study_start, study_end = study_dates[study_id]
        if not study_start <= session_date <= study_end:
            raise ValueError(
                f"session date is outside its study range: {session_id}"
            )
        expected_weekday = WEEKDAYS[by_id[study_id]["weekday"]]
        if session_date.weekday() != expected_weekday:
            raise ValueError(
                f"session date does not match study weekday: {session_id}"
            )
        if (
            not isinstance(session.get("title"), str)
            or not session["title"].strip()
        ):
            raise ValueError(f"session title is missing: {session_id}")
        summary = session.get("summary")
        if summary is not None and (
            not isinstance(summary, str) or not summary.strip()
        ):
            raise ValueError(
                f"session summary must be a non-empty string: {session_id}"
            )
        discussion_points = session.get("discussion_points", [])
        if not isinstance(discussion_points, list) or any(
            not isinstance(item, str) or not item.strip()
            for item in discussion_points
        ):
            raise ValueError(
                "session discussion_points must be a string array: "
                f"{session_id}"
            )
        for field in ("presenters", "chapters"):
            values = session.get(field)
            if not isinstance(values, list) or any(
                not isinstance(item, str) or not item.strip()
                for item in values
            ):
                raise ValueError(
                    f"{field} must be a string array for {session_id}"
                )
        unknown_chapters = sorted(
            set(session["chapters"]) - set(planned_chapters[study_id])
        )
        if unknown_chapters:
            raise ValueError(
                f"unknown planned chapter for {session_id}: "
                f"{', '.join(unknown_chapters)}"
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
        meeting_url = session.get("meeting_url")
        meeting_status = session.get("meeting_status")
        if meeting_status is not None and meeting_status not in {
            "pending",
            "available",
            "ended",
        }:
            raise ValueError(
                f"invalid meeting_status for {session_id}: "
                f"{meeting_status}"
            )
        if meeting_url is not None:
            session["meeting_url"] = validate_meeting_url(
                meeting_url,
                f"meeting_url for {session_id}",
            )
            if meeting_status in {"pending", "ended"}:
                raise ValueError(
                    f"{meeting_status} meeting must not publish a "
                    f"meeting_url: {session_id}"
                )
        elif meeting_status == "available":
            raise ValueError(
                f"available meeting requires meeting_url: {session_id}"
            )
        if (
            status in {"materials-published", "video-public"}
            and not artifacts
        ):
            raise ValueError(
                f"{status} requires at least one artifact for {session_id}"
            )
        if status == "scheduled" and artifacts:
            raise ValueError(
                f"scheduled session must not publish artifacts: {session_id}"
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
        if status != "cancelled":
            covered_chapters[study_id].update(session["chapters"])

    for study_id, chapters in planned_chapters.items():
        counts = covered_chapters[study_id]
        missing = [chapter for chapter in chapters if counts[chapter] == 0]
        duplicates = [
            chapter for chapter in chapters if counts[chapter] > 1
        ]
        if missing or duplicates:
            details = []
            if missing:
                details.append(f"missing={', '.join(missing)}")
            if duplicates:
                details.append(f"duplicate={', '.join(duplicates)}")
            raise ValueError(
                f"session plan does not cover {study_id}: "
                + "; ".join(details)
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
<html lang="ko" class="theme-light">
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


def presenter_label(session: dict) -> str:
    return ", ".join(session.get("presenters", [])) or "미정"


def meeting_state(session: dict) -> str:
    if session.get("meeting_url"):
        return "available"
    return session.get("meeting_status", "pending")


def study_schedule_label(study: dict) -> str:
    return (
        f"매주 {WEEKDAY_LABELS[study['weekday']]} "
        f"{study['start_time']}–{study['end_time']} · {study['venue']}"
    )


def render_session_card(
    session: dict,
    study: dict,
    prefix: str = "",
) -> str:
    chapters = " · ".join(session.get("chapters", []))
    chapter_meta = (
        f'<span>{html.escape(chapters)}</span>' if chapters else ""
    )
    time_and_venue = (
        f"{study['start_time']}–{study['end_time']} · {study['venue']}"
    )
    return (
        f'<a class="card" href="{prefix}sessions/{session["id"]}/">'
        f'<span class="badge badge--{session["status"]}">'
        f'{status_label(session["status"])}</span>'
        f'<p class="eyebrow">{html.escape(str(session["date"]))}</p>'
        f'<h3>{html.escape(session["title"])}</h3>'
        '<div class="session-card-meta">'
        f'{chapter_meta}'
        f'<span>{html.escape(time_and_venue)}</span>'
        f'<span>발표: {html.escape(presenter_label(session))}</span>'
        "</div>"
        "</a>"
    )


def render_home_video_card(session: dict, study: dict) -> str:
    video_id = session["youtube_video_id"]
    session_url = f'sessions/{session["id"]}/'
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    title = html.escape(session["title"])
    return f"""<article class="home-video-card">
        <div class="video home-video-embed">
          <iframe src="https://www.youtube.com/embed/{video_id}" title="{title}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
        </div>
        <div class="home-video-copy">
          <p class="eyebrow">{html.escape(str(session["date"]))} · {html.escape(study["title_ko"])}</p>
          <h3><a href="{session_url}">{title}</a></h3>
          <p>발표: {html.escape(presenter_label(session))}</p>
          <div class="home-video-links">
            <a href="{session_url}">교안·발표자료 보기 →</a>
            <a href="{watch_url}">YouTube에서 보기 ↗</a>
          </div>
        </div>
      </article>"""


def render_schedule_row(
    session: dict,
    study: dict,
    prefix: str = "",
) -> str:
    meeting_url = session.get("meeting_url")
    state = meeting_state(session)
    meeting = (
        f'<a class="schedule-webex" href="{html.escape(meeting_url)}" '
        'target="_blank" rel="noopener noreferrer">Webex 접속 ↗</a>'
        if state == "available"
        else (
            '<span class="schedule-ended">종료</span>'
            if state == "ended"
            else '<span class="schedule-tbd">추후 공지</span>'
        )
    )
    chapters = " · ".join(session.get("chapters", []))
    chapter_label = (
        '\n            <span class="schedule-chapters">'
        f'{html.escape(chapters)}</span>'
        if chapters
        else ""
    )
    return f"""        <div class="schedule-row">
          <div class="schedule-when">
            <strong>{html.escape(str(session["date"]))}</strong>
            <span>{html.escape(study["start_time"])}–{html.escape(study["end_time"])}</span>
          </div>
          <div class="schedule-topic">
            <span class="badge badge--{session["status"]}">{status_label(session["status"])}</span>{chapter_label}
            <a href="{prefix}sessions/{session["id"]}/">{html.escape(session["title"])}</a>
          </div>
          <div class="schedule-presenter"><span class="schedule-mobile-label">발표</span>{html.escape(presenter_label(session))}</div>
          <div class="schedule-meeting"><span class="schedule-mobile-label">접속</span>{meeting}</div>
        </div>"""


def render_materials_gate(site: dict) -> str:
    """교재는 private 저장소에 있다. 외부 방문자가 GitHub 404를 보는 대신
    무슨 자료인지와 참여 방법을 안내받도록 공개 사이트가 대신 응답한다."""
    materials_repo = site["materials_repository"]
    body = f"""    <header class="site-masthead">
      <a class="brand-name" href="../">{html.escape(site["name"])}</a>
      <span class="brand-sub">STUDY MATERIALS</span>
    </header>
    <a class="back" href="../">← 스터디 허브</a>
    <header class="page-header">
      <p class="eyebrow">참가자 공개 자료</p>
      <h1>교재 자료</h1>
      <p class="lead" id="requested-path">스터디 참가자에게 공개되는 자료입니다.</p>
      <p class="study-description">
        발표자료에 인용된 교재 원문·해설·소스 코드는 스터디 참가자에게
        공개합니다. 참가 신청을 하시면 교재 저장소 접근 권한을 드립니다.
      </p>
      <div class="actions">
        <a class="button" href="{html.escape(site["kakao_openchat_url"])}"
           target="_blank" rel="noopener noreferrer">카카오 오픈채팅 참여 ↗</a>
        <a class="button button--secondary"
           href="https://github.com/{html.escape(materials_repo)}"
           target="_blank" rel="noopener noreferrer">교재 저장소 (참가자) ↗</a>
      </div>
      <p class="session-meeting-note">
        오픈채팅 입장에는 참가 코드가 필요합니다.
        <a href="mailto:{html.escape(site["contact_email"])}"
           >{html.escape(site["contact_email"])}</a>
        로 메일 주시면 코드를 안내해 드립니다.
      </p>
    </header>
    <script>
      (function () {{
        var p = new URLSearchParams(location.search).get("p");
        if (!p) return;
        var name = p.split("/").pop();
        var el = document.getElementById("requested-path");
        if (el) el.textContent = name;
        var repo = document.querySelector(".button--secondary");
        if (repo) {{
          repo.href =
            "https://github.com/{materials_repo}/blob/main/" + p;
        }}
      }})();
    </script>"""
    return page(
        "교재 자료 · 참가자 공개",
        "../assets/site.css",
        body,
        site["pages_url"] + "materials/",
    )


def render_not_found(site: dict) -> str:
    body = f"""    <header class="page-header">
      <p class="eyebrow">404</p>
      <h1>페이지를 찾을 수 없습니다</h1>
      <p class="lead">주소가 바뀌었거나 아직 공개되지 않은 회차일 수 있습니다.</p>
      <div class="actions">
        <a class="button" href="{html.escape(site["pages_url"])}">스터디 허브로</a>
        <a class="button button--secondary"
           href="{html.escape(site["youtube_url"])}"
           target="_blank" rel="noopener noreferrer">YouTube 채널 ↗</a>
      </div>
    </header>"""
    return page(
        "찾을 수 없음",
        site["pages_url"] + "assets/site.css",
        body,
        site["pages_url"],
    )


def render_book(study: dict) -> str:
    """교재 본문은 저작물이라 배포하지 않는다. 무슨 책인지 밝히고
    구매처로 보내는 것이 공개 사이트가 할 수 있는 전부다."""
    book = study["book"]
    imprint = " · ".join(
        part
        for part in (
            ", ".join(book["authors"]),
            book["publisher"],
            book.get("series", ""),
            book["year"],
        )
        if part
    )
    subtitle = (
        f'\n        <p class="book-subtitle">'
        f'{html.escape(book["subtitle"])}</p>'
        if book.get("subtitle")
        else ""
    )
    return f"""    <section id="book">
      <h2>교재</h2>
      <p class="section-intro">발표자료와 해설은 스터디에서 직접 만들지만, 함께 읽는 원본은 아래 책입니다. 책은 배포하지 않으니 각자 직접 구매해 주세요.</p>
      <article class="book">
        <h3>{html.escape(book["title"])}</h3>{subtitle}
        <p class="book-imprint">{html.escape(imprint)}</p>
        <p class="book-summary">{html.escape(book["summary_ko"].strip())}</p>
        <dl class="book-facts">
          <div><dt>ISBN</dt><dd>{html.escape(book["isbn13"])}</dd></div>
          <div><dt>언어</dt><dd>{html.escape(book["language_ko"])}</dd></div>
          <div><dt>스터디 범위</dt><dd>{len(study["planned_chapters"])}개 장</dd></div>
        </dl>
        <div class="actions">
          <a class="button" href="{html.escape(book["store_url"])}"
             target="_blank" rel="noopener noreferrer">{html.escape(book["store_label"])}에서 구매 ↗</a>
          <a class="button button--secondary" href="{html.escape(book["publisher_url"])}"
             target="_blank" rel="noopener noreferrer">출판사 페이지 ↗</a>
        </div>
      </article>
    </section>"""


def render_files(
    site: dict,
    studies: list[dict],
    sessions: list[dict],
) -> dict[Path, str]:
    files: dict[Path, str] = {}
    files[Path("materials") / "index.html"] = render_materials_gate(site)
    files[Path("404.html")] = render_not_found(site)
    study_by_id = {study["id"]: study for study in studies}
    active_studies = [
        study for study in studies if study["status"] == "active"
    ]
    archived_studies = [
        study for study in studies if study["status"] == "archived"
    ]
    cards = "\n".join(
        '<a class="card" href="studies/{slug}/">'
        '<span class="badge">{track}</span>'
        "<h2>{title_ko}</h2><p>{title}</p>"
        '<p class="study-card-description">{description}</p>'
        '<p class="study-card-schedule">{schedule}</p></a>'.format(
            slug=study["slug"],
            track=html.escape(study["track"].upper()),
            title_ko=html.escape(study["title_ko"]),
            title=html.escape(study["title"]),
            description=html.escape(study["description_ko"]),
            schedule=html.escape(study_schedule_label(study)),
        )
        for study in active_studies
    )
    # 종료된 교재는 진행 중 목록과 전체 일정에서 빼고 지난 스터디로 안내한다.
    # 회차 URL과 교안·영상은 교재 페이지에서 그대로 볼 수 있다.
    archive_cards = "\n".join(
        '<a class="card card--archived" href="studies/{slug}/">'
        '<span class="badge badge--archived">종료</span>'
        '<span class="badge">{track}</span>'
        "<h2>{title_ko}</h2><p>{title}</p>"
        '<p class="study-card-description">{description}</p>'
        '<p class="study-card-schedule">{start}–{end} · {count}회</p></a>'.format(
            slug=study["slug"],
            track=html.escape(study["track"].upper()),
            title_ko=html.escape(study["title_ko"]),
            title=html.escape(study["title"]),
            description=html.escape(study["description_ko"]),
            start=html.escape(study["start_date"]),
            end=html.escape(study["end_date"]),
            count=sum(
                1
                for item in sessions
                if item["study_id"] == study["id"]
                and item["status"] != "cancelled"
                and item.get("kind", "study") == "study"
            ),
        )
        for study in archived_studies
    )
    archive_section = (
        f"""    <section id="archive">
      <h2>지난 스터디</h2>
      <p class="section-intro">종료된 교재입니다. 회차별 교안과 공개 영상은 그대로 볼 수 있습니다.</p>
      <div class="grid">{archive_cards}</div>
    </section>
"""
        if archived_studies
        else ""
    )
    archive_button = (
        '\n      <a class="button button--secondary" href="#archive">지난 스터디</a>'
        if archived_studies
        else ""
    )
    published_sessions = sorted(
        (
            item
            for item in sessions
            if item["status"] in {"materials-published", "video-public"}
        ),
        key=lambda item: (str(item["date"]), item["id"]),
        reverse=True,
    )
    recent = (
        "\n".join(
            render_session_card(item, study_by_id[item["study_id"]])
            for item in published_sessions[:8]
        )
        or '<p class="empty">등록된 회차가 없습니다.</p>'
    )
    public_videos = sorted(
        (item for item in sessions if item["status"] == "video-public"),
        key=lambda item: (str(item["date"]), item["id"]),
        reverse=True,
    )
    home_videos = (
        "\n".join(
            render_home_video_card(item, study_by_id[item["study_id"]])
            for item in public_videos[:4]
        )
        or '<p class="empty">공개된 영상이 없습니다.</p>'
    )
    root_schedules = []
    for study in sorted(
        active_studies,
        key=lambda item: (item["start_time"], item["track"]),
    ):
        matching = sorted(
            (
                item
                for item in sessions
                if item["study_id"] == study["id"]
                and item.get("kind", "study") == "study"
            ),
            key=lambda item: (str(item["date"]), item["id"]),
        )
        rows = "\n".join(
            render_schedule_row(item, study)
            for item in matching
        )
        root_schedules.append(
            f"""      <article class="track-schedule" id="{study["track"]}-schedule">
        <header class="track-schedule-header">
          <div>
            <p class="eyebrow">{html.escape(study["track"].upper())}</p>
            <h3>{html.escape(study["title_ko"])}</h3>
            <p>{html.escape(study["description_ko"])}</p>
          </div>
          <div class="track-schedule-meta">
            <span>{html.escape(study_schedule_label(study))}</span>
            <span>{html.escape(study["start_date"])}–{html.escape(study["end_date"])}</span>
            <a href="studies/{study["slug"]}/#schedule">스터디 상세 →</a>
          </div>
        </header>
        <div class="schedule-board">
          <div class="schedule-head" aria-hidden="true">
            <span>일시</span><span>범위</span><span>발표자</span><span>접속</span>
          </div>
{rows}
        </div>
      </article>"""
        )
    root_schedule_html = "\n".join(root_schedules)
    operations_sessions = sorted(
        (item for item in sessions if item.get("kind", "study") == "operations"),
        key=lambda item: (str(item["date"]), item["id"]),
        reverse=True,
    )
    operations_rows = "\n".join(
        render_schedule_row(item, study_by_id[item["study_id"]])
        for item in operations_sessions
    )
    operations_section = (
        f"""    <section id="operations">
      <h2>운영 기록</h2>
      <p class="section-intro">교재 진도와 별도로 진행한 운영 논의와 안내입니다. 회차 페이지에서 자료와 공개 영상을 볼 수 있습니다.</p>
      <div class="schedule-board">
        <div class="schedule-head" aria-hidden="true">
          <span>일시</span><span>주제</span><span>발표자</span><span>접속</span>
        </div>
{operations_rows}
      </div>
    </section>
"""
        if operations_sessions
        else ""
    )
    operations_button = (
        '\n      <a class="button button--secondary" href="#operations">운영 기록</a>'
        if operations_sessions
        else ""
    )
    root_body = f"""    <div class="brand">
      <span class="brand-name">{html.escape(site["name"])}</span>
      <span class="brand-sub">OPEN STUDY ARCHIVE</span>
    </div>
    <a class="back back--home" href="{html.escape(site["landing_url"])}">← {html.escape(site["name"])} 홈</a>
    <h1>{html.escape(site["space_ko"])}</h1>
    <p class="lead">교안을 먼저 공개하고, 스터디 영상이 공개되면 같은 회차 페이지에서 연결합니다.</p>
    <div class="actions">
      <a class="button" href="#schedule">전체 일정·Webex 보기</a>
      <a class="button button--secondary" href="{html.escape(site["youtube_url"])}"
         target="_blank" rel="noopener noreferrer">YouTube 채널 ↗</a>{archive_button}{operations_button}
    </div>
    <section>
      <h2>진행 중인 스터디</h2>
      <div class="grid">{cards}</div>
    </section>
{archive_section}    <section id="videos">
      <h2>최근 공개 영상</h2>
      <p class="section-intro">최신 공개 영상을 이 페이지에서 바로 재생하거나 회차별 교안·발표자료와 함께 볼 수 있습니다.</p>
      <div class="home-video-grid">
{home_videos}
      </div>
    </section>
    <section id="schedule">
      <h2>전체 스터디 일정</h2>
      <p class="section-intro">기존 스터디 README처럼 날짜·발표자·접속 링크를 한곳에 모았습니다. 종료·미정 상태와 공개된 회차 자료도 함께 확인할 수 있습니다.</p>
      <div class="root-schedules">
{root_schedule_html}
      </div>
    </section>
{operations_section}    <section>
      <h2>공개된 교안</h2>
      <div class="grid">{recent}</div>
    </section>"""
    files[Path("index.html")] = page(
        f"{site['space_ko']} · {site['name_ko']}",
        "assets/site.css",
        root_body,
        site["pages_url"],
    )

    for study in studies:
        matching = [
            item
            for item in sessions
            if item["study_id"] == study["id"]
            and item.get("kind", "study") == "study"
        ]
        matching.sort(
            key=lambda item: (str(item["date"]), item["id"])
        )
        # 교재는 참가자 공개 저장소에 있다. 외부 방문자가 GitHub 404를
        # 만나지 않도록 안내 페이지를 거쳐 보낸다.
        materials_url = (
            "../../materials/?p="
            + study["materials_path"].removeprefix("materials/")
        )
        schedule_rows = (
            "\n".join(
                render_schedule_row(item, study, "../../")
                for item in matching
            )
            or '<p class="empty">등록된 회차가 없습니다.</p>'
        )
        study_status_html = (
            '\n      <p class="study-status study-status--archived">종료된 스터디 · '
            f'{html.escape(study["start_date"])}–{html.escape(study["end_date"])} · '
            "교안과 공개 영상은 계속 볼 수 있습니다.</p>"
            if study["status"] == "archived"
            else ""
        )
        body = f"""    <header class="site-masthead">
      <a class="brand-name" href="../../">{html.escape(site["name"])}</a>
      <span class="brand-sub">STUDY MATERIALS</span>
    </header>
    <a class="back" href="../../">← 전체 스터디</a>
    <header class="page-header">
      <p class="eyebrow">{html.escape(study["track"].upper())}</p>{study_status_html}
      <h1>{html.escape(study["title_ko"])}</h1>
      <p class="lead">{html.escape(study["title"])}</p>
      <p class="study-description">{html.escape(study["description_ko"])}</p>
      <dl class="study-facts">
        <div><dt>기간</dt><dd>{html.escape(study["start_date"])}–{html.escape(study["end_date"])}</dd></div>
        <div><dt>일정</dt><dd>{html.escape(study_schedule_label(study))}</dd></div>
        <div><dt>시간대</dt><dd>{html.escape(study["timezone"])}</dd></div>
      </dl>
      <div class="actions">
        <a class="button" href="{html.escape(materials_url)}">교재 자료</a>
        <a class="button button--secondary" href="{html.escape(study["source_repository"])}">이전 저장소</a>
      </div>
    </header>
{render_book(study)}
    <section id="schedule">
      <h2>전체 일정</h2>
      <p class="section-intro">발표 담당과 Webex 접속 링크를 확인하세요. 미정 항목은 확정되는 대로 갱신합니다.</p>
      <div class="schedule-board">
        <div class="schedule-head" aria-hidden="true">
          <span>일시</span><span>범위</span><span>발표자</span><span>접속</span>
        </div>
{schedule_rows}
      </div>
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
        meeting_url = session.get("meeting_url")
        state = meeting_state(session)
        meeting_access = (
            '<div class="actions session-access">'
            f'<a class="button" href="{html.escape(meeting_url)}" '
            'target="_blank" rel="noopener noreferrer">'
            'Webex 접속 ↗</a></div>'
            if state == "available"
            else (
                '<p class="session-meeting-note">접속 링크: 종료된 회차</p>'
                if state == "ended"
                else '<p class="session-meeting-note">접속 링크: 추후 공지</p>'
            )
        )
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
        status = session["status"]
        if video_id:
            watch_url = (
                f"https://www.youtube.com/watch?v={video_id}"
            )
            video = f"""<div class="video">
        <iframe src="https://www.youtube.com/embed/{video_id}" title="{html.escape(session["title"])}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
      </div>
      <a class="button" href="{watch_url}">YouTube에서 보기·댓글 참여</a>"""
        elif status == "materials-published":
            video = """<div class="pending">
        <strong>영상 준비 중</strong>
        <p>교안을 먼저 공개했습니다. 영상이 공개되면 이 페이지에서 연결합니다.</p>
      </div>"""
        elif status == "scheduled":
            video = """<div class="pending">
        <strong>일정 등록</strong>
        <p>교안과 영상은 공개 준비가 끝나는 순서대로 이 페이지에 연결합니다.</p>
      </div>"""
        else:
            video = """<div class="pending pending--cancelled">
        <strong>취소된 회차</strong>
        <p>이 회차는 취소되었습니다. 변경된 일정은 스터디 목록에서 확인해 주세요.</p>
      </div>"""
        presenters = presenter_label(session)
        summary = session.get("summary")
        discussion_points = session.get("discussion_points", [])
        brief = ""
        if summary:
            points = "".join(
                f"<li>{html.escape(item)}</li>"
                for item in discussion_points
            )
            point_list = (
                f'<ul class="session-discussion-points">{points}</ul>'
                if points
                else ""
            )
            ended = session.get("meeting_status") == "ended"
            brief_heading = "논의 기록" if ended else "논의 안내"
            brief_title = "이 회차의 논의 내용" if ended else "이 회차에서 함께 결정할 것"
            brief = f"""    <section class="session-brief">
      <h2>{brief_heading}</h2>
      <article class="book">
        <h3>{brief_title}</h3>
        <p class="book-summary">{html.escape(summary)}</p>
        {point_list}
      </article>
    </section>
"""
        body = f"""    <header class="site-masthead">
      <a class="brand-name" href="../../">{html.escape(site["name"])}</a>
      <span class="brand-sub">SESSION ARCHIVE</span>
    </header>
    <a class="back" href="../../studies/{study["slug"]}/">← {html.escape(study["title_ko"])}</a>
    <header class="page-header">
      <p class="eyebrow">{html.escape(str(session["date"]))} · {html.escape(study["start_time"])}–{html.escape(study["end_time"])} · {html.escape(study["track"].upper())}</p>
      <h1>{html.escape(session["title"])}</h1>
      <p class="lead">발표: {html.escape(presenters)}</p>
      <p class="session-venue">장소: {html.escape(study["venue"])} · {html.escape(study["timezone"])}</p>
      {meeting_access}
    </header>
{brief}    <section>
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
            "presenters": session.get("presenters", []),
            "chapters": session.get("chapters", []),
            "status": session["status"],
            "meeting_status": meeting_state(session),
            "page_url": (
                site["pages_url"]
                + f"sessions/{session['id']}/"
            ),
            "artifacts": session.get("artifacts", []),
        }
        if session.get("meeting_url"):
            public["meeting_url"] = session["meeting_url"]
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
