# KG·LLM 15장 발표 준비 계획 (10/31, 도라 12259, task b89f5d14d25c)

목표: 10/31(토) 09:00–10:00 KG·LLM 15장 "LangGraph로 QA 에이전트 구축"(발표 태영=도라)에 쓸 상세 리포트와 발표자료를 기존 회차와 같은 템플릿으로 준비하고, 도라 검토 뒤 공개한다. 장소·시간·녹화 작업은 끝났고 여기서 다루지 않는다.

## 현황 (10/24 12:4x 읽기 전용)

| 항목 | 상태 |
|---|---|
| 일정 정본 | README·sessions.toml `2026-10-31-kg-llm-ch15`, 태영, 09:00–10:00, status scheduled |
| 교재 원자료 | `study-materials/.../chapter_15_building_a_qa_agent_with_langgraph/` 원문 md·pdf, 한국어 번역(84KB), 쉬운 해설판(101KB, 15.1 LangGraph 파이프라인 / 15.2 Streamlit 앱 / 15.3 전문가 모방 수사 / 15.4 향후 방향 / 핵심 용어), 그림 19장, `src/`, `notebooklm/` |
| 참고 해설 영상 | `uVnn9ikCDpA` 공개, 회차 페이지에 이미 걸림 |
| 회차 리포트·덱 | **없음** (`presentations/2026-10-31-ch15/` 미생성) |
| 앞 회차 기준 | ch14(10/24, 종훈(L)): `study-report-v1`+`study-deck-v1`, `raw-report-deck-v1`, source_fidelity·report_quality·deck_quality 검사, 내용 검토 JSON |

## 재사용

- 쉬운 해설판을 `source_material` 로 쓴다(ch14와 같은 방식). 해설판을 새로 쓰지 않는다.
- 참고 해설 영상은 그대로 둔다.
- 템플릿·검사기는 기존 `new-presentation.py`·`validate-site.py` 를 쓴다. 새 디자인 없음.

## 만들 것 (최소)

`agent-support/procedures/study-presentation.md` 절차 그대로.

1. `presentations/2026-10-31-ch15/` 생성(presentation.toml, report.html, index.html, assets). `--print-source-outline` 으로 원본 절·그림·Listing 좌표 기준선을 뽑는다.
2. 상세 리포트: 원본 절 순서·그림/Listing 번호 보존, 자체 해설. 코드는 핵심 Listing만 발췌·설명(전체 복사 금지, 교재 공개 저장소 복사 금지 원칙).
3. 발표자료: 50분 발표+10분 Q&A 기준, 의미 있는 그림 하나에 슬라이드 하나. 교재 그림은 복제하지 않고 필요한 것만 자체 도해(SVG)로.
4. 내용 검토 JSON(`2026-10-31-kg-llm-ch15-content.json`).
5. 확인: `build_site.py --check`, `validate-site.py`(교재 연결), owner 렌더 러너로 리포트·덱 1280/390 실물 확인, 짝 C3.

## 일정 (10/26 월 09–18 정전 반영)

| 날짜 | 할 일 |
|---|---|
| 10/24(토) | 이 계획 C1 |
| 10/25(일) | 원자료 감사·리포트 초안, 짝 중간 검토 |
| 10/26(월) 09–18 | 정전: 도라 작업 불가. h1도 꺼질 수 있으므로 이 시간대에 h1 작업·검토 요청을 잡지 않는다 |
| 10/27(화) | 발표자료 초안, C3 |
| 10/28(수)–10/29(목) | 도라 검토·수정 |
| 10/30(금) | 도라 OK 뒤 공개(push·Pages) 및 실제 페이지 확인 |

## 관문

- 공개(public 저장소 push)는 도라가 리포트·덱을 본 뒤에만 한다. 그 전에는 로컬 브랜치/작업트리에서만 만든다.
- 외부 발송 없음. 장소·녹화 수정 0.

## 도라에게 물을 것 (판단에 필수인 것만)

1. 리포트·덱 초안을 에이전트가 만들고 도라가 검토하는 방식이 맞는지(지난 태영 발표 ch03·ch01은 도라 본인 커밋).
2. 도라 검토 가능한 날(10/28–10/29 가정이 맞는지).
