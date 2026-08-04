# 발표자료 품질 루프 기록 · 2026-08-03

## 범위

- 표본: `knowledge-graphs-and-llms-in-action` Chapter 1·2·3
- 원자료: `study-materials`의 각 장 한국어 해설판
- 산출물: 공개 `report.html`, `index.html`, SVG·CSS·JS, A4 PDF 렌더
- 검토자: Codex, Claude
- 종료 상한: 5라운드

이 기록은 작업 트리 기준이다. 커밋·push·배포는 이 품질 루프의 범위가 아니다.

## 라운드 1 · 기준선 감사와 1차 수정

### 기준선 결함

| 등급 | 증거 | 영향 | 수정 위치 |
| --- | --- | --- | --- |
| 중대 | Chapter 1 그림 1.5가 원본의 LLM·KG 강점/약점 비교축을 역할 상자로 바꿈 | 원본 그림의 핵심 의미와 항목 누락 | 회차 SVG·캡션 |
| 중대 | Chapter 1 그림 1.1의 화살표 하나가 개체 경계가 아닌 빈 공간에서 시작 | 관계의 주어와 방향을 잘못 읽게 함 | 회차 SVG |
| 보완 | Chapter 1·2 도입, 학습 지도, 확인 질문이 거의 같은 범용 문구 | 장별 논증 흐름과 학습 목표 식별이 어려움 | 스킬·덱·리포트 |
| 보완 | Chapter 1·2 일부 절이 제목과 요약만 남고 정의·메커니즘·예·경계가 충분히 연결되지 않음 | 원자료 없이 독립 학습하기 어려움 | 스킬·리포트·덱 |
| 보완 | AIML Quant의 검증·운영 보충이 원자료의 목소리와 섞임 | 주장 주체와 원본 범위를 오인할 수 있음 | 스킬·리포트·SVG·덱 |
| 보완 | 공개 화면에 `Source Section`, `Section 00`, `One Sentence` 같은 제작 표지가 남음 | 학습 문서의 완결성과 한국어 독해 흐름 저하 | 리포트 |
| 보완 | 연속 브라우저 캡처가 transient service 종료와 다음 시작 사이에서 간헐적으로 충돌 | 최종 크기 시각 검사가 불안정 | 렌더 드라이버 |
| 보완 | 리포트 해시 복원 직전에 문서 맨 위로 이동하는 프레임이 있음 | 자동 캡처가 깊은 링크에서 빈 화면을 잡을 수 있음 | 보고서 템플릿·1~3장 런타임 |

### 채택과 구현

- 스킬: 절별 설명 payload, 장 고유의 도입·학습 지도·요약·질문, AIML Quant 보충의
  가시적 구분, 재구성 그림의 비교축·방향·상태 보존 규칙을 추가했다. 품질 루프의
  결함·결정·파일·검증 증거를 `agent-support/reviews/`에 영구 기록하도록 명시했다.
- 절차: 여섯 품질 게이트, 최대 5라운드, 상호 충분 종료 조건, 결함 등급과 수정 계층을
  `presentation-quality-loop.md`로 고정했다.
- Chapter 1: 그림 1.1·1.4·1.5를 의미와 연결 규칙에 맞게 고치고, 본문 설명과 도입·지도·
  확인 질문을 확장했다. 새 검증 게이트는 `AIML Quant 보충`으로 표시했다.
- Chapter 2: 장 고유의 지능형 시스템 분해와 hybrid system 논증으로 도입·지도·질문을
  교체하고, 핵심 하위 절의 메커니즘과 사례를 확장했다.
- Chapter 3: 영문 제작 표지를 학습자용 한국어 표지로 바꿨다.
- 템플릿·도구: 해시 복원 중 불필요한 top reset을 제거하고, guarded capture 사이에
  transient service handoff 간격을 두었다.

### Codex 판정

