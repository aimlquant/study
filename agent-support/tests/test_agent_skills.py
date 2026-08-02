from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CODEX_SKILLS = REPO_ROOT / ".agents" / "skills"
CLAUDE_SKILLS = REPO_ROOT / ".claude" / "skills"


def skill_names(root: Path) -> set[str]:
    return {entry.name for entry in root.iterdir() if not entry.name.startswith(".")}


class ClaudeSkillMirrorTest(unittest.TestCase):
    """Claude Code discovers project skills only under `.claude/skills`, while
    Codex reads `.agents/skills`. The mirror is a symlink rather than a second
    copy so the two harnesses cannot drift onto different instructions."""

    def test_every_codex_skill_is_exposed_to_claude(self) -> None:
        self.assertEqual(skill_names(CODEX_SKILLS), skill_names(CLAUDE_SKILLS))

    def test_each_mirror_is_a_symlink_to_its_codex_skill(self) -> None:
        for name in sorted(skill_names(CODEX_SKILLS)):
            mirror = CLAUDE_SKILLS / name
            with self.subTest(skill=name):
                self.assertTrue(
                    mirror.is_symlink(),
                    f"{mirror} must be a symlink into .agents/skills, not a copy",
                )
                self.assertEqual(mirror.resolve(), (CODEX_SKILLS / name).resolve())

    def test_each_mirror_resolves_to_a_readable_skill(self) -> None:
        for name in sorted(skill_names(CODEX_SKILLS)):
            with self.subTest(skill=name):
                self.assertTrue((CLAUDE_SKILLS / name / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
