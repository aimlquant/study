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
    "name": "AI Odyssey Study",
    "name_ko": "AI 오딧세이 스터디",
    "repository": "restful3/ai-odyssey-study",
    "pages_url": "https://restful3.github.io/ai-odyssey-study/",
    "youtube_channel_id": "UCFCw_lSFRhco6h25cXiFecw",
    "youtube_handle": "@ai_odyssey_study",
    "youtube_url": "https://www.youtube.com/@ai_odyssey_study",
}
STUDIES = [
    {
        "id": "machine-trading-2026",
        "track": "ml4t",
        "slug": "machine-trading",
        "title": "Machine Trading",
        "title_ko": "머신 트레이딩",
        "status": "active",
        "materials_path": "materials/active/machine-trading",
        "source_repository": "https://github.com/restful3/ml4t",
    }
]


class SiteRenderingTest(unittest.TestCase):
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
        catalog = json.loads(files[Path("data") / "catalog.json"])

        self.assertIn(
            "https://www.youtube.com/embed/123456789ab",
            page,
        )
        self.assertEqual(
            catalog["sessions"][0]["page_url"],
            (
                "https://restful3.github.io/ai-odyssey-study/"
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
name = "AI Odyssey Study"
name_ko = "AI 오딧세이 스터디"
repository = "restful3/ai-odyssey-study"
pages_url = "https://restful3.github.io/ai-odyssey-study/"
youtube_channel_id = "UCFCw_lSFRhco6h25cXiFecw"
youtube_handle = "@ai_odyssey_study"
youtube_url = "https://www.youtube.com/@ai_odyssey_study"
""",
            encoding="utf-8",
        )
        studies.write_text(
            """
schema_version = 1
[[studies]]
id = "machine-trading-2026"
track = "ml4t"
slug = "machine-trading"
title = "Machine Trading"
title_ko = "머신 트레이딩"
status = "active"
materials_path = "materials/active/machine-trading"
source_repository = "https://github.com/restful3/ml4t"
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


if __name__ == "__main__":
    unittest.main()
