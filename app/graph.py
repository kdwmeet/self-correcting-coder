from typing import TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.utilities import PythonREPL
from langgraph.graph import StateGraph, START, END

load_dotenv()

# Pydantic 스키마 정의
class CodeOutput(BaseModel):
    """작성된 파이썬 코드"""
    code: str = Field(description="실행 가능한 순수 파이썬 코드 (마크다운 코드 블록 기호 제외)")
    
# 상태 정의
class CodeState(TypedDict):
    task: str
    code: str
    excution_result: str
    error: str
    iteration: int

# 도구 및 노드 구현
def coder_node(state: CodeState):
    """목표 또는 이전 에러 로그를 바탕으로 파이썬 코드를 작성합니다."""
    llm = ChatOpenAI(model="gpt-5-mini", reasoning_effort="low")
    structured_llm = llm.with_structured_output(CodeOutput)

    current_iteraion = state.get("iteration", 0)

    # 에러가 발생해서 다시 돌아온 경우 (수정 작업)
    if state.get("error"):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 파이썬 시니어 개발자입니다. 작성한 코드에서 에러가 발생했습니다. 에러 메시지를 분석하여 코드를 수정하십시오. 반드시 실행 가능한 순수 파이썬 코드만 반환해야 합니다."),
            ("user", "목표: {task}\n\n기존 코드:\n{code}\n\n에러 메시지:\n{error}")
        ])
        result = (prompt | structured_llm).invoke({
            "task": state["task"],
            "code": state["code"],
            "error": state["error"]
        })
    # 처음 코드를 작성하는 경우
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 파이썬 시니어 개발자입니다. 주어진 목표를 달성하는 완벽한 파이썬 코드를 작성하십시오. 출력(print)문을 포함하여 결과를 확인할 수 있게 하십시오. 반드시 실행 가능한 순수 파이썬 코드만 반환해야 합니다."),
            ("user", "목표: {task}")
        ])
        result = (prompt | structured_llm).invoke({"task": state["task"]})

    return {"code": result.code, "iteraion": current_iteraion + 1}

def executor_node(state: CodeState):
    """작성된 코드를 Python REPL 환경에서 실행하고 결과를 확인합니다."""
    repl = PythonREPL()
    code_to_run = state["code"]

    try:
        # 코드를 실행하고 표준 출력을 캡처합니다.
        result = repl.run(code_to_run)

        # 실행 결과에 에러 메시지가 포함되어 있는지 검사합니다.
        if "Traceback" in result or "Error:" in result or "Exception:" in result:
            return {"execution_result": "", "error": result}
        else: return {"execution_result": result.strip(), "error": ""}

    except Exception as e:
        # 실행 환경 자체의 예외를 캡처합니다.
        return {"execution_result": "", "error": str(e)}

# 라우팅 로직
def route_evaluaion(state: CodeState):
    """실행 결과를 평가하여 루프를 종료할지 코드를 수정할지 결정합니다."""
    # 에러가 없거나 최대 시도 횟수를 초과하면 종료합니다.
    if not state.get("error") or state.get("iteration", 0) >= 3:
        return END
    return "coder_node"

# 그래프 조립
workflow = StateGraph(CodeState)

workflow.add_node("coder_node", coder_node)
workflow.add_node("executor_node", executor_node)

workflow.add_edge(START, "coder_node")
workflow.add_edge("coder_node", "executor_node")

# 실행 후 검증 결과에 따른 조건부 라우팅
workflow.add_conditional_edges(
    "executor_node",
    route_evaluaion,
    {"coder_node": "coder_node", END: END}
)

app_graph = workflow.compile()