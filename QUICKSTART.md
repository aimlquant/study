# AIML Quant 참여자 빠른 시작

## 1. 내 일정 확인

발표 날짜·챕터·발표자는 공개 사이트의 스터디별 `전체 일정` 또는
[`agent-support/sessions.toml`](agent-support/sessions.toml)에서 확인한다.

- [AI/ML 전체 일정](https://restful3.github.io/aimlquant/studies/knowledge-graphs-and-llms-in-action/)
- [Quant 전체 일정](https://restful3.github.io/aimlquant/studies/machine-trading/)

`발표자 미정`인 회차는 담당자가 정해진 뒤 레지스트리를 먼저 갱신한다.

## 2. 교재와 발표자료 준비

현재 교재는 `materials/<track>/active/<study-slug>/` 아래에 있다. 실행 환경과 노트북은
[`study-materials` 절차](agent-support/procedures/study-materials.md)를 따르고, 회차 리포트와
슬라이드는 [`study-presentation` 절차](agent-support/procedures/study-presentation.md)를 따른다.
새 회차는 가능하면 상세 리포트를 먼저 완성·검토하고 그 내용을 발표자료로 압축한다.

## 3. 공개 회차 등록

1. 일정은 `scheduled`로 먼저 등록한다.
2. `html/studies/<study-slug>/presentations/<session-slug>/`에 공개 자료를 둔다.
3. `artifacts`를 등록하고 `materials-published`로 바꾼다.
4. YouTube 영상이 실제 `public`이 된 뒤에만 ID를 기록하고 `video-public`으로 바꾼다.

비공개·일부공개 video ID, OAuth 정보, 쿠키, 녹화 원본과 업로드 원장은 이 공개 저장소에
넣지 않는다. 자세한 내용은 [`study-lifecycle.md`](agent-support/procedures/study-lifecycle.md)를 본다.

## 4. 로컬 확인

```bash
uv run --with 'nbformat>=5,<6' python -m unittest discover -s agent-support/tests -v
python3 agent-support/scripts/build_site.py
python3 agent-support/scripts/build_site.py --check
python3 agent-support/scripts/validate-site.py --site html --check-materials
python3 -m http.server 8000 -d html
```

브라우저에서 <http://localhost:8000/>을 열고 데스크톱·모바일 크기에서 일정, 발표자,
자료 링크와 텍스트 줄바꿈을 확인한다. 커밋·push·Pages 변경은 요청받은 범위에서만 수행한다.