| 품질 게이트 | 1차 수정 후 판정 | 근거 |
| --- | --- | --- |
| 원본 구조 충실성 | 충분 | source-fidelity 좌표·제목·필수 그림 검사 통과, 그림 1.5 항목 복원 |
| 의미와 주장 충실성 | 충분 | 추가 검증·운영 해설을 가시적으로 구분하고 캡션·alt·도형을 일치시킴 |
| 독립 문서 완결성 | 충분 | Chapter 1·2 설명 payload와 장 고유의 논증 지도를 보강 |
| 학습성과 설명성 | 충분 | 그림 읽는 법·중요성·경계와 사례의 입력–역할–검증 연결 확인 |
| 발표·시각 품질 | 충분 | 최종 크기 덱, 모바일, 리포트, A4 실제 픽셀 검사에서 잘림·겹침 없음 |
| 추적성과 출판 무결성 | 충분 | report ref·source ref·링크·사이트 검증과 전체 테스트 통과 |

### 검증 증거

- 덱 1600×900 전체: Chapter 1 19장, Chapter 2 22장
- 변경 슬라이드 1366×768 및 390×844, 리포트 desktop/mobile anchor 캡처
- A4 PDF: Chapter 1 14쪽, Chapter 2 18쪽, Chapter 3 25쪽
- 총 81개 guarded capture를 실제 픽셀로 검사
- `uv run --with 'nbformat>=5,<6' python -m unittest discover -s agent-support/tests -v`:
  208 tests, 6 optional skips, 통과
- `build_site.py`, `build_site.py --check`, `validate-site.py --site html`,
  `git diff --check`: 통과. 외부 YouTube iframe 수동 검토 경고 2건만 존재

### 라운드 상태

Codex는 여섯 게이트를 모두 충분으로 판정했다. Claude 독립 검토가 아직 대기열에 있어
상호 충분 종료 조건은 충족하지 않았다. Claude 지적을 받으면 증거와 대조해 라운드 2
채택·기각·보류를 이 문서에 이어 기록한다.

## 라운드 2 · 검토 이력의 영속성 감사

### Codex 추가 지적과 채택

| 등급 | 증거 | 판단과 조치 |
| --- | --- | --- |
| 보완 | 절차에 라운드 기록 형식은 있었지만 저장 위치와 복원 가능한 최소 정보가 고정되지 않음 | 채택. `agent-support/reviews/presentation-quality-loop-YYYY-MM-DD.md`를 표준 원장으로 정하고, 같은 날 여러 루프의 이름 규칙을 추가 |
| 보완 | 스킬이 품질 절차를 참조하지만 미래 작업자가 채팅 기록 없이 과거 결함·결정·파일·증거를 복원해야 한다는 요구가 없음 | 채택. Checkpoint 5에 영구 원장과 최소 복원 정보 요구를 추가 |

### 검증과 상태

- `study-presentation` skill quick validation: 통과
- `git diff --check`: 통과
- Claude 요청 `452368ef1db44cc7be716ca1e398baf9`: queued

Claude 창에 다른 사용자 입력이 미전송 상태로 남아 있어 peer-council의 안전 알림이 기존
입력을 덮어쓰지 않고 대기한다. 이 외의 Codex 2차 감사 항목은 현재 모두 충분이며,
Claude 응답 전에는 상호 충분으로 종료하지 않는다.

### 중단 상태

동일한 외부 상태가 세 번의 연속 goal turn에서 확인됐다. `study:1` Claude 입력창에는
`HANDOFF.md 갱신해줘`가 미전송 상태이고, 독립 검토 요청
`452368ef1db44cc7be716ca1e398baf9`는 계속 queued다. peer-council은 기존 사용자 입력을
덮어쓰지 않도록 알림을 보내지 않는 것이 정상 동작이다.

사용자가 해당 입력을 제출하거나 지운 뒤 이 품질 루프를 재개하면, 같은 request ID를
다시 nudge/poll하고 Claude 판정과 채택·기각·보류를 다음 라운드에 기록한다. 현재 상태는
상호 충분이 아니며 완료로 판정하지 않는다.

## 라운드 3 · Claude 1차 독립 재검증과 결정

