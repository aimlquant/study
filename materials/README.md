# Materials

진행 교재와 종료 교재를 분야와 상태로 나눈다.

```text
materials/
├── aiml/
│   ├── active/      # 현재 AI/ML 교재
│   └── archive/     # 종료된 AI/ML 교재
└── quant/
    ├── active/      # 현재 퀀트 교재
    └── archive/     # 종료된 퀀트 교재
```

교재 폴더 이름은 소문자 ASCII slug를 사용한다. 종료 시 같은 분야 안에서
`active/<study-slug>`를 `archive/<study-slug>`로 이동하고
`agent-support/studies.toml`의 `status`와 `materials_path`를 함께 갱신한다.

발표자료는 교재 수명주기와 분리해 `html/studies/<study-slug>`에 계속 보존한다.
