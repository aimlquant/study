# 8장 읽기 쉬움 B · 레인 ch08rb 결과

- task: `83fe65a6276a` / 도라 16341.
- 규칙 기준: `e382f456846a3c12c6c900a0697095946dd6fb5c`, 단계 1 C3 AGREED.
- 본문 커밋: `7d15a8bcba22e0f1e495e45c855f39a60e38c004`.
- 브랜치: `ch08rb-readability-b-20261101`.
- worktree: `/tmp/aimlquant-study-ch08rb-83fe65`.
- 산출물: `html/studies/machine-learning-for-trading-3e/presentations/2026-11-07-ch08/report.html`.
- 공개 push 0, 옛 `.study-*` worktree 수정 0.

## 변경 범위와 작성자 확인

8.3–8.7을 읽고 새 규칙에 맞춰 8.3–8.6 문장을 고쳤다. 8.7은 추가 재작성이 필요한 문단을 찾지 못해 그대로 뒀다. 기존 판정표 230문단 중 막힘 66개 모두를 다뤘다. 판정표 기준 수정은 99문단이며 짧은 식 도입부도 작은 예·상황으로 연결했다. 출처·저장 출력·구현 대조 38개 항목을 절 끝 텍스트 전용 메모 3개로 모았다.

이 기록은 레인 작성자의 자가점검이다. 전체 독립 읽기, 막힘 0 판정, 한국어 정식 관문이나 통합 C3를 대신하지 않는다.

| 절 | 기존 막힘 수정 | 판정표 문단 수정 | 메모 항목 | 그림 | 번호 있는 표 | 표시식 |
|---|---:|---:|---:|---:|---:|---:|
| 8.3 | 19/19 | 33 | 12 | 15 | 2 | 11 |
| 8.4 | 17/17 | 20 | 9 | 10 | 0 | 5 |
| 8.5 | 5/5 | 7 | 0 | 4 | 0 | 1 |
| 8.6 | 25/25 | 39 | 17 | 12 | 3 | 17 |
| 8.7 | 0/0 | 0 | 0 | 3 | 0 | 0 |

8.7에는 번호 없는 용어표 1개가 별도로 있다. 표의 그림·표·식 수는 전후 동일하다.

다룬 기존 막힘 idx:

- 8.3: 286, 297, 299, 302, 305, 307, 310, 311, 317, 323, 324, 332, 334, 337, 349, 362, 363, 366, 368.
- 8.4: 380, 383, 384, 389, 393, 395, 396, 397, 404, 410, 415, 419, 422, 428, 429, 432, 435.
- 8.5: 439, 444, 456, 458, 459.
- 8.6: 479, 487, 491, 492, 493, 497, 498, 499, 500, 537, 540, 544, 548, 553, 554, 556, 560, 564, 581, 582, 586, 587, 588, 594, 596.

## 보존 검사

- 전체 그림 73개, 번호 있는 표 10개 및 용어표 1개, 코드 블록 7개의 HTML 직렬화가 기준본과 동일하다.
- 전체 표시식 58개와 인라인식 4개의 LaTeX 문자열·순서가 동일하다. 합계 62개다.
- 기존 id 누락·중복 0. 새 id는 `s83-verification`, `s84-verification`, `s86-verification` 세 개뿐이다. 식 풀이 purpose/symbols/example id를 본문 학습 위치에 유지했다.
- `source-inventory.json`, `presentation.toml`, 회차 `assets/report.css`는 기준 커밋과 바이트가 같다. 원장 대응과 reader_review 설정을 변경하지 않았다.
- 8.3 이전 바이트와 8.7 절 전체는 기준본과 같다. 레인 A 범위 변경 0.
- 절별 기존 숫자 토큰 집합의 누락 0, 기존 href 집합의 누락 0. 대조 수치·셀 번호·사례 경로는 메모 본문에 남겼다.
- 검증 메모에는 텍스트와 제목만 있으며 그림·표·코드·수식·접힌 details는 없다.
- 이해용 추가 예의 VIX 16/40=0.4를 검산했다. 식 해설에 옮긴 기존 예도 롤 수익률·곡률·동종 편차·타깃 인코딩·AR·CAR·CAAR 산술을 직접 확인했다.

