@AGENTS.md

## Claude Code

- 프로젝트 스킬의 정본은 `.agents/skills/`이지만 Claude Code는 그 경로를 읽지 못한다.
  Claude용 사본은 `.claude/skills/`에 둔다. 스킬 본문을 고칠 때는 두 경로를 함께 갱신한다.
- 회차 리포트·발표자료는 `study-presentation`, 교재 코드와 해설 노트북은 `study-materials`,
  회차 등록·Pages 발행·공개 영상 연결은 `study-operations`, 교재 이미지의 한국어화는
  `localize-image-text` 스킬을 사용한다.
- 스킬이 안내하는 `agent-support/templates/STUDY_SESSION_BLUEPRINT.md`와 두 템플릿의
  `DESIGN.md`를 리포트·슬라이드·자동 목차의 공통 품질 기준으로 사용한다.
- `.claude/settings.local.json`은 개인 설정이므로 공유하거나 공용 설정으로 복사하지 않는다.
