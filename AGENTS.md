# AIML Quant agent guide

## Purpose

- 이 저장소는 AI/ML과 ML4T 스터디의 공개 교재·발표자료·GitHub Pages를 관리한다.
- 공개 YouTube 채널과 회차 페이지는 `session_id`로 연결한다.
- 기본 응답 언어는 한국어로 하되 코드·명령어·고유명사는 원문을 유지한다.

## Repositories

- `aimlquant/study` (공개, 이 저장소): `html/` 공개 산출물과 `agent-support/` 도구
- `aimlquant/study-materials` (비공개): 교재 원문·해설·소스. 스터디 참가자에게 공개
- 로컬은 `aimlquant/` 아래 `study/`와 `study-materials/`를 나란히 둔다

저장소 이름이 곧 공개 URL 경로다. `study` → `https://aimlquant.github.io/study/`.

## Directory lifecycle

- `study-materials/aiml/active/`: 현재 AI/ML 교재
- `study-materials/aiml/archive/`: 종료된 AI/ML 교재
- `study-materials/quant/active/`: 현재 퀀트 교재
- `study-materials/quant/archive/`: 종료된 퀀트 교재
- `html/`: GitHub Pages에 그대로 배포되는 공개 HTML·자산
- `agent-support/`: 레지스트리, 절차, 생성·검증 도구

교재가 끝나면 해당 분야의 `active/<study-slug>`를
`archive/<study-slug>`로 이동하고 레지스트리를 함께 갱신한다.
`html/studies/<study-slug>`의 공개 URL은 교재 이동과 무관하게 유지한다.

`studies.toml`의 `materials_path`는 `materials/<track>/...` 형식을 유지한다.
이는 교재 저장소 안의 논리 좌표이며, 안내 페이지가 앞의 `materials/`를 떼고
링크를 만든다.

## Sources of truth

- `agent-support/site.toml`: 브랜드, 저장소, Pages, 공개 YouTube 채널
- `agent-support/studies.toml`: 진행 교재와 공개 경로
- `agent-support/sessions.toml`: 일정, 발표자, 공개 Webex, 발행 상태, 공개 YouTube video ID
- 새 Webex 링크를 받으면: 회차별 `meeting_url`에 넣기 → build·push로 게시 → 실제 회차·과정 페이지를 열어 링크 확인 → `media/scripts/study_links.py sync-calendar --date <토요일> --apply`로 캘린더를 맞추고 `check`로 페이지·캘린더·녹화 run 일치 확인 → 보고. 비밀번호는 공개 페이지에 넣지 않는다.
- 회차 일정·회의 안내는 한 묶음으로 끝낸다: 회차·링크를 `sessions.toml` 정본에 반영 → 실제 회차·과정 페이지·README·캘린더(`study_links.py sync-calendar`·`check`)·녹화 run 확인 → 카톡 공지 문안을 만들어 운영자 확인 → 카톡방 글 게시 → 방 공지 등록(기존 공지는 내리고 글은 지우지 않음) → 카톡 화면에서 실제로 보이는지 확인 → 운영 창구에 보고.
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
uv run --with 'nbformat>=5,<6' python -m unittest discover -s agent-support/tests -v
python3 agent-support/scripts/build_site.py
python3 agent-support/scripts/build_site.py --check
python3 agent-support/scripts/validate-site.py --site html
git diff --check
```

교재 내용을 검증하는 테스트는 `study-materials`가 없으면 건너뛴다. 교재를
건드리는 작업이면 두 저장소를 함께 놓고 전체를 돌린다.

```bash
ln -sfn ../study-materials materials   # 검증 뒤 rm materials
```

HTML·CSS·SVG를 변경하면 실제 GitHub Pages 표시 크기의 데스크톱·모바일 렌더를
확인한다. 텍스트 잘림, 불균형, 깨진 링크, 영상 프레임 비율을 DOM 검사만으로
판정하지 않는다.
