import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages]

def setup_graph():
    # 그래프 설정
    graph_builder = StateGraph(State)

    # AI 모델과 도구 설정
    tool = TavilySearchResults(max_results=2)
    tools = [tool]
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        streaming=True
    )
    llm_with_tools = llm.bind_tools(tools)

    # 챗봇 노드 함수
    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    # 그래프 구성
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", ToolNode(tools=[tool]))
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")

    return graph_builder.compile()

def test_chatbot(graph, question: str):
    """
    챗봇 테스트 함수
    """
    print("\n" + "="*50)
    print(f"😀 사용자: {question}")
    print("="*50)

    try:
        for event in graph.stream({"messages": [("human", question)]}):
            for value in event.values():
                if "messages" in value:
                    message = value["messages"][-1]

                    # AI 응답 출력
                    if hasattr(message, "content"):
                        print("\n🤖 AI:", message.content)

                    # 도구 사용 여부 확인 및 출력
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        print("\n🔍 검색 중...")
                        for tool_call in message.tool_calls:
                            print(f"- 검색어: {tool_call['args'].get('query', '')}")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")

def main():
    # 테스트할 질문들
    test_questions = [
        "안녕하세요!",
        "2024년 가장 인기있는 프로그래밍 언어는 뭐야?",
        "1 + 1은 뭐야?",
        "파이썬이란 무엇인가요?",
        "어제 있었던 월드컵 결과 알려줘",
        "2025년 IT 최신 트렌드를 알려줘"
    ]

    # 그래프 초기화
    print("🔄 챗봇 초기화 중...")
    graph = setup_graph()
    print("✅ 챗봇 준비 완료!\n")

    # 각 질문 테스트
    for question in test_questions:
        test_chatbot(graph, question)
        print("\n" + "-"*50)  # 질문 구분선

if __name__ == "__main__":
    main()