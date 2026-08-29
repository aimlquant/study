from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_site.py"
)
SPEC = importlib.util.spec_from_file_location("build_site", SCRIPT)
assert SPEC and SPEC.loader
build_site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_site)


SITE = {
    "name": "AIML Quant",
    "name_ko": "AI·ML·Quant",
    "space_ko": "스터디",
    "repository": "restful3/aimlquant",
    "pages_url": "https://restful3.github.io/aimlquant/",
    "landing_url": "https://restful3.github.io/",
    "youtube_channel_id": "UCFCw_lSFRhco6h25cXiFecw",
    "youtube_handle": "@aimlquant",
    "youtube_url": "https://www.youtube.com/@aimlquant",
    "kakao_openchat_url": "https://open.kakao.com/o/gtYt0KGi",
    "contact_email": "restful3@gmail.com",
    "materials_repository": "aimlquant/study-materials",
}
STUDIES = [
    {
        "id": "machine-trading-2026",
        "track": "quant",
        "slug": "machine-trading",
        "title": "Machine Trading",
        "title_ko": "머신 트레이딩",
        "description_ko": "알고리즘 트레이딩을 재현 실험과 함께 학습합니다.",
        "status": "active",
        "start_date": "2026-07-25",
        "end_date": "2026-09-12",
        "weekday": "saturday",
        "start_time": "08:00",
        "end_time": "10:00",
        "timezone": "Asia/Seoul",
        "venue": "Webex",
        "planned_chapters": ["Chapter 2"],
        "materials_path": "materials/quant/active/machine-trading",
        "archive_path": "materials/quant/archive/machine-trading",
        "presentation_path": "html/studies/machine-trading",
        "source_repository": "https://github.com/restful3/ml4t",
        "source_commit": "2f7e3801e088ab50f9cd9181f725477443cf8e47",
        "book": {
            "title": "Machine Trading",
            "authors": ["Ernest P. Chan"],
            "publisher": "Wiley",
            "year": "2017",
            "isbn13": "9781119219606",
            "language_ko": "영어",
            "summary_ko": "정량 전략을 하나씩 구현하며 알고리즘 트레이딩을 익힌다.",
            "store_label": "Amazon",
            "store_url": "https://www.amazon.com/dp/1119219604",
            "publisher_url": "https://www.wiley.com/example",
        },
    }
]