사용자가 Claude 입력창을 비운 뒤 요청 `452368ef1db44cc7be716ca1e398baf9`를 다시
알렸고 응답을 받았다. Claude는 원장을 먼저 읽었으므로 이 평가는 blind 독립 검토가
아니라 **독립 재검증**으로 분류한다. 다만 현재 작업 트리를 직접 다시 렌더해 Chapter 1
19장, Chapter 2 22장, Chapter 3 32장과 리포트 화면을
`tmp/browser-shots/claude-r1/`에서 검사하고 전체 자동 검증도 재실행했다.

### Claude 판정

| 품질 게이트 | 판정 | 핵심 근거 |
| --- | --- | --- |
| 원본 구조 충실성 | 보완 필요 | Ch2 Listing 2.1 덱 축약, Ch3 코드 발췌·명칭 변형 |
| 의미와 주장 충실성 | 중대 결함 | Ch1 그림 1.5의 보완 화살표가 강점→약점이 아니라 같은 행끼리 연결 |
| 독립 문서 완결성 | 보완 필요 | Ch2 Wu et al. 11개 반사실 과제 근거와 일부 원 출처 귀속 누락 |
| 학습성과 설명성 | 보완 필요 | Ch3 발췌 코드의 변수 바인딩 누락, Ch2 농부 예제의 실패 과정 과도한 압축 |
| 발표·시각 품질 | 보완 필요 | bare `section-summary` 문장 연결, SVG 내부 중복 설명, 그림 2.9 비대칭 |
| 추적성과 출판 무결성 | 보완 필요 | 캡처 묶음이 단일 실패에 중단되고 제시된 증거 경로의 신선도가 불명확 |

### 지적별 결정

| ID | 결정 | 근거와 조치 계층 |
| --- | --- | --- |
| A1 렌더 신선도 | 조건부 채택 | Codex의 최신 `presentation-quality-round1` 렌더는 있었으나 peer 요청이 낡은 경로를 지목했다. 절차·스킬에 관련 변경 이후 신선도 증명을 추가한다. |
| A2 캡처 중단·재개 | 채택 | 도구에 지수형 재시도, 유효 출력 건너뛰기, 실패 수집·최종 요약을 추가하고 회귀 테스트를 보강한다. |
| B1 Ch2 Listing 2.1 | 채택 | 덱 프롬프트를 리포트·원문과 정확히 일치시키고 동등성 회귀 검사를 추가한다. |
| B2 Ch1 그림 1.5 화살표 | 채택·중대 | 두 기술의 강점이 상대 약점을 보완하는 실제 경계 간 연결로 다시 그린다. |
| B3 Ch1 transfer learning fan-out | 채택 | pretrained model에서 세 downstream task 모두로 shaft가 보이는 연결을 만든다. |
| B4 Ch1 그림 1.3 캡션 | 채택 | SVG의 여섯 구성요소와 캡션·읽는 법을 맞추고, 세 가지 규모 논거는 본문에 별도로 둔다. |
| B5·B6 근거·귀속 | 채택 | Wu et al. 11개 과제와 Stokman–de Vries, Ch1의 AI 3차 물결·모델 예·Zhang 귀속을 인접 본문에 복원한다. |
| B7·D2 SVG 안 설명 | 채택 | 세 장의 사용 중인 모든 형제 SVG를 감사해 제목·부제·footer·side summary를 캡션/본문으로 옮기고 viewBox를 실제 다이어그램에 맞춘다. |
| B8 Ch3 HPO/OMIM 명칭 | 채택 | 원자료와 live output에 표시된 정확한 문자열로 리포트와 덱을 맞춘다. |
| C1·C2 Ch3 코드 발췌 | 채택 | 변수 바인딩을 복원하고, 원문을 바꾼 실행 보정은 인접 문구로 명시한다. 재발 규칙을 스킬·절차에 추가한다. |
| C3 Ch2 추론 사례 | 채택 | 첫 왕복 뒤 익숙한 늑대–양–양배추 절차를 반복하는 실패 사슬을 3~4단계로 복원한다. |
| C4 `온톨지` | 채택 | `온톨로지`로 교정한다. |
| D1 section summary | 채택 | bare span도 줄·bullet로 읽히도록 템플릿과 세 회차 CSS를 고치고 실제 화면을 확인한다. |
| D3 그림 2.9 정렬 | 채택 | 같은 수준의 좌우 상자를 같은 top·height·centerline grid에 맞춘다. |
| D4 넓은 여백 | 기각 | 잘림·정보 계층 손실의 증거가 없는 취향 제안이다. SVG 정리 후 실제 렌더에서 다시 판단한다. |
| E1 미참조 SVG 9개 | 보류 | 공개 문서에서 참조되지 않아 학습자 영향이 없고, 스킬은 unregistered sibling 삭제 권한을 추론하지 못하게 한다. 사용자 요청 없이 삭제하지 않는다. |

