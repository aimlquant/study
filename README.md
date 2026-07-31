# AI Odyssey Study

AI 오딧세이 스터디의 공개 학습 허브다. AI/ML과 ML4T 두 스터디의 교재,
회차별 리포트·발표자료, 공개된 YouTube 영상을 하나의 안정적인 URL 체계로 연결한다.

## 발행 순서

1. 스터디 일정을 등록한다 (`scheduled`).
2. 스터디 후 리포트·발표자료를 GitHub Pages에 먼저 발행한다 (`materials-published`).
3. YouTube 설명에 이미 발행된 회차 페이지 URL을 넣어 영상을 업로드한다.
4. 영상이 최종 승인되어 `public`이 된 뒤에만 video ID를 이 저장소에 등록한다
   (`video-public`).
5. 사이트를 다시 빌드하면 회차 페이지에서 영상과 YouTube 링크가 활성화된다.

비공개·일부공개 영상 ID, OAuth 정보, 원본 녹화, 자막 작업본과 업로드 원장은
비공개 `ai-odyssey` 운영 저장소에서만 관리한다.

## 저장소 구조

```text
agent-support/
  site.toml       # 브랜드·GitHub Pages·YouTube 공개 채널
  studies.toml    # 진행 교재와 공개 자료 경로
  sessions.toml   # 회차 수명주기와 공개 video ID
  scripts/        # 결정적 사이트 생성기
  procedures/     # 에이전트 공통 운영 절차
materials/active/ # 진행 중 교재(순차 이전)
docs/             # GitHub Pages 배포 산출물
```

## 로컬 검증

```bash
python3 -m unittest discover -s agent-support/tests -v
python3 agent-support/scripts/build_site.py
python3 agent-support/scripts/build_site.py --check
```

공개 사이트 기준 URL은 <https://restful3.github.io/ai-odyssey-study/>이고,
YouTube 채널은 [AI 오딧세이 스터디](https://www.youtube.com/@ai_odyssey_study)다.
