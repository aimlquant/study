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
  sessions.toml   # 일정·발표자·Webex·회차 수명주기와 공개 video ID
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
- [`Machine Learning for Trading` 3판](materials/quant/active/machine-learning-for-trading-3e)

종료된 교재:

- [`Machine Trading`](materials/quant/archive/machine-trading) — 2026-08-29 종료. 회차 페이지와 교안은 그대로 공개된다.

## 일정·발표자·Webex

스터디는 매주 토요일 Webex에서 진행한다. 발표자와 접속 링크가 미정인 회차는
확정되는 대로 갱신한다. 모바일에 최적화된 일정은 각 스터디의 GitHub Pages에서 볼 수 있다.

- [Quant 전체 일정](https://aimlquant.github.io/study/studies/machine-learning-for-trading-3e/#schedule): 08:00–09:00, 2026-09-05~2027-04-03
- [AI/ML 전체 일정](https://aimlquant.github.io/study/studies/knowledge-graphs-and-llms-in-action/#schedule): 09:00–10:00, 2026-07-25~2026-10-31
- Quant 발표자: 태영, 핀조이 (미정 25회). 9월 5일 오리엔테이션과 마지막 전권 회고는 참석자 전원
- 종료된 스터디: [머신 트레이딩](https://aimlquant.github.io/study/studies/machine-trading/) 2026-07-25~2026-08-29, 08:00–09:00. 발표자 정훈, 종훈, 태호, 태영, 핀조이, 원미
- AI/ML 발표자: 수경, 태영, 종훈(S), 두균, 종훈(L), 재익, 태호, 정훈 (미정 2회)
- 2026-09-26은 추석 연휴로 휴회하며, 이후 AI/ML 회차는 한 주씩 미뤄졌다

### Quant · Machine Trading (종료)

| 날짜 | 시간 | 범위 | 발표자 | Webex | 회차 페이지 |
|---|---|---|---|---|---|
| 2026-07-25 | 08:00–09:00 | Chapter 1 | 정훈 | 종료 | [자료](https://aimlquant.github.io/study/sessions/2026-07-25-machine-trading-ch01/) |
| 2026-08-01 | 08:00–09:00 | Chapter 2 | 종훈 | 종료 | [자료·영상](https://aimlquant.github.io/study/sessions/2026-08-01-machine-trading-ch02/) |
| 2026-08-08 | 08:00–09:00 | Chapter 3 | 태호 | 종료 | [회차](https://aimlquant.github.io/study/sessions/2026-08-08-machine-trading-ch03/) |
| 2026-08-15 | 08:00–09:00 | Chapter 4 | 태영 | 종료 | [자료·영상](https://aimlquant.github.io/study/sessions/2026-08-15-machine-trading-ch04/) |
| 2026-08-22 | 08:00–09:00 | Chapter 5 | 핀조이 | 종료 | [자료](https://aimlquant.github.io/study/sessions/2026-08-22-machine-trading-ch05/) |
| 2026-08-29 | 08:00–09:00 | Chapter 6 | 원미 | 종료 | [자료·영상](https://aimlquant.github.io/study/sessions/2026-08-29-machine-trading-ch06/) |
| 2026-08-29 | 08:00–09:00 | Chapter 7 | 원미 | 종료 | [자료·영상](https://aimlquant.github.io/study/sessions/2026-08-29-machine-trading-ch07/) |

### Quant · Machine Learning for Trading (3판)

| 날짜 | 시간 | 범위 | 발표자 | Webex | 회차 페이지 |
|---|---|---|---|---|---|
| 2026-09-05 | 08:00–09:00 | 오리엔테이션 | 참석자 전원 | 종료 | [자료](https://aimlquant.github.io/study/sessions/2026-09-05-ml4t-orientation/) |
| 2026-09-12 | 08:00–09:00 | Chapter 1 | 태영 | [접속](https://lgehq.webex.com/lgehq-en/j.php?MTID=m9aa5e7d1c892d9f7acd3e6a5cefb6400) | [회차](https://aimlquant.github.io/study/sessions/2026-09-12-ml4t-ch01/) |
| 2026-09-19 | 08:00–09:00 | Chapter 2 | 핀조이 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-09-19-ml4t-ch02/) |
| 2026-10-03 | 08:00–09:00 | Chapter 3 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-10-03-ml4t-ch03/) |
| 2026-10-10 | 08:00–09:00 | Chapter 4 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-10-10-ml4t-ch04/) |
| 2026-10-17 | 08:00–09:00 | Chapter 5 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-10-17-ml4t-ch05/) |
| 2026-10-24 | 08:00–09:00 | Chapter 6 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-10-24-ml4t-ch06/) |
| 2026-10-31 | 08:00–09:00 | Chapter 7 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-10-31-ml4t-ch07/) |
| 2026-11-07 | 08:00–09:00 | Chapter 8 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-11-07-ml4t-ch08/) |
| 2026-11-14 | 08:00–09:00 | Chapter 9 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-11-14-ml4t-ch09/) |
| 2026-11-21 | 08:00–09:00 | Chapter 10 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-11-21-ml4t-ch10/) |
| 2026-11-28 | 08:00–09:00 | Chapter 11 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-11-28-ml4t-ch11/) |
| 2026-12-05 | 08:00–09:00 | Chapter 12 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-12-05-ml4t-ch12/) |
| 2026-12-12 | 08:00–09:00 | Chapter 13 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-12-12-ml4t-ch13/) |
| 2026-12-19 | 08:00–09:00 | Chapter 14 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-12-19-ml4t-ch14/) |
| 2026-12-26 | 08:00–09:00 | Chapter 15 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-12-26-ml4t-ch15/) |
| 2027-01-02 | 08:00–09:00 | Chapter 16 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-01-02-ml4t-ch16/) |
| 2027-01-09 | 08:00–09:00 | Chapter 17 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-01-09-ml4t-ch17/) |
| 2027-01-16 | 08:00–09:00 | Chapter 18 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-01-16-ml4t-ch18/) |
| 2027-01-23 | 08:00–09:00 | Chapter 19 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-01-23-ml4t-ch19/) |
| 2027-01-30 | 08:00–09:00 | Chapter 20 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-01-30-ml4t-ch20/) |
| 2027-02-13 | 08:00–09:00 | Chapter 21 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-02-13-ml4t-ch21/) |
| 2027-02-20 | 08:00–09:00 | Chapter 22 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-02-20-ml4t-ch22/) |
| 2027-02-27 | 08:00–09:00 | Chapter 23 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-02-27-ml4t-ch23/) |
| 2027-03-06 | 08:00–09:00 | Chapter 24 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-03-06-ml4t-ch24/) |
| 2027-03-13 | 08:00–09:00 | Chapter 25 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-03-13-ml4t-ch25/) |
| 2027-03-20 | 08:00–09:00 | Chapter 26 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-03-20-ml4t-ch26/) |
| 2027-03-27 | 08:00–09:00 | Chapter 27 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-03-27-ml4t-ch27/) |
| 2027-04-03 | 08:00–09:00 | 전권 회고 | 참석자 전원 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2027-04-03-ml4t-retrospective/) |