### 구현 진행

- 캡처 드라이버와 테스트: 재시도·backoff·`--skip-existing`·실패 집계에 더해 PNG
  서명·요청 치수·최소 실내용량 검증을 구현했다. 종료 코드 0이지만 7,766바이트 빈 PNG인
  긴 리포트 fragment를 실제로 거부했으며 관련 6개 단위 테스트가 통과했다.
- 스킬·절차: SVG 본체/설명 분리, 코드 변수 바인딩과 실행 보정 표시, 렌더 신선도,
  빈 렌더 판별, blind 검토와 독립 재검증 구분을 추가
- Chapter 1·2·3 산출물: B1–B8, C1–C4, D1–D3의 채택 사항을 각각 리포트 우선으로
  수정하고 덱·사용 중인 전체 형제 SVG·회차 CSS에 반영했다. 미참조 SVG는 보류 결정대로
  삭제하지 않았다.

### 새 렌더의 시각 재검증

- `tmp/browser-shots/presentation-quality-round3/`에 Chapter 1 19장, Chapter 2 22장,
  Chapter 3 32장의 1600×900 렌더를 새로 만들고 contact sheet와 핵심 원본을 실제로
  확인했다. 이전 Ch3 매니페스트가 29장까지만 포함한 사실을 발견해 30–32장도 추가했다.
- 변경 덱의 1366×768 렌더와 390×844 모바일 렌더, 세 리포트의 데스크톱·모바일
  fragment를 확인했다. 긴 리포트 fragment는 단순 screenshot 모드의 빈 화면을
  Puppeteer 제어 캡처로 대체한 뒤 매니페스트 검증기에서 81개 모두 유효 산출물로
  재검증했다.
- A4 PDF는 Chapter 1 14쪽, Chapter 2 16쪽, Chapter 3 24쪽이며 모두
  594.96×841.92pt로 다시 생성했다. 72dpi 전 페이지 contact sheet와 Ch3 Listing 3.17,
  3.22, 3.23, 3.26 원본 페이지에서 잘림·빈 페이지·코드 바인딩·실행 보정 표시를
  확인했다.

### 자동 검증

- `uv run --with 'nbformat>=5,<6' python -m unittest discover -s agent-support/tests -v`:
  212개 통과, 선택 패키지·미구축 환경에 따른 6개 건너뜀
- `python3 agent-support/scripts/build_site.py`와 `--check`: 생성물 최신 상태
- `python3 agent-support/scripts/validate-site.py --site html`: 40개 HTML 통과, 기존 외부
  YouTube iframe 확인 경고 2개만 유지
- `git diff --check`: 통과
- skill-creator `quick_validate.py .agents/skills/study-presentation`: 통과

Codex는 현재 구현과 새 렌더를 기준으로 여섯 게이트를 모두 충분으로 재판정한다. 다만
상호 충분은 Claude의 수정 후 재평가가 끝나기 전까지 선언하지 않고 라운드 4로 간다.

## 라운드 4 · Claude 수정 후 재검증과 게이트 보강

Claude 요청 `c39a91caa7e14e5a9dd954d399578693`은 현재 작업 트리와 렌더를 먼저
독립 재검증한 뒤 이 원장과 대조했다. 판정은 중대 2건, 보완 2건, 이전 보류 1건이었다.

### Claude 판정과 결정

