# examples/example5/main.py

import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command, interrupt

load_dotenv()

# State 정의
class State(TypedDict):
    messages: Annotated[list, add_messages]
    name: str
    birthday: str

# 사람의 검증을 받는 도구
@tool
def human_assistance(
    name: str,
    birthday: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """사람에게 정보 검증을 요청합니다."""
    human_response = interrupt({
        "question": "이 정보가 맞나요?",
        "name": name,
        "birthday": birthday,
    })

    if human_response.get("correct", "").lower().startswith("y"):
        verified_name = name
        verified_birthday = birthday
        response = "확인 완료"
    else:
        verified_name = human_response.get("name", name)
        verified_birthday = human_response.get("birthday", birthday)
        response = f"수정됨: {human_response}"

    state_update = {
        "name": verified_name,
        "birthday": verified_birthday,
        "messages": [ToolMessage(content=response, tool_call_id=tool_call_id)],
    }
    return Command(update=state_update)

def setup_graph():
    # 그래프 설정
    memory = MemorySaver()
    graph_builder = StateGraph(State)

    # 도구 설정
    search_tool = TavilySearchResults(max_results=2)
    tools = [search_tool, human_assistance]

    # AI 모델 설정
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7,
    )
    llm_with_tools = llm.bind_tools(tools)

    # 챗봇 노드
    def chatbot(state: State):
        message = llm_with_tools.invoke(state["messages"])
        assert len(message.tool_calls) <= 1
        return {"messages": [message]}

    # 그래프 구성
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", ToolNode(tools=tools))
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")

    return graph_builder.compile(checkpointer=memory)

def test_information_lookup():
    graph = setup_graph()
    config = {"configurable": {"thread_id": "lookup_test"}}

    # 정보 검색 요청
    print("\n=== 정보 검색 테스트 시작 ===")
    user_input = (
        "LangGraph의 출시일을 찾아주세요. "
        "찾으면 human_assistance 도구로 검증해주세요."
    )

    try:
        # 초기 검색 실행
        events = graph.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
            stream_mode="values"
        )

        print("\n검색 중...")
        for event in events:
            if "messages" in event:
                message = event["messages"][-1]
                if hasattr(message, "content"):
                    print(f"\n🤖 AI: {message.content}")

        # 검증 정보 제공
        print("\n사람의 검증 진행 중...")
        human_command = Command(
            resume={
                "name": "LangGraph",
                "birthday": "Jan 17, 2024",
            }
        )

        # 검증 정보로 계속 진행
        events = graph.stream(human_command, config, stream_mode="values")
        for event in events:
            if "messages" in event:
                message = event["messages"][-1]
                if hasattr(message, "content"):
                    print(f"\n🤖 AI: {message.content}")

        # 최종 상태 확인
        state = graph.get_state(config)
        if "name" in state.values and "birthday" in state.values:
            print("\n=== 최종 저장된 정보 ===")
            print(f"이름: {state.values['name']}")
            print(f"출시일: {state.values['birthday']}")

        # 상태 수동 업데이트 테스트
        print("\n=== 상태 수동 업데이트 테스트 ===")
        graph.update_state(config, {"name": "LangGraph (수동 업데이트 실행)"})
        new_state = graph.get_state(config)
        print(f"수정된 이름: {new_state.values['name']}")
        print(f"출시일: {new_state.values['birthday']}")

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")

def main():
    print("🔄 정보 검색 및 검증 시스템 시작...")
    test_information_lookup()
    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    main()