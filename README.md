# LectureMate Lite

강의 PDF를 업로드하여 AI 요약, 키워드 추출, 객관식 퀴즈를 제공하는 팀 프로젝트입니다.

## 실행 방법

Python 3.11 권장

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

> 모델 및 패키지 버전은 1주 차 기술 검증 후 확정합니다. 현재는 UI 뼈대만 실행됩니다.

## 담당
- A: PDF 텍스트 추출, 키워드
- B: AI 요약
- C: 퀴즈 생성
- D: UI, 통합, 팀 운영

## 협업 규칙
- main에 직접 push하지 않고 기능 브랜치에서 PR 생성
- 커밋: feat:, fix:, docs:, test:, refactor:
- PR에 테스트 방법 및 결과 작성
- 모델 가중치, 개인정보 포함 PDF, .env 커밋 금지

## 지원 범위
텍스트 기반 PDF만 지원하며 OCR, 계정, DB, 배포는 MVP에서 제외합니다.

## AI 에이전트 협업
- 작업 시작 전에 [`AGENTS.md`](AGENTS.md)와 [`docs/CONTRACTS.md`](docs/CONTRACTS.md)를 읽으세요.
- 에이전트가 해당 파일을 자동으로 읽지 않는 환경에서는 첫 프롬프트에 두 파일을 읽도록 명시하세요.
- CI는 문법·린트·가벼운 테스트만 확인합니다. 실제 한국어 AI 출력 품질은 각 담당자가 별도로 검증해야 합니다.
