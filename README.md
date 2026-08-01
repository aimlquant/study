# AIML Quant

AIML Quant의 공개 학습 허브다. AI/ML과 Quant 두 스터디의 교재,
회차별 리포트·발표자료, 공개된 YouTube 영상을 하나의 안정적인 URL 체계로 연결한다.

현재 진행 교재와 기존 공개 발표자료는 각각 `ds4th_study`, `ml4t`의
검증된 Git 스냅숏에서 가져왔다. 원본 저장소의 로컬 미커밋 변경은 가져오지 않았다.
단, 기존 ignore 규칙에 잘못 제외된 Chapter 12의 필수 Python 리스팅 5개는
비밀값·캐시를 제외하고 보완했으며 내역은 마이그레이션 원장에 남겼다.

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
materials/
  aiml/
    active/       # 현재 AI/ML 교재
    archive/      # 종료된 AI/ML 교재
  quant/
    active/       # 현재 퀀트 교재
    archive/      # 종료된 퀀트 교재
html/             # GitHub Pages 배포 산출물
```

현재 교재:

- [`Knowledge Graphs and LLMs in Action`](materials/aiml/active/knowledge-graphs-and-llms-in-action)
- [`Machine Trading`](materials/quant/active/machine-trading)

이전 기록은 `agent-support/migrations.toml`에서 원본 저장소와 커밋 단위로 확인한다.

## 로컬 검증

```bash
uv run --with 'nbformat>=5,<6' python -m unittest discover -s agent-support/tests -v
python3 agent-support/scripts/build_site.py
python3 agent-support/scripts/build_site.py --check
python3 agent-support/scripts/validate-site.py --site html --check-materials
```

공개 사이트 기준 URL은 <https://restful3.github.io/aimlquant/>이고,
YouTube 채널은 [@aimlquant](https://www.youtube.com/@aimlquant)다.
