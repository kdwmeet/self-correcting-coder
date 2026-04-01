# Self-Correcting Coding Agent (자율 수정 코딩 에이전트)

## 1. 프로젝트 개요

이 프로젝트는 LangGraph의 순환 구조(Cyclic Graph)를 활용하여 AI가 스스로 파이썬 코드를 작성하고, 실행하며, 오류를 수정하는 자율 에이전트입니다.

단순히 코드를 생성하는 것에 그치지 않고 가상의 실행 환경(Python REPL)에서 코드를 직접 구동합니다. 실행 중 오류(Traceback)가 발생하면 에이전트가 에러 로그를 분석하여 코드를 수정하고 재실행하는 자기 반성(Self-Reflection) 과정을 거쳐 최종적으로 완벽하게 동작하는 코드를 도출해 냅니다.

## 2. 시스템 아키텍처



본 시스템은 실행 결과에 따라 코더 노드로 되돌아가는 순환 루프 워크플로우를 가집니다.

1. State Definition: 사용자의 목표, 작성된 코드, 실행 결과(stdout), 에러 로그(Traceback), 현재 시도 횟수를 전역 상태로 관리합니다.
2. Coder Node: 사용자의 초기 목표 또는 이전 실행의 에러 로그를 바탕으로 실행 가능한 순수 파이썬 코드를 작성합니다.
3. Executor Node: 작성된 코드를 langchain-experimental의 PythonREPL 도구를 사용하여 로컬 환경에서 실행하고 표준 출력 및 에러 메시지를 캡처합니다.
4. Conditional Routing: 실행 결과에 에러가 없거나, 최대 시도 횟수(3회)에 도달하면 파이프라인을 종료(END)하고, 에러가 발생했다면 다시 Coder Node로 라우팅하여 코드를 수정하도록 지시합니다.

## 3. 기술 스택

* Language: Python 3.10+
* Package Manager: uv
* LLM: OpenAI gpt-5-mini (코드 작성, 에러 로그 분석 및 자율 수정)
* Data Validation: Pydantic (v2)
* Execution Environment: langchain-experimental (PythonREPL)
* Orchestration: LangGraph (순환 라우팅), LangChain
* Web Framework: Streamlit

## 4. 프로젝트 구조

self-correcting-coder/
├── .env                  
├── requirements.txt      
├── main.py               
└── app/
    ├── __init__.py
    └── graph.py          

## 5. 설치 및 실행 가이드

### 5.1. 환경 변수 설정
프로젝트 루트 경로에 .env 파일을 생성하고 API 키를 입력하십시오.

OPENAI_API_KEY=sk-your-api-key-here

### 5.2. 의존성 설치 및 앱 실행
독립된 가상환경을 구성하고 애플리케이션을 구동합니다.

uv venv
uv pip install -r requirements.txt
uv run streamlit run main.py

## 6. 테스트 시나리오 및 검증 방법

* 정상 실행 검증: "1부터 100까지 짝수만 더하는 코드를 작성하십시오"와 같은 명확한 목표를 입력하여 에러 없이 한 번에 성공하는지 확인합니다.
* 자율 수정(Self-Correction) 검증: 고의로 에러가 발생할 만한 복잡한 연산이나 올바르지 않은 패키지 사용을 유도합니다. 실행 후 에러가 발생했을 때 에이전트가 우측 패널에서 에러 메시지를 인지하고 코드를 스스로 수정하여 루프를 도는지 확인합니다.
* 무한 루프 방지: 에이전트가 해결할 수 없는 과제(예: 외부 API 키가 필요한 차단된 요청)를 주었을 때, 최대 시도 횟수(3회)에 도달하면 반복을 중단하고 최종 에러 상태를 반환하는지 점검합니다.

## 7. 실행 화면