### 운영 회차 (정본 목록은 [운영 페이지](https://aimlquant.github.io/operations/))

교재 진도와 별도로 진행한 운영 논의 중 회차 페이지가 필요한 것만 `kind = "operations"`로 등록한다.
교재 일정표와 허브 일정에는 나오지 않으며, 운영 논의 목록의 정본은 조직 운영 페이지다.
회차 페이지 주소는 공개 영상 설명이 가리키므로 바꾸지 않는다.

| 날짜 | 시간 | 주제 | 발표자 | Webex | 회차 페이지 |
|---|---|---|---|---|---|
| 2026-09-05 | 08:00–09:00 | 다음 교재·스터디 운영 논의 (오리엔테이션 사전 읽기) | 참석자 전원 | 종료 | [자료·영상](https://aimlquant.github.io/study/sessions/2026-09-12-machine-trading-next-study-discussion/) |

### AI/ML · Knowledge Graphs and LLMs in Action

| 날짜 | 시간 | 범위 | 발표자 | Webex | 회차 페이지 |
|---|---|---|---|---|---|
| 2026-07-25 | 09:00–10:00 | Chapter 1–2 | 수경 | 종료 | [자료](https://aimlquant.github.io/study/sessions/2026-07-25-kg-llm-ch01-ch02/) |
| 2026-08-01 | 09:00–10:00 | Chapter 3 | 태영 | 종료 | [자료·영상](https://aimlquant.github.io/study/sessions/2026-08-01-kg-llm-ch03/) |
| 2026-08-08 | 09:00–10:00 | Chapter 4 | 종훈(S) | 종료 | [회차](https://aimlquant.github.io/study/sessions/2026-08-08-kg-llm-ch04/) |
| 2026-08-15 | 09:00–10:00 | Chapter 5 | 두균 | 종료 | [자료·영상](https://aimlquant.github.io/study/sessions/2026-08-15-kg-llm-ch05/) |
| 2026-08-22 | 09:00–10:00 | Chapter 6 | 종훈(L) | 종료 | [자료](https://aimlquant.github.io/study/sessions/2026-08-22-kg-llm-ch06/) |
| 2026-08-29 | 09:00–10:00 | Chapter 7 | 재익 | 종료 | [자료·영상](https://aimlquant.github.io/study/sessions/2026-08-29-kg-llm-ch07/) |
| 2026-09-05 | 09:00–10:00 | Chapter 8 | 태호 | 종료 | [자료](https://aimlquant.github.io/study/sessions/2026-09-05-kg-llm-ch08/) |
| 2026-09-12 | 09:00–10:00 | Chapter 9 | 정훈 | [접속](https://lgehq.webex.com/lgehq-en/j.php?MTID=m9aa5e7d1c892d9f7acd3e6a5cefb6400) | [회차](https://aimlquant.github.io/study/sessions/2026-09-12-kg-llm-ch09/) |
| 2026-09-19 | 09:00–10:00 | Chapter 10 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-09-19-kg-llm-ch10/) |
| 2026-10-03 | 09:00–10:00 | Chapter 11 | 미정 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-10-03-kg-llm-ch11/) |
| 2026-10-10 | 09:00–10:00 | Chapter 12 | 재익 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-10-10-kg-llm-ch12/) |
| 2026-10-17 | 09:00–10:00 | Chapter 13 | 정훈 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-10-17-kg-llm-ch13/) |
| 2026-10-24 | 09:00–10:00 | Chapter 14 | 종훈(L) | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-10-24-kg-llm-ch14/) |
| 2026-10-31 | 09:00–10:00 | Chapter 15 | 태영 | 추후 공지 | [회차](https://aimlquant.github.io/study/sessions/2026-10-31-kg-llm-ch15/) |

날짜·챕터·발표자·Webex 링크·발행 상태의 정본은
[`agent-support/sessions.toml`](agent-support/sessions.toml)이다. 참여자는
[`QUICKSTART.md`](QUICKSTART.md)에서 준비·발행 흐름을 확인할 수 있다.

## 정본과 이전 저장소

2026-07-31 병합 이후 새 일정·교재 경로·공개 회차의 정본은 이 저장소다.
`ds4th_study`와 `ml4t`는 이전 이력과 병합 전 자료를 보존하는 출처이며, 다시 가져올 때는
공개 커밋과 범위를 [`agent-support/migrations.toml`](agent-support/migrations.toml)에 기록한다.
원본 저장소의 로컬 미커밋 변경은 자동으로 포함하지 않는다.

- 이전 AI/ML 기록: <https://github.com/restful3/ds4th_study>
- 이전 ML4T 기록: <https://github.com/restful3/ml4t>

## 공개 자료의 권리 경계

업스트림 코드가 공개되어 있어도 책 본문·표·그림의 재배포 권리까지 자동으로 생기지는 않는다.
권리 확인 없는 책 그림·표 스캔은 새로 추가하지 않고 자체 도식과 최소 인용을 사용한다.
현재 Knowledge Graph 교재 노트북에 포함된 책 그림 attachment는 승인된 예외가 아니라
삭제·재도식화·비공개 전환 중 방침 결정이 필요한 알려진 항목이다.

## 로컬 검증

```bash
uv run --with 'nbformat>=5,<6' python -m unittest discover -s agent-support/tests -v
python3 agent-support/scripts/build_site.py
python3 agent-support/scripts/build_site.py --check
python3 agent-support/scripts/validate-site.py --site html
git diff --check
```

공개 사이트 기준 URL은 <https://aimlquant.github.io/study/>이고,
YouTube 채널은 [@aimlquant](https://www.youtube.com/@aimlquant)다.
