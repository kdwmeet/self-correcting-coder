import streamlit as st
from app.graph import app_graph

st.set_page_config(page_title="자율 수정 코딩 에이전트", layout="wide")

st.title("자율 수정 코딩 에이전트 (Self-Correcting Coding Agent)")
st.markdown("에이전트가 코드를 작성하고 직접 실행합니다. 에러가 발생하면 스스로 에러 로그를 분석하여 코드를 수정합니다.")
st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("코딩 목표 입력")
    with st.form(key="coding_form"):
        task_input = st.text_area(
            "구현할 파이썬 프로그램의 목표를 입력하십시오.",
            placeholder="예: 1부터 50까지의 피보나치 수열을 구해서 리스트로 출력하는 코드",
            height=150
        )
        submit_btn = st.form_submit_button("코드 작성 및 실행", use_container_width=True)

with col2:
    st.subheader("실행 현황 및 결과")

    if submit_btn and task_input.strip():
        initial_state = {
            "task": task_input,
            "code": "",
            "execution_result": "",
            "error": "",
            "iteraion": 0
        }

        status_placeholder = st.empty()
        final_state = initial_state.copy()

        with st.spinner("에이전트가 코드를 작성하고 실행 환경을 테스트 중입니다..."):
            for output in app_graph.stream(initial_state):
                for node_name, state_update in output.items():
                    final_state.update(state_update)

                    with status_placeholder.container():
                        if node_name == "coder_node":
                            st.info(f"[시도 횟수: {final_state['iteraion']}] 코드를 작성하고 있습니다...")
                        elif node_name == "executor_node":
                            if state_update.get("error"):
                                st.error("실행 중 에러 발생. 에러 로그를 분석하여 코드를 다시 수정합니다.")
                            else:
                                st.success("코드 실행에 성공했습니다.")
            
        tab1, tab2 = st.tabs(["최종 코드", "실행 결과"])

        with tab1:
            st.code(final_state.get("code", ""), language="python")
        
        with tab2:
            if final_state.get("error") and final_state.get("iteraion") >= 3:
                st.error("최대 시도 횟수를 초과하여 코드를 완성하지 못했습니다. 아래는 최종 에러 로그입니다.")
                st.code(final_state.get("error"), language="text")
            else:
                st.text_area(
                    "표중 출력(stdout)",
                    value=final_state.get("execution_result", "출력값 없음"),
                    height=200,
                    disabled=True
                )
    elif not submit_btn:
        st.info("좌측에 목표를 입력하고 실행 버튼을 누르십시오.")