## 검증 결과

- `uv run --with 'nbformat>=5,<6' python -m unittest discover -s agent-support/tests -v`: 345개 실행, OK, 5개 건너뜀. 건너뜀은 선택 패키지 httpx/neo4j/openai 부재다.
- `python3 agent-support/scripts/build_site.py`: 통과, 다른 생성 파일 변경 0.
- `python3 agent-support/scripts/build_site.py --check`: 통과.
- `python3 agent-support/scripts/validate-site.py --site html --check-materials`: 기준본 오류 20개, 레인 최종본 21개. 추가 오류는 8장 `content_review report hash is stale` 하나다. 기존 5·6장 원본 제목·덱 좌표 오류는 증가하지 않았다. 기준본은 별도 /tmp 사이트 사본에 원래 8장 report를 둬 같은 검증기로 비교했다.
- 낡은 내용 검토 해시를 자동 갱신하지 않았다. 통합 뒤 실제 검토 담당자가 내용 검토 기록과 전체 읽기 기록을 갱신해야 한다.
- `git diff --check`: 통과.
- `check-svg-bboxes.mjs`를 h1-run 4G/120초로 PC 1440·모바일 390에서 각각 실행: 그림 73개, 수식 62개, 둘 다 passed, math findings 0. 기존 로컬 npx 캐시의 Puppeteer를 NODE_PATH로 사용했다.
- 소유자 설치본 safe-browser-shot으로 최종 HTML의 PC 1440×1800 본문과 모바일 390×2400 검증 메모를 캡처해 실제 이미지를 확인했다.
- 같은 설치본으로 A4 PDF 119쪽 생성. inspect-study-pdf로 전쪽 래스터 생성 및 raw delimiter 부재 62개 확인. 대표 84·99·112쪽을 실제로 열어 문장·메모·식·그림을 확인했다. PDF 전쪽 육안 검수는 수행하지 않았다.
- 메모 제목은 기존 `.sub-h4`가 적용된 h4로 두어 A4에서 제목만 앞쪽 끝에 남지 않게 했다.

## 통합 담당자에게

- 레인 A의 CSS를 통합해야 `.verification-note` 테두리·배경이 적용된다. rb는 지시대로 회차 CSS를 수정하지 않았다. 현재 캡처는 이 CSS를 받기 전의 중간 상태다.
- `reader_review`는 켜지 않았다. 옛 내용 검토/독자 검토 기록도 수정하지 않았다.
- 레인 A와 합친 뒤 build/validate, 실제 전체 독자 검수, 한국어 관문, 최종 PC·모바일·A4 검수를 다시 해야 한다.
- 본문 커밋 `7d15a8b` 뒤의 별도 결과 메모 커밋까지 레인 브랜치에 보존한다. 원격 push는 하지 않는다.

## 로컬 증거와 해시

- 기준 report SHA-256: `5c13fa53915bc90a620226831894208885ccd1f3e01e3208a0bf7da57ce78d57`.
- 레인 report SHA-256: `7ff743f83e2e86f84f6849d35865fcf414f41670cd7fc555dcd666d909ebb891`.
- 보존 상세: `/tmp/ch08rb-preservation-final.json`.
- 수정 idx 목록: `/tmp/ch08rb-edit-map.json`.
- 테스트: `/tmp/ch08rb-tests-final.log`.
- build: `/tmp/ch08rb-build.log`, `/tmp/ch08rb-build-check-final.log`.
- validate: `/tmp/ch08rb-validate-baseline.log`, `/tmp/ch08rb-validate-final.log`.
- DOM: `/tmp/ch08rb-qa/bbox-pc.json`, `/tmp/ch08rb-qa/bbox-mobile.json`.
- PNG: `/tmp/ch08rb-final-s83-pc.png`, `/tmp/ch08rb-final-note-mobile.png`.
- PDF: `/tmp/ch08rb-qa/tmp/browser-shots/ch08rb-final-report.pdf`.
- PDF 확인: `/tmp/ch08rb-pdf-inspect-final.log`, `/tmp/ch08rb-qa/tmp/browser-shots/pdf-final-pages/`.
