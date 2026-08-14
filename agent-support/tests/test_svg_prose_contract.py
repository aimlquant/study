"""도해 안에 설명 산문이 남는 것을 막는 계약을 검증한다.

퀀트 ch04 는 이 규칙이 스킬과 템플릿 DESIGN 에 이미 적혀 있는 상태에서 작성됐고,
그럼에도 20장 가운데 22곳에 제목·하단 해설문·우측 설명 패널·차트 위 결과 박스가
들어갔다. 산문 규칙만으로는 막히지 않으므로 게이트로 옮긴다.

판정 기준은 해독 정보와 서술 정보의 구분이다. 축·틱 라벨, 범례, 노드 정체성 라벨,
데이터 점 라벨은 그림을 읽는 데 필요하므로 남고, 제목·캡션·요약 패널·결론은 본문으로
간다. 길이는 그 구분의 프록시다 — 정리된 ch04 의 도형 밖 최장 텍스트가 27자였다.
"""

from __future__ import annotations

import importlib.util

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPO_ROOT / "agent-support" / "scripts" / "validate-site.py"
SPEC = importlib.util.spec_from_file_location("aimlquant_validate_site_svg", VALIDATOR_PATH)
assert SPEC and SPEC.loader
validate_site = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_site
SPEC.loader.exec_module(validate_site)

HEAD = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200">'
    "<style>.t{font-size:12.5px}</style>"
)


def session(tmp: Path, *svg_bodies: str) -> Path:
    """assets/figs 에 SVG 를 놓은 세션 디렉터리를 만든다."""
    figs = tmp / "assets" / "figs"
    figs.mkdir(parents=True, exist_ok=True)
    for index, body in enumerate(svg_bodies):
        (figs / f"fig-{index}.svg").write_text(HEAD + body + "</svg>", encoding="utf-8")
    return tmp


def run(session_dir: Path, baseline: dict[str, list[str]] | None = None) -> list[str]:
    errors: list[str] = []
    validate_site.validate_svg_prose_contract(
        session_dir, errors, baseline=baseline or {}
    )
    return errors


