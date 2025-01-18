import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver  # 메모리 기능 추가
load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages]




def setup_graph():
    # 메모리 설정
    memory = MemorySaver()

    # 나머지 설정은 동일
    graph_builder = StateGraph(State)
    tool = TavilySearchResults(max_results=2)
    tools = [tool]
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        streaming=True
    )
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", ToolNode(tools=[tool]))
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")

    # 메모리 추가하여 컴파일
    return graph_builder.compile(checkpointer=memory)

def test_chatbot(graph, question: str, thread_id: str = "default"):
    """
    챗봇 테스트 함수 - thread_id로 대화 구분
    """
    print("\n" + "="*50)
    print(f"😀 사용자: {question}")
    print(f"🧵 대화 ID: {thread_id}")
    print("="*50)

    try:
        # thread_id를 포함한 설정 추가
        config = {"configurable": {"thread_id": thread_id}}
        for event in graph.stream(
            {"messages": [("human", question)]},
            config  # 설정 추가
        ):
            for value in event.values():
                if "messages" in value:
                    message = value["messages"][-1]
                    if hasattr(message, "content"):
                        print("\n🤖 AI:", message.content)
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        print("\n🔍 검색 중...")
                        for tool_call in message.tool_calls:
                            print(f"- 검색어: {tool_call['args'].get('query', '')}")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")

def main():
    graph = setup_graph()
    print("✅ 챗봇 준비 완료!\n")

    # 첫 번째 대화 (thread_id: conversation_1)
    print("\n🗣️ 첫 번째 대화 시작")
    thread_1 = "conversation_1"
    questions_1 = [
        "내 이름은 철수야",
        "내 이름이 뭐였지?",
        "나는 학생이야",
        "내가 뭐라고 했었지?"
    ]

    for question in questions_1:
        test_chatbot(graph, question, thread_1)
        print("\n" + "-"*50)

    # 두 번째 대화 (thread_id: conversation_2)
    print("\n🗣️ 두 번째 대화 시작")
    thread_2 = "conversation_2"
    questions_2 = [
        "안녕! 내 이름은 영희야",
        "내 이름이 뭐였지?",
        "나는 선생님이야",
        "내가 뭐라고 했었지?"
    ]

    for question in questions_2:
        test_chatbot(graph, question, thread_2)
        print("\n" + "-"*50)

if __name__ == "__main__":
    main()