class SiteRenderingTest(unittest.TestCase):
    def test_pages_share_the_presentation_visual_identity(self) -> None:
        session = {
            "id": "2026-08-01-machine-trading-ch02",
            "study_id": "machine-trading-2026",
            "date": "2026-08-01",
            "title": "Chapter 2. 팩터 모델",
            "presenters": ["발표자"],
            "chapters": ["Chapter 2"],
            "status": "materials-published",
            "artifacts": [
                {
                    "kind": "slides",
                    "label": "발표자료",
                    "url": "studies/machine-trading/presentations/ch02/",
                }
            ],
        }

        files = build_site.render_files(SITE, STUDIES, [session])
        root_page = files[Path("index.html")]
        study_page = files[
            Path("studies") / "machine-trading" / "index.html"
        ]
        session_page = files[
            Path("sessions")
            / "2026-08-01-machine-trading-ch02"
            / "index.html"
        ]

        for rendered in (root_page, study_page, session_page):
            with self.subTest(page=rendered[:80]):
                self.assertIn('<html lang="ko" class="theme-light">', rendered)
                self.assertIn("AIML Quant", rendered)
        self.assertIn("OPEN STUDY ARCHIVE", root_page)
        self.assertIn('<div class="brand">', root_page)
        self.assertIn("STUDY MATERIALS", study_page)
        self.assertIn("SESSION ARCHIVE", session_page)

    def test_materials_are_published_before_video(self) -> None:
        session = {
            "id": "2026-08-01-machine-trading-ch02",
            "study_id": "machine-trading-2026",
            "date": "2026-08-01",
            "title": "Chapter 2. 팩터 모델",
            "presenters": ["발표자"],
            "chapters": ["Chapter 2"],
            "status": "materials-published",
            "artifacts": [
                {
                    "kind": "slides",
                    "label": "발표자료",
                    "url": "studies/machine-trading/presentations/ch02/",
                }
            ],
        }

        files = build_site.render_files(SITE, STUDIES, [session])
        page = files[
            Path("sessions")
            / "2026-08-01-machine-trading-ch02"
            / "index.html"
        ]

        self.assertIn("영상 준비 중", page)
        self.assertIn("발표자료", page)
        self.assertNotIn("youtube.com/embed/", page)

    def test_schedule_and_presenter_are_visible_in_lists_and_catalog(self) -> None:
        session = {
            "id": "2026-08-01-machine-trading-ch02",
            "study_id": "machine-trading-2026",
            "date": "2026-08-01",
            "title": "Chapter 2. 팩터 모델",
            "presenters": ["종훈"],
            "chapters": ["Chapter 2"],
            "status": "scheduled",
            "meeting_url": (
                "https://lgehq.webex.com/lgehq-en/j.php?"
                "MTID=m04f313dbbe685507858e50181ce261a7"
            ),
            "artifacts": [],
        }

        files = build_site.render_files(SITE, STUDIES, [session])
        root_page = files[Path("index.html")]
        study_page = files[
            Path("studies") / "machine-trading" / "index.html"
        ]
        catalog = json.loads(files[Path("data") / "catalog.json"])

        self.assertIn("전체 스터디 일정", root_page)
        self.assertIn('class="root-schedules"', root_page)
        self.assertIn('class="schedule-presenter"', root_page)
        self.assertIn("종훈", root_page)
        self.assertIn(session["meeting_url"], root_page)
        self.assertIn("08:00–10:00 · Webex", root_page)
        self.assertIn("매주 토요일 08:00–10:00 · Webex", study_page)
        self.assertIn("전체 일정", study_page)
        self.assertIn('<section id="schedule">', study_page)
        self.assertIn('class="schedule-board"', study_page)
        self.assertIn("Webex 접속 ↗", study_page)
        self.assertIn(session["meeting_url"], study_page)
        self.assertEqual(catalog["sessions"][0]["presenters"], ["종훈"])
        self.assertEqual(catalog["sessions"][0]["chapters"], ["Chapter 2"])
        self.assertEqual(
            catalog["sessions"][0]["meeting_url"],
            session["meeting_url"],
        )

    def test_scheduled_page_does_not_claim_materials_are_published(self) -> None:
        session = {
            "id": "2026-08-01-machine-trading-ch02",
            "study_id": "machine-trading-2026",
            "date": "2026-08-01",
            "title": "Chapter 2. 팩터 모델",
            "presenters": [],
            "chapters": ["Chapter 2"],
            "status": "scheduled",
            "artifacts": [],
        }

        files = build_site.render_files(SITE, STUDIES, [session])
        page = files[
            Path("sessions")
            / "2026-08-01-machine-trading-ch02"
            / "index.html"
        ]

        self.assertIn("일정 등록", page)
        self.assertIn("발표: 미정", page)
        self.assertNotIn("교안을 먼저 공개했습니다", page)

    def test_public_video_adds_embed_and_backlink_catalog(self) -> None:
        session = {
            "id": "2026-08-01-machine-trading-ch02",
            "study_id": "machine-trading-2026",
            "date": "2026-08-01",
            "title": "Chapter 2. 팩터 모델",
            "presenters": ["발표자"],
            "chapters": ["Chapter 2"],
            "status": "video-public",
            "artifacts": [
                {
                    "kind": "slides",
                    "label": "발표자료",
                    "url": "studies/machine-trading/presentations/ch02/",
                }
            ],
            "youtube_video_id": "123456789ab",
        }

        files = build_site.render_files(SITE, STUDIES, [session])
        page = files[
            Path("sessions")
            / "2026-08-01-machine-trading-ch02"
            / "index.html"
        ]
        root_page = files[Path("index.html")]
        catalog = json.loads(files[Path("data") / "catalog.json"])

        self.assertIn(
            "https://www.youtube.com/embed/123456789ab",
            page,
        )
        self.assertIn("최근 공개 영상", root_page)
        self.assertIn(
            "https://www.youtube.com/embed/123456789ab",
            root_page,
        )
        self.assertIn('class="home-video-grid"', root_page)
        self.assertIn('loading="lazy"', root_page)
        self.assertEqual(
            catalog["sessions"][0]["page_url"],
            (
                "https://restful3.github.io/aimlquant/"
                "sessions/2026-08-01-machine-trading-ch02/"
            ),
        )
        self.assertEqual(
            catalog["sessions"][0]["youtube_url"],
            "https://www.youtube.com/watch?v=123456789ab",
        )


