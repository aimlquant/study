# Session Handoff: Chapter 2. The Financial Data Universe (2026-09-19)

본 문서는 Stefan Jansen의 _Machine Learning for Trading (3rd Edition)_ (2026) Chapter 2 "The Financial Data Universe" 발표 세션(발표일: 2026-09-19, 발표자: 핀조이)에 대한 세션별 독립 핸드오프 리포트입니다.

## 1. 세션 기본 정보
- **스터디 ID**: `machine-learning-for-trading-3e-2026`
- **세션 ID**: `2026-09-19-ml4t-ch02`
- **세션 슬러그 / 배포 경로**: `html/studies/machine-learning-for-trading-3e/presentations/2026-09-19-ch02/`
- **발표 범위**: Chapter 2. 금융 데이터 세계 (The Financial Data Universe) — §2.1 ~ §2.5 전 범위
- **발표자**: 핀조이 (pinjoy99@gmail.com)
- **발표일**: 2026-09-19

## 2. 파일 목록 (Asset Manifest)
본 세션 디렉토리는 다음 파일들로 구성되어 독립 배포됩니다:
- `report.html`: 상세 분석 리포트 (KaTeX 오프라인 로컬 수식 렌더링, 12개 실습 박스기사 `실습 1` ~ `실습 12`, 반응형 좌측 목차 사이드바, 인쇄/PDF 최적화 스타일 내장)
- `index.html`: 발표용 16:9 슬라이드 (총 46개 슬라이드, `study-deck-v1` 1280x720 고정 스케일 스테이지, 네비게이션 및 목차 드로어, 실습 전용 골드 뱃지/카드, 텍스트/표 오버플로우 및 겹침 방지 최적화)
- `presentation.toml`: 세션 메타데이터 (workflow: raw-report-deck-v1, artifacts: report, slides)
- `HANDOFF.md`: 세션 핸드오프 리포트 (본 파일)
- `assets/`: 회차별 전용 스타일시트(`report.css`, `deck.css`), 스크립트(`report.js`, `deck.js`, `deck-lightbox.js`) 및 오프라인 KaTeX 자산(`katex/`)

## 3. 핵심 내용 및 12개 주피터 실습 연계 감사
본 발표 및 리포트는 교재 2장의 2.1~2.5 전 절에 대한 깊이 있는 이론 전개와 함께, 공식 코드베이스의 22개 주피터 노트북 핵심 실습 결과와 수치를 총 12개의 상세 실습 단위로 완벽하게 통합했습니다:

- **§2.1 금융 데이터 분류 체계 & 4대 데이터 계약**:
  - 시장 데이터(틱, 오더북, 체결, OHLCV), 펀더멘털 데이터(발표 지연 및 빈티지 개정), 대체 데이터(위성, 카드, 온체인, 예측시장)의 특성 대조.
  - 모델링 전 반드시 확정해야 할 4대 데이터 계약(타임스탬프 의미론, 기업행위 조정 방법론, 식별자 안정성, 수정/재작성 처리) 확립.
  - **`실습 1` (`01_us_equities_eda`)**: Quandl WIKI 3,199개 미국 주식 패널 분석을 통해 777개(24.3%) 상장폐지 종목이 2014년 이후에만 집중되어 1962~2013년 구간에 생존자 편향이 내포되어 있음을 발견.
- **§2.2 자산군별 시장 데이터 환경 (표 2.1)**:
  - 주식, ETP, 선물, 옵션, 크립토, 외환, 채권, 스왑, 원자재 등 9개 자산군의 시장 구조와 실패 모드 분석.
  - **`실습 2` (`02_corporate_actions`)**: Apple(AAPL) 1980~2018 4회 분할 및 54회 배당 역방향 조정 공식 검증. 미조정 가격($5.9\times$) 대비 올바른 조정 가격($398.2\times$)으로 **68배의 누적 성과 왜곡** 실증 및 Quandl 기준치 대비 0.05% 오차 내 100% 일치 검증.
  - **`실습 3` (`03_etfs_eda`)**: 100개 ETF(2006~2025) 패널에서 SPY와 원자재 ETF 간 23배 유동성 격차 및 가격 4개 필드 독립 조정에 따른 473건(0.1%) OHLC 불변식 위반 진단.
  - **`실습 4` (`04`~`06_futures_continuous`)**: 30개 CME 선물의 23시간 세션 집계 및 거래량 역전일 기반 자동 롤 탐지 파이프라인 구축. 선물 시계열의 담보 이자(Collateral Return) 분리 분석.
  - **`실습 5` (`07`~`09_options_continuous`)**: Black-Scholes 제1원리 기반 Greeks(Delta, Gamma, Vega, Theta, Rho) 산출 및 고정만기(30일물) 옵션의 롤오버 오염 제거 기법 실증.
  - **`실습 6` (`10_crypto_perps_eda` & `11`)**: Binance 19개 코인 무기한 선물의 8시간 펀딩 비율(Funding Rate) 분석을 통해 극단 펀딩비의 횡단면 반전 예측력 및 델타 뉴트럴 차익거래 성과 입증.
