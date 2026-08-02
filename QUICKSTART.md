# AIML Quant 참여자 빠른 시작

## 0. 저장소 두 개 준비

발표 자료는 공개 저장소에, 교재는 참가자 전용 저장소에 있다. 두 저장소를
나란히 놓고, 공개 저장소 안에 교재를 가리키는 심링크를 건다.

```bash
mkdir -p ~/workspace/aimlquant && cd ~/workspace/aimlquant
git clone https://github.com/aimlquant/study.git
git clone https://github.com/aimlquant/study-materials.git   # 참가자만 접근 가능
cd study && ln -sfn ../study-materials materials
```

```text
aimlquant/
  ├── study/              공개 — 발표자료·사이트·도구
  │     └── materials → ../study-materials   (심링크, 커밋 안 됨)
  └── study-materials/    비공개 — 교재 원문·해설·소스
```

심링크 덕분에 교재 경로가 예전과 같은 `materials/<track>/active/<slug>/` 로
유지되고, 검증도 전부 실행된다. 심링크가 없으면 교재 관련 검사 약 51개가
조용히 건너뛰어진다.

`study-materials` 가 안 받아지면 아직 조직 멤버가 아닌 것이다.
`restful3@gmail.com` 으로 GitHub 계정을 알려주면 초대한다.

## 1. 내 일정 확인

발표 날짜·챕터·발표자는 공개 사이트의 스터디별 `전체 일정` 또는
[`agent-support/sessions.toml`](agent-support/sessions.toml)에서 확인한다.

- [AI/ML 전체 일정](https://aimlquant.github.io/study/studies/knowledge-graphs-and-llms-in-action/)
- [Quant 전체 일정](https://aimlquant.github.io/study/studies/machine-trading/)

`발표자 미정`인 회차는 담당자가 정해진 뒤 레지스트리를 먼저 갱신한다.

## 2. 교재와 발표자료 준비

현재 교재는 `materials/<track>/active/<study-slug>/` 아래에 있다. 실행 환경과 노트북은
[`study-materials` 절차](agent-support/procedures/study-materials.md)를 따르고, 회차 리포트와
슬라이드는 [`study-presentation` 절차](agent-support/procedures/study-presentation.md)를 따른다.
새 회차는 가능하면 상세 리포트를 먼저 완성·검토하고 그 내용을 발표자료로 압축한다.

교재를 고쳤으면 `study-materials` 에서 커밋·push하고, 발표자료를 고쳤으면
`study` 에서 커밋·push한다. 저장소가 다르므로 한 번에 커밋되지 않는다.

발표자료에서 교재 파일을 링크할 때는 GitHub 주소를 직접 쓰지 않는다.
교재 저장소가 비공개라 외부 방문자에게 404가 되기 때문이다. 대신 안내
페이지를 거치게 하면 참가 방법이 함께 안내된다.

```text
../../../../materials/?p=aiml/active/<slug>/<chapter>/<file>.md
```

`validate-site.py` 가 직접 링크를 잡아내므로 잊어도 검증에서 걸린다.

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