class LifecycleValidationTest(unittest.TestCase):
    def write_metadata(
        self,
        root: Path,
        status: str,
        video_line: str,
    ) -> tuple[Path, Path, Path]:
        site = root / "site.toml"
        studies = root / "studies.toml"
        sessions = root / "sessions.toml"
        site.write_text(
            """
schema_version = 1
[site]
name = "AIML Quant"
name_ko = "AI·ML·Quant"
space_ko = "스터디"
repository = "restful3/aimlquant"
pages_url = "https://restful3.github.io/aimlquant/"
landing_url = "https://restful3.github.io/"
youtube_channel_id = "UCFCw_lSFRhco6h25cXiFecw"
youtube_handle = "@aimlquant"
youtube_url = "https://www.youtube.com/@aimlquant"
kakao_openchat_url = "https://open.kakao.com/o/gtYt0KGi"
contact_email = "restful3@gmail.com"
materials_repository = "aimlquant/study-materials"
""",
            encoding="utf-8",
        )
        studies.write_text(
            """
schema_version = 1
[[studies]]
id = "machine-trading-2026"
track = "quant"
slug = "machine-trading"
title = "Machine Trading"
title_ko = "머신 트레이딩"
description_ko = "알고리즘 트레이딩을 재현 실험과 함께 학습합니다."
status = "active"
start_date = "2026-07-25"
end_date = "2026-09-12"
weekday = "saturday"
start_time = "08:00"
end_time = "10:00"
timezone = "Asia/Seoul"
venue = "Webex"
planned_chapters = ["Chapter 2"]
materials_path = "materials/quant/active/machine-trading"
archive_path = "materials/quant/archive/machine-trading"
presentation_path = "html/studies/machine-trading"
source_repository = "https://github.com/restful3/ml4t"
source_commit = "2f7e3801e088ab50f9cd9181f725477443cf8e47"

[studies.book]
title = "Machine Trading"
authors = ["Ernest P. Chan"]
publisher = "Wiley"
year = "2017"
isbn13 = "9781119219606"
language_ko = "영어"
summary_ko = "정량 전략을 하나씩 구현하며 알고리즘 트레이딩을 익힌다."
store_label = "Amazon"
store_url = "https://www.amazon.com/dp/1119219604"
publisher_url = "https://www.wiley.com/example"
""",
            encoding="utf-8",
        )
        sessions.write_text(
            f"""
schema_version = 1
[[sessions]]
id = "2026-08-01-machine-trading-ch02"
study_id = "machine-trading-2026"
date = "2026-08-01"
title = "Chapter 2"
presenters = ["발표자"]
chapters = ["Chapter 2"]
status = "{status}"
artifacts = [
  {{ kind = "slides", label = "발표자료", url = "slides/ch02/" }},
]
{video_line}
""",
            encoding="utf-8",
        )
        return site, studies, sessions

    def test_non_public_status_rejects_video_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.write_metadata(
                Path(directory),
                "materials-published",
                'youtube_video_id = "123456789ab"',
            )
            with self.assertRaisesRegex(
                ValueError,
                "non-public session must not store",
            ):
                build_site.load_model(*paths)

    def test_public_status_requires_video_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.write_metadata(
                Path(directory),
                "video-public",
                "",
            )
            with self.assertRaisesRegex(
                ValueError,
                "video-public requires",
            ):
                build_site.load_model(*paths)

    def test_scheduled_session_rejects_published_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.write_metadata(
                Path(directory),
                "scheduled",
                "",
            )
            with self.assertRaisesRegex(
                ValueError,
                "scheduled session must not publish artifacts",
            ):
                build_site.load_model(*paths)

    def test_meeting_url_requires_a_valid_webex_join_url(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.write_metadata(
                Path(directory),
                "materials-published",
                'meeting_url = "https://example.com/meeting"',
            )
            with self.assertRaisesRegex(
                ValueError,
                "HTTPS Webex join URL",
            ):
                build_site.load_model(*paths)

    def test_ended_meeting_must_not_publish_a_join_url(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.write_metadata(
                Path(directory),
                "materials-published",
                "\n".join(
                    [
                        'meeting_status = "ended"',
                        (
                            'meeting_url = "https://lgehq.webex.com/'
                            'lgehq-en/j.php?MTID='
                            'm04f313dbbe685507858e50181ce261a7"'
                        ),
                    ]
                ),
            )
            with self.assertRaisesRegex(
                ValueError,
                "ended meeting must not publish",
            ):
                build_site.load_model(*paths)

    def test_planned_chapters_must_all_have_a_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.write_metadata(
                Path(directory),
                "materials-published",
                "",
            )
            studies = paths[1]
            studies.write_text(
                studies.read_text(encoding="utf-8").replace(
                    'planned_chapters = ["Chapter 2"]',
                    'planned_chapters = ["Chapter 1", "Chapter 2"]',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "missing=Chapter 1",
            ):
                build_site.load_model(*paths)


class MaterialsGateTest(unittest.TestCase):
    """교재는 private 저장소로 가므로, 외부 방문자가 404 대신
    참여 안내를 보도록 공개 사이트가 안내 페이지를 제공해야 한다."""

    def test_gate_page_is_generated(self) -> None:
        files = build_site.render_files(SITE, STUDIES, [])

        self.assertIn(Path("materials") / "index.html", files)

    def test_gate_page_invites_participants_without_leaking_the_join_code(
        self,
    ) -> None:
        files = build_site.render_files(SITE, STUDIES, [])
        gate = files[Path("materials") / "index.html"]

        self.assertIn(SITE["kakao_openchat_url"], gate)
        self.assertIn(SITE["contact_email"], gate)
        self.assertIn(SITE["materials_repository"], gate)
        # 참가 암호는 메일로만 안내한다. 공개 산출물에 넣지 않는다.
        self.assertNotIn("참가 코드:", gate)
        self.assertNotIn("암호:", gate)

    def test_gate_page_is_for_every_participant_not_only_presenters(
        self,
    ) -> None:
        files = build_site.render_files(SITE, STUDIES, [])
        gate = files[Path("materials") / "index.html"]

        self.assertIn("참가자", gate)
        self.assertNotIn("발표자 전용", gate)

    def test_site_config_requires_the_new_contact_fields(self) -> None:
        for field in (
            "kakao_openchat_url",
            "contact_email",
            "materials_repository",
        ):
            with self.subTest(field=field):
                broken = dict(SITE)
                broken.pop(field)
                with self.assertRaisesRegex(ValueError, field):
                    build_site.validate_site(broken)

    def test_custom_404_page_is_generated(self) -> None:
        files = build_site.render_files(SITE, STUDIES, [])

        self.assertIn(Path("404.html"), files)


class LandingLinkTest(unittest.TestCase):
    """이 저장소는 조직 랜딩의 하위 공간이다. 루트에서 랜딩으로
    한 번에 돌아갈 수 있어야 방문자가 다른 공간을 찾을 수 있다."""

    def test_root_page_links_back_to_the_landing_page(self) -> None:
        files = build_site.render_files(SITE, STUDIES, [])
        root = files[Path("index.html")]

        self.assertIn(
            f'<a class="back back--home" href="{SITE["landing_url"]}">'
            f'← {SITE["name"]} 홈</a>',
            root,
        )

    def test_root_header_follows_the_landing_format(self) -> None:
        """네 공개 공간이 한 형식으로 읽혀야 한다. 운영 가이드가 기준이다 —
        브랜드 표기, 홈 링크, 제목, 리드 순서. 그 사이에 eyebrow 나
        커버 블록을 끼우지 않는다."""
        files = build_site.render_files(SITE, STUDIES, [])
        header = files[Path("index.html")].split("<section")[0]

        self.assertNotIn("hero", header)
        self.assertNotIn('class="eyebrow"', header)
        for earlier, later in (
            ('class="brand"', 'class="back back--home"'),
            ('class="back back--home"', "<h1>"),
            ("<h1>", 'class="lead"'),
        ):
            self.assertLess(header.index(earlier), header.index(later))

    def test_root_title_and_heading_name_the_space(self) -> None:
        """랜딩은 이 공간을 '스터디' 라고 부른다. 페이지 제목도 같은 이름이어야
        방문자가 어디에 왔는지 안다. 조직 이름은 브랜드 표기가 이미 말한다."""
        files = build_site.render_files(SITE, STUDIES, [])
        root = files[Path("index.html")]

        self.assertIn(f"<h1>{SITE['space_ko']}</h1>", root)
        self.assertIn(
            f"<title>{SITE['space_ko']} · {SITE['name_ko']}</title>", root
        )

    def test_site_config_requires_the_space_name(self) -> None:
        broken = dict(SITE)
        broken.pop("space_ko")

        with self.assertRaisesRegex(ValueError, "space_ko"):
            build_site.validate_site(broken)

    def test_shell_matches_the_landing_width(self) -> None:
        css = (build_site.DEFAULT_OUTPUT / "assets" / "site.css").read_text(encoding="utf-8")

        self.assertIn("width: min(1080px, calc(100% - 48px));", css)

    def test_site_config_requires_the_landing_url(self) -> None:
        broken = dict(SITE)
        broken.pop("landing_url")

        with self.assertRaisesRegex(ValueError, "landing_url"):
            build_site.validate_site(broken)


class RealRegistryTest(unittest.TestCase):
    def test_current_schedule_covers_both_studies(self) -> None:
        _, studies, sessions = build_site.load_model(
            build_site.DEFAULT_SITE_CONFIG,
            build_site.DEFAULT_STUDIES,
            build_site.DEFAULT_SESSIONS,
        )
        counts = {
            study["id"]: sum(
                session["study_id"] == study["id"]
                for session in sessions
            )
            for study in studies
        }

        self.assertEqual(counts["machine-trading-2026"], 8)
        self.assertEqual(counts["kg-llm-in-action-2026"], 14)
        self.assertEqual(len(sessions), 22)

        machine_trading = next(
            study
            for study in studies
            if study["id"] == "machine-trading-2026"
        )
        self.assertNotIn("Chapter 8", machine_trading["planned_chapters"])
        discussion = next(
            session
            for session in sessions
            if session["id"]
            == "2026-09-12-machine-trading-next-study-discussion"
        )
        self.assertEqual(discussion["chapters"], [])
        self.assertEqual(discussion["presenters"], ["참석자 전원"])

    def test_root_page_lists_every_public_session(self) -> None:
        site, studies, sessions = build_site.load_model(
            build_site.DEFAULT_SITE_CONFIG,
            build_site.DEFAULT_STUDIES,
            build_site.DEFAULT_SESSIONS,
        )
        root_page = build_site.render_files(
            site,
            studies,
            sessions,
        )[Path("index.html")]

        self.assertEqual(root_page.count('class="track-schedule"'), 2)
        for session in sessions:
            self.assertIn(
                f'href="sessions/{session["id"]}/"',
                root_page,
            )

    def test_readme_schedule_matches_public_session_registry(self) -> None:
        site, studies, sessions = build_site.load_model(
            build_site.DEFAULT_SITE_CONFIG,
            build_site.DEFAULT_STUDIES,
            build_site.DEFAULT_SESSIONS,
        )
        study_by_id = {study["id"]: study for study in studies}
        readme_lines = (
            (build_site.REPO_ROOT / "README.md")
            .read_text(encoding="utf-8")
            .splitlines()
        )

        for session in sessions:
            needle = f"/sessions/{session['id']}/"
            matching = [line for line in readme_lines if needle in line]
            self.assertEqual(len(matching), 1, session["id"])
            row = matching[0]
            study = study_by_id[session["study_id"]]
            self.assertIn(str(session["date"]), row)
            self.assertIn(
                f"{study['start_time']}–{study['end_time']}",
                row,
            )
            self.assertIn(build_site.presenter_label(session), row)
            meeting_url = session.get("meeting_url")
            if meeting_url:
                self.assertIn(meeting_url, row)
            elif build_site.meeting_state(session) == "ended":
                self.assertIn("종료", row)
            else:
                self.assertIn("추후 공지", row)

        self.assertIn(site["pages_url"], "\n".join(readme_lines))


if __name__ == "__main__":
    unittest.main()


class SourceBookTest(unittest.TestCase):
    """발표자료는 우리가 만들지만 원본은 출판된 책이다. 스터디 페이지가
    무슨 책을 읽는지, 어디서 살 수 있는지 밝혀야 참가 여부를 판단할 수 있다."""

    def test_study_page_shows_the_source_book(self) -> None:
        files = build_site.render_files(SITE, STUDIES, [])
        page = files[Path("studies") / "machine-trading" / "index.html"]
        book = STUDIES[0]["book"]

        self.assertIn('<section id="book">', page)
        self.assertIn(book["title"], page)
        self.assertIn(book["authors"][0], page)
        self.assertIn(book["publisher"], page)
        self.assertIn(book["year"], page)
        self.assertIn(book["isbn13"], page)
        self.assertIn(book["summary_ko"], page)

    def test_study_page_links_to_the_store_and_the_publisher(self) -> None:
        files = build_site.render_files(SITE, STUDIES, [])
        page = files[Path("studies") / "machine-trading" / "index.html"]
        book = STUDIES[0]["book"]

        self.assertIn(book["store_url"], page)
        self.assertIn(book["publisher_url"], page)
        self.assertIn(book["store_label"], page)

    def test_the_book_itself_is_not_distributed(self) -> None:
        """교재 본문은 저작물이다. 공개 페이지가 배포처럼 읽히면 안 된다."""
        files = build_site.render_files(SITE, STUDIES, [])
        page = files[Path("studies") / "machine-trading" / "index.html"]

        self.assertIn("직접 구매", page)

    def test_every_study_must_declare_its_book(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site, studies, sessions = LifecycleValidationTest().write_metadata(
                root, "scheduled", ""
            )
            text = studies.read_text(encoding="utf-8")
            studies.write_text(
                text[: text.index("[studies.book]")], encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "book"):
                build_site.load_model(site, studies, sessions)


class RealBookRegistryTest(unittest.TestCase):
    def test_both_active_studies_declare_a_verifiable_book(self) -> None:
        _, studies, _ = build_site.load_model(
            build_site.DEFAULT_SITE_CONFIG,
            build_site.DEFAULT_STUDIES,
            build_site.DEFAULT_SESSIONS,
        )

        self.assertEqual(len(studies), 2)
        for study in studies:
            with self.subTest(study=study["id"]):
                book = study["book"]
                self.assertRegex(book["isbn13"], r"^97[89]\d{10}$")
                self.assertTrue(book["store_url"].startswith("https://"))
                self.assertTrue(book["publisher_url"].startswith("https://"))