| ID | 등급 | 결정과 조치 |
| --- | --- | --- |
| B3-R `transfer-learning.svg` 검은 쐐기 | 중대 | 채택. `marker-end`가 있는 꺾은선의 암묵적 SVG 기본 fill이 원인이었다. `.line`에 `fill:none`을 넣고 모든 source-fidelity SVG를 자동 검사한다. |
| A4 Ch1·2 A4 절 제목 쪽나눔 | 중대 | 채택. 회차 CSS에 인쇄 절 `break-before`와 제목 `break-inside/page-break-inside` 계약을 동기화했다. |
| CSS 스냅샷 드리프트 | 보완 | 채택. 세 회차와 템플릿의 한글 폰트 스택·표지 줄바꿈·인쇄 절 시작·제목 무결성을 맞추고 자동 검사한다. 회차 고유 러닝 헤더와 코드 라벨은 유지했다. |
| Ch3 계층 추론 도형이 덱에만 존재 | 보완 | 채택. `hierarchical-inference.svg`를 §3.5 리포트 그림 12로 먼저 등록하고 덱이 같은 자산과 안정 ID를 참조하게 했다. 덱 전용 자산은 명시적 adaptation 표지와 리포트 링크 없이는 실패한다. |
| E1 미참조 SVG 9개 | 추적성 보류 해소 | 삭제 권한은 추론하지 않았다. Ch1 4개·Ch2 5개를 각 `presentation.toml`의 `[[retained_unreferenced_assets]]`에 보존 이유와 함께 등록했다. 설명 없는 미참조 SVG, 사라진 파일, 다시 사용 중인 자산의 낡은 보존 기록은 검증 실패로 만든다. |

### 스킬·절차·검증기 보강

- `study-presentation`은 report-first 시각자료, 의도적 덱 adaptation 표지, 공용 CSS
  계약, marker-ended path의 `fill:none`, A4 제목 쪽나눔 검사를 명시한다.
- 공개 미참조 SVG는 사용자 승인 없이 삭제하지 않되, 메타데이터에 경로·보존 이유를
  남겨 설명 가능한 상태로 만든다. 보존 기록은 삭제 승인이 아니다.
- `validate-site.py`는 덱 시각자료 출처, marker-ended SVG fill, source-fidelity CSS
  핵심 계약, 미참조 SVG 보존 원장을 검사한다. 관련 회귀 테스트를 추가했다.

### 최종 크기 렌더 재검증

- 세 덱 전체 1600×900: Chapter 1 19장, Chapter 2 22장, Chapter 3 32장을 새로
  렌더하고 전 회차 contact sheet를 실제 픽셀로 검사했다.
- `transfer-learning.svg`가 쓰인 Ch1 5번, Ch2 그림 2.9, Ch3 계층 추론·검증 게이트를
  1366×768 또는 390×844에서 추가 검사했다. 검은 쐐기, 상자 불균형, 화살촉 이탈,
  텍스트 잘림은 없었다.
- 세 리포트의 데스크톱·390px 모바일 상단을 새로 렌더했다. Ch3 계층 추론은 덱
  1600×900과 A4 20쪽에서 같은 의미·방향·라벨을 유지했다.
- A4 PDF는 Chapter 1 19쪽, Chapter 2 21쪽, Chapter 3 24쪽이며 모두
  594.96×841.92pt다. 전 페이지 contact sheet에서 절 제목 고립·분할, 잘림,
  빈 페이지를 검사했고 이전 Ch1·2 제목 분할은 재현되지 않았다.

### 자동 검증

- 교재 저장소를 함께 연결한 전체 단위 테스트: 220개 통과, 선택 패키지·미구축 환경
  6개 건너뜀
- `build_site.py`, `build_site.py --check`, `validate-site.py --site html
  --check-materials`, `git diff --check`: 통과. 기존 외부 YouTube iframe 수동 확인
  경고 2개만 유지
- 세 회차 전체 SVG `xmllint`, skill-creator `quick_validate.py`: 통과

### Codex 판정