class DecodeLabelsPass(unittest.TestCase):
    """그림을 읽는 데 필요한 라벨은 도형 밖에 있어도 통과한다."""

    def test_axis_legend_and_node_labels_pass(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dir_ = session(
                Path(raw),
                # 축 라벨 · 틱 라벨 · 범례 · 패널 식별 라벨 — 정리된 ch04 의 실제 사례
                '<text class="t" x="200" y="180">연평균 성장률 (CAGR)</text>'
                '<text class="t" x="20" y="30">누적 수익</text>'
                '<text class="t" x="60" y="40">가는 선 — 개별 트리 예측</text>'
                '<text class="t" x="16" y="26">원본 분할 — lr.m · stepwiseLR.m</text>'
                '<rect x="10" y="60" width="120" height="40"/>'
                '<text class="t" x="70" y="84">백 1 · 복제본</text>',
            )
            self.assertEqual([], run(dir_))

    def test_sentence_inside_a_shape_passes(self) -> None:
        """상자 안 서술은 다이어그램 노드의 내용이므로 게이트가 건드리지 않는다."""
        with tempfile.TemporaryDirectory() as raw:
            dir_ = session(
                Path(raw),
                '<rect x="10" y="10" width="380" height="120"/>'
                '<text class="t" x="200" y="60">복원추출이므로 어떤 관측치는 여러 번 들어가고 어떤 것은 빠진다</text>',
            )
            self.assertEqual([], run(dir_))


class ProseInDiagramFails(unittest.TestCase):
    """제목·해설문·설명 패널은 오류다."""

    def test_footer_commentary_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dir_ = session(
                Path(raw),
                '<rect x="10" y="10" width="380" height="100"/>'
                '<text class="t" x="16" y="180">정확한 정규화 계수는 중요하지 않다. 2일·3일 변동성으로 나눠도 된다</text>',
            )
            errors = run(dir_)
            self.assertEqual(1, len(errors), errors)
            self.assertIn("정확한 정규화 계수는", errors[0])

    def test_title_above_the_diagram_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dir_ = session(
                Path(raw),
                '<text class="t" x="16" y="20">교차 검증처럼 나누는 대신, 원 학습셋을 복제해 K개의 백을 만든다</text>'
                '<rect x="10" y="40" width="380" height="120"/>',
            )
            self.assertEqual(1, len(run(dir_)))

    def test_split_tspan_does_not_bypass(self) -> None:
        """tspan 으로 쪼개도 합쳐서 길이를 잰다."""
        with tempfile.TemporaryDirectory() as raw:
            dir_ = session(
                Path(raw),
                '<rect x="10" y="10" width="380" height="100"/>'
                '<text class="t" x="16" y="180">정확한 정규화 계수는'
                "<tspan> 중요하지 않다. 2일·3일 변동성으로 나눠도 된다</tspan></text>",
            )
            self.assertEqual(1, len(run(dir_)))

    def test_short_lines_stacked_into_a_panel_fail(self) -> None:
        """한 줄씩은 짧아도 같은 x 로 쌓이면 설명 패널이다 — fig-source-4-8 우측 패널 사례."""
        with tempfile.TemporaryDirectory() as raw:
            dir_ = session(
                Path(raw),
                '<rect x="10" y="10" width="200" height="180"/>'
                '<text class="t" x="300" y="60">초평면에 가장 가까운</text>'
                '<text class="t" x="300" y="78">점들이며 이들만이</text>'
                '<text class="t" x="300" y="96">경계 위치를 정한다</text>',
            )
            errors = run(dir_)
            self.assertEqual(1, len(errors), errors)
            self.assertIn("묶음", errors[0])

    def test_group_translate_is_composed(self) -> None:
        """<g transform> 안에 숨겨도 좌표를 합성해 도형 밖임을 판정한다."""
        with tempfile.TemporaryDirectory() as raw:
            dir_ = session(
                Path(raw),
                '<rect x="10" y="10" width="100" height="40"/>'
                '<g transform="translate(0 150)">'
                '<text class="t" x="16" y="20">막대가 길수록 좋은 것이 아니다 — 두 막대의 간격이 과적합이다</text>'
                "</g>",
            )
            self.assertEqual(1, len(run(dir_)))

    def test_foreign_object_text_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dir_ = session(
                Path(raw),
                '<rect x="10" y="10" width="380" height="150"/>'
                '<foreignObject x="20" y="20" width="200" height="60">'
                "<div>설명을 HTML 로 우회해 넣는다</div></foreignObject>",
            )
            errors = run(dir_)
            self.assertEqual(1, len(errors), errors)
            self.assertIn("foreignObject", errors[0])


class BaselineRatchet(unittest.TestCase):
    """기존 부채는 정확한 문자열 단위로만 유예되고, 새 위반은 막힌다."""

    PROSE = "정확한 정규화 계수는 중요하지 않다. 2일·3일 변동성으로 나눠도 된다"

    def body(self, *texts: str) -> str:
        marks = "".join(
            f'<text class="t" x="16" y="{180 + i * 40}">{t}</text>'
            for i, t in enumerate(texts)
        )
        return '<rect x="10" y="10" width="380" height="100"/>' + marks

    def test_baselined_string_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dir_ = session(Path(raw), self.body(self.PROSE))
            key = f"{dir_.name}/fig-0.svg"
            baseline = {key: [validate_site.svg_prose_digest(self.PROSE)]}
            self.assertEqual([], run(dir_, baseline))

    def test_new_violation_in_a_baselined_file_still_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            dir_ = session(
                Path(raw),
                self.body(self.PROSE, "이 그림이 말하려는 것은 결국 순위가 뒤집힌다는 사실이다"),
            )
            key = f"{dir_.name}/fig-0.svg"
            baseline = {key: [validate_site.svg_prose_digest(self.PROSE)]}
            errors = run(dir_, baseline)
            self.assertEqual(1, len(errors), errors)
            self.assertIn("순위가 뒤집힌다", errors[0])


class ShippedBaselineIsHonest(unittest.TestCase):
    """저장소에 든 baseline 이 실제 위반과 어긋나지 않는지 확인한다."""

    def test_baseline_has_no_stale_entries(self) -> None:
        if not validate_site.SVG_PROSE_BASELINE_PATH.is_file():
            self.skipTest("baseline 파일 없음")
        recorded = validate_site.load_svg_prose_baseline()
        live: set[str] = set()
        for session_dir in sorted(
            (REPO_ROOT / "html" / "studies").glob("*/presentations/*")
        ):
            errors: list[str] = []
            validate_site.validate_svg_prose_contract(session_dir, errors, baseline={})
            if errors:
                live.add(session_dir.name)
        stale = [
            key
            for key in recorded
            if key.split("/")[0] not in live
        ]
        self.assertEqual(
            [], stale, f"위반이 사라졌으니 baseline 에서 지워야 한다: {stale}"
        )


if __name__ == "__main__":
    unittest.main()
