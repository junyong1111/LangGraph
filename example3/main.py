from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list, add_messages]

def setup_graph():
    # 그래프 빌더 생성
    graph_builder = StateGraph(State)

    # 도구 설정
    tool = TavilySearchResults(max_results=2)
    tools = [tool]

    # LLM 설정
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        streaming=True
    )
    llm_with_tools = llm.bind_tools(tools)

    # 챗봇 노드 정의
    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    # 노드 추가
    graph_builder.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools=tools)

    # human-in-the-loop 적용
    def require_human_approval(*args, **kwargs):
        print("\n⚠️ Human Approval Required")
        input("Press Enter to continue...")

    graph_builder.add_node("tools", tool_node, interrupt_before=require_human_approval)
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)

    # 그래프 컴파일
    return graph_builder.compile()

def main():
    graph = setup_graph()
    print("✅ Human-in-the-loop 챗봇 준비 완료!")

    # 사용자 메시지
    messages = [
        "Python에 대해 검색해줘",
        "오늘 날씨를 알려줘"
    ]

    for question in messages:
        print(f"\n😀 사용자: {question}")
        for event in graph.stream({"messages": [("human", question)]}):
            for value in event.values():
                if "messages" in value:
                    message = value["messages"][-1]
                    if hasattr(message, "content"):
                        print(f"🤖 AI: {message.content}")