- **§2.3 데이터 소싱 실사 프레임워크 & 4대 치명적 실패 모드**:
  - 5차원 품질 프레임워크(적시성, 완전성, 정확성, 일관성, 유효성), 벤더 실사 3대 축, 내부 거버넌스 5대 기둥.
  - **`실습 7` (`13_data_quality_framework`)**: `OHLCVValidator` 및 두꺼운 꼬리에 강건한 MAD/IQR 기반 수익률 이상치 탐지와 `AnomalyManager`의 감사 격리 로그 생성.
  - **`실습 8` (`14_point_in_time_validation`)**: 중심 이동평균의 미래정보 누출 시각화 및 FRED API `vintage_date`를 활용한 GDP 속보치/확정치 이중시간(Bitemporal) 쿼리 구현.
  - **`실습 9` (`15_survivorship_bias_detection`)**: CRSP 상장폐지 3대 시나리오 몬테카를로 1,000회 시뮬레이션을 통해 생존자 전용 포트폴리오의 **+8.0%p ~ +15.3%p 성과 과대평가** 계량화.
  - **`실습 10` (`16`~`19_incremental_updates`)**: 영구 식별자(FIGI/CIK) 크로스워크 매핑 및 Hive 파티셔닝(`year=YYYY/month=MM/`) 기반 안전한 일일 증분 수집 파이프라인 구축.
- **§2.4 데이터 저장 아키텍처 & 벤치마크**:
  - 파일 형식 벤치마크 (표 2.4), 임베디드 분석 스택(DuckDB, Polars, SQLite), 시계열 DB 벤치마크, 스토리지 의사결정 매트릭스 (표 2.5).
  - **`실습 11` (`20` & `22_pandas_polars_benchmark`)**: Parquet Row Group 메타데이터 기반 조건자 푸시다운(Predicate Pushdown) 및 1,000만 행 대규모 집계에서 Polars의 Pandas 대비 5~15배 속도 향상 실측.
  - **`실습 12` (`21_storage_benchmark_database`)**: 시계열 DB 벤치마크 및 비동기 틱 매칭을 위한 ASOF 조인 성능 순위(`Polars > Pandas > DuckDB > QuestDB`) 실증.
- **§2.5 요약 및 핵심 용어 사전**:
  - 4대 실천 원칙(가정 명시화, 가짜 알파 원천 봉쇄, 시장 구조 부합 모델링, 단순/빠른 스토리지) 및 7대 핵심 용어 정의.

## 4. 품질 검증 상태
- **빌드 및 사이트 검증**: `python agent-support/scripts/build_site.py --check` 및 `python agent-support/scripts/validate-site.py --site html` 100% 통과 (100개 HTML 전수 검증 통과).
- **테스트 스위트**: `uv run --with 'nbformat>=5,<6' python -m unittest discover -s agent-support/tests -v` 284개 테스트 전수 통과 (`OK (skipped=6)`).
- **슬라이드 레이아웃 적합성**: 1280x720 고정 스케일 스테이지(`study-deck-v1`) 기반으로 46개 전 슬라이드의 가로/세로 오버플로우 및 텍스트 겹침 0건 확인.
- **스타일 가이드라인 준수**:
  - 오렌지색(Gold) 테두리 및 뱃지는 오직 주피터 실습(`card-lab`, `highlight-lab`)에만 배타적으로 적용.
  - 일반 개념 및 로드맵은 블루/슬레이트 카드(`card`)로 통일.
- **수식 렌더링**: 외부 CDN 없이 오프라인 KaTeX 엔진(`assets/katex/`)으로 모든 수식 기호, 분할 조정 산식, 블랙-숄즈 수식 정상 렌더링.

## 5. 배포 경로
- **슬라이드 라이브 URL**: <https://aimlquant.github.io/study/studies/machine-learning-for-trading-3e/presentations/2026-09-19-ch02/>
- **상세 리포트 라이브 URL**: <https://aimlquant.github.io/study/studies/machine-learning-for-trading-3e/presentations/2026-09-19-ch02/report.html>
- **회차 세션 아카이브 URL**: <https://aimlquant.github.io/study/sessions/2026-09-19-ml4t-ch02/>
- **GitHub 소스 디렉토리**: [html/studies/machine-learning-for-trading-3e/presentations/2026-09-19-ch02/](https://github.com/aimlquant/study/tree/main/html/studies/machine-learning-for-trading-3e/presentations/2026-09-19-ch02)