| 품질 게이트 | 판정 | 근거 |
| --- | --- | --- |
| 원본 구조 충실성 | 충분 | Ch1–3 원자료 좌표·제목·필수 그림 대조와 report-first 도형 계약 통과 |
| 의미와 주장 충실성 | 충분 | 이전 B2·B8과 이번 계층 추론 의미·방향·귀속을 렌더와 본문에서 재확인 |
| 독립 문서 완결성 | 충분 | Ch3 계층 추론을 리포트 본문에 통합하고 덱 전용 설명 공백 제거 |
| 학습성과 설명성 | 충분 | 그림 읽는 법·경계, 코드 바인딩, 장별 확인 질문이 유지됨 |
| 발표·시각 품질 | 충분 | 전체 덱, 핵심 1366/mobile, 리포트 desktop/mobile, 전 A4 페이지 실제 픽셀 통과 |
| 추적성과 출판 무결성 | 충분 | 자동 게이트 220개와 미참조 자산 보존 원장, 링크·사이트 검증 통과 |

Codex는 여섯 게이트를 모두 충분으로 판정했다. 당시에는 상호 충분 종료 여부를
라운드 5의 Claude 최종 재검증으로 결정할 예정이었다.

## 라운드 5 · 사용자 종료와 Codex 최종 자체 감사

- 2026-08-04 KST에 사용자가 Claude review를 하지 말고 현재 상태에서 Codex 자체
  검토로 마무리하라고 지시했다.
- 기존 Claude 요청 `9e9f92e325cc4b4f8a6c6a41b28c7eec`는 사용자 지시로 종료된
  대기 요청으로 처리한다. 이후 본문 전송, nudge, poll을 하지 않는다.
- Claude 판정은 미수행·사용자 면제로 기록하며, `MUTUAL SUFFICIENT / PASS`를
  선언하지 않는다.

### 최종 자체 감사와 절차 개선

- 최신 1600×900 전체 덱 contact sheet, 핵심 1366×768·390×844 렌더,
  세 리포트의 데스크톱·모바일·A4 contact sheet와 핵심 원본 크기 화면을
  다시 점검했다. 검은 쏐기, 화살촉 이탈, 반복 상자 불균형, 텍스트 잘림,
  A4 절 제목 분할은 남아 있지 않았다.
- 시각 산출물의 생성 시각이 마지막 관련 HTML·CSS·JavaScript·SVG 변경 이후임을
  확인했다. `presentation.toml` 후속 변경은 보존 자산 메타데이터로,
  렌더 픽셀을 바꾸지 않는다.
- `render-shot-manifest.py`는 이미 제한 재시도·실패 수집·최종 요약을
  구현했지만 제작 절차에는 여전히 첫 실패 중단으로 적혀 있었다.
  절차와 스킬을 실제 동작에 맞게 고쳐 재개 신선도 조건도 명시했다.
- 라운드 3의 Puppeteer 캡처는 역사적 작업 기록으로만 남긴다. 현재 안전
  규칙에서는 owner-only safe runner를 raw Chrome·Puppeteer로 우회한 화면을 최종
  증거로 사용하지 않는다. 이번 최종 판정은 safe runner로 생성된 전체 화면,
  A4와 contact sheet가 실제로 보여 주는 범위에 한정했다.
- 사용자가 peer review를 종료한 경우의 대기 요청 처리, Codex-only 판정,
  peer 기준 면제를 스킬과 품질 루프 절차에 추가했다.

새로운 중대·보완 결함은 발견되지 않았다.

### 최종 자동 검증

- 교재 저장소를 함께 연결한 전체 단위 테스트: 220개 통과, 선택 패키지·미구축
  환경 6개 건너뜀
- `build_site.py`, `build_site.py --check`: 통과
- `validate-site.py --site html --check-materials`: HTML 40개 통과, 기존 외부
  YouTube iframe 수동 확인 경고 2개만 유지
- 세 회차 전체 SVG `xmllint`, `git diff --check`: 통과
- safe browser runner 설치본 `--verify`와 runner `--check`: 통과
- skill-creator `quick_validate.py .agents/skills/study-presentation`: 통과

현재 종료 판정은 `Codex 자체 여섯 게이트 충분 / Claude 기준 사용자
면제`이며, 상호 충분 판정은 아니다.
