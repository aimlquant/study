# AIML Quant agent guide

## Purpose

- 이 저장소는 AI/ML과 ML4T 스터디의 공개 교재·발표자료·GitHub Pages를 관리한다.
- 공개 YouTube 채널과 회차 페이지는 `session_id`로 연결한다.
- 기본 응답 언어는 한국어로 하되 코드·명령어·고유명사는 원문을 유지한다.

## Directory lifecycle

- `materials/aiml/active/`: 현재 AI/ML 교재
- `materials/aiml/archive/`: 종료된 AI/ML 교재
- `materials/quant/active/`: 현재 퀀트 교재
- `materials/quant/archive/`: 종료된 퀀트 교재
- `html/`: GitHub Pages에 그대로 배포되는 공개 HTML·자산
- `agent-support/`: 레지스트리, 절차, 생성·검증 도구

교재가 끝나면 해당 분야의 `active/<study-slug>`를
`archive/<study-slug>`로 이동하고 레지스트리를 함께 갱신한다.
`html/studies/<study-slug>`의 공개 URL은 교재 이동과 무관하게 유지한다.

## Sources of truth

- `agent-support/site.toml`: 브랜드, 저장소, Pages, 공개 YouTube 채널
- `agent-support/studies.toml`: 진행 교재와 공개 경로
- `agent-support/sessions.toml`: 회차, 발행 상태, 공개 YouTube video ID
- `agent-support/procedures/study-lifecycle.md`: 교안과 영상의 양방향 연결 절차

## Safety boundaries

1. `youtube_video_id`는 영상이 승인되어 실제 `public`이 된 뒤에만 기록한다.
2. private 또는 unlisted video ID, OAuth 토큰, 쿠키, 클라이언트 비밀, 로컬 녹화 경로,
   업로드 복구 원장은 이 공개 저장소에 넣지 않는다.
3. 회차 페이지 URL은 영상보다 먼저 만들고 이후 변경하지 않는다.
4. YouTube 설명은 해당 회차 페이지를 링크하고, 회차 페이지는 공개 영상만 링크한다.
5. 사용자 변경을 보존하고 관련 없는 파일을 되돌리지 않는다.
6. 커밋, push, Pages 설정 변경은 사용자가 요청한 범위에서만 수행한다.

## Required verification

변경 뒤 다음을 실행한다.

```bash
python3 -m unittest discover -s agent-support/tests -v
python3 agent-support/scripts/build_site.py
python3 agent-support/scripts/build_site.py --check
python3 agent-support/scripts/validate-site.py --check-materials
git diff --check
```

HTML·CSS·SVG를 변경하면 실제 GitHub Pages 표시 크기의 데스크톱·모바일 렌더를
확인한다. 텍스트 잘림, 불균형, 깨진 링크, 영상 프레임 비율을 DOM 검사만으로
판정하지 않는다.
