# 스터디 교안·YouTube 연결 절차

## 정본과 상태

`agent-support/sessions.toml`을 날짜·챕터·발표자·공개 Webex 접속 링크·발행 상태를
포함한 공개 회차 메타데이터의 정본으로 사용한다. `meeting_url`은 실제 접속 URL이
확정된 회차에만 기록하고 `#` 같은 임시 링크를 넣지 않는다. 종료된 회차는 접속
URL을 제거하고 `meeting_status = "ended"`로 바꾸어 오래된 접속 버튼을 노출하지 않는다.
허용 상태와 의미는 다음과 같다.

- `scheduled`: 일정만 등록됨
- `materials-published`: 회차 페이지와 하나 이상의 교안 산출물이 공개됨
- `video-public`: 교안이 공개됐고 승인된 공개 YouTube 영상이 연결됨
- `cancelled`: 취소된 회차

## 1. 회차 URL을 먼저 확정

전역에서 고유한 소문자 ASCII `session_id`를 정한다. 공개 회차 URL은
`https://restful3.github.io/aimlquant/sessions/<session_id>/`이며 이후 바꾸지 않는다.
영상이 없어도 회차 페이지는 정상적으로 발행되어야 한다.

2026-08-01 저장소 리브랜딩으로 기존
`https://restful3.github.io/ai-odyssey-study/` 기준 URL을 위 주소로 한 번 이관했다.
GitHub는 저장소 이름 변경 시 project Pages URL을 자동 리디렉션하지 않으므로,
이 시점 이후 외부 링크와 새 회차는 `aimlquant` 기준 URL만 사용한다.

## 2. 교안을 먼저 발행

리포트·발표자료를 `html/studies/<study-slug>/presentations/<session-slug>/`에 둔다.
`artifacts`에 사이트 루트 기준 상대 URL을 등록하고 상태를
`materials-published`로 바꾼다. 사이트를 빌드·검증하고 실제 렌더를 확인한다.

## 3. 영상 설명에서 Pages로 연결

비공개 `ai-odyssey` 운영 저장소의 업로드 단위에 같은 `session_id`를 사용한다.
YouTube 설명의 관련 자료 링크는 위 회차 URL을 사용한다. 업로드 준비·비공개·일부공개
단계의 video ID는 공개 저장소로 복사하지 않는다.

## 4. 공개 영상만 역연결

영상·제목·설명·자막·썸네일이 승인되고 YouTube 상태가 실제 `public`인지 확인한다.
그 뒤 `youtube_video_id`를 추가하고 상태를 `video-public`으로 바꾼다. 사이트를 다시
빌드하면 회차 페이지에 영상 플레이어와 YouTube 링크가 생긴다.

## 5. 검증

```bash
uv run --with 'nbformat>=5,<6' python -m unittest discover -s agent-support/tests -v
python3 agent-support/scripts/build_site.py
python3 agent-support/scripts/build_site.py --check
python3 agent-support/scripts/validate-site.py --site html --check-materials
git diff --check
```

회차 페이지 URL이 YouTube 설명과 일치하고, Pages의 video ID가 공개 영상과 일치하며,
발표자료가 회차 페이지로 돌아오는 링크를 제공하는지 확인한다.
