from typing import Annotated, Literal
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# State 타입 정의
class MessagesState(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def get_weather(location: str) -> str:
    """특정 지역의 날씨 정보를 반환합니다"""
    if location in ["서울", "인천"]:
        return "현재 기온은 15도이고 안개가 끼었습니다."
    else:
        return "현재 기온은 32도이고 맑습니다."

@tool
def get_coolest_cities() -> str:
    """가장 시원한 도시 목록을 반환합니다"""
    return "서울, 고성"

# 도구 목록 생성
tools = [get_weather, get_coolest_cities]

# ToolNode 생성
tool_node = ToolNode(tools=tools)

llm = ChatOpenAI(
    model="gpt-4",
    timeout=10,
)
model_with_tools = llm.bind_tools(tools)


def should_continue(state: MessagesState) -> Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

def call_model(state: MessagesState):
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def example2():
    # 워크플로우 생성
    workflow = StateGraph(MessagesState)

    # 노드 추가
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    # 엣지 추가
    workflow.add_edge(START, "agent")

    # 조건부 엣지 추가
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )

    # 도구 노드에서 에이전트로 돌아가는 엣지
    workflow.add_edge("tools", "agent")

    # 그래프 컴파일
    graph = workflow.compile()

    for chunk in graph.stream({
        "messages": [("human", "가장 추운 도시의 날씨는 어때?")]
    }, stream_mode="values"):
        chunk['messages'][-1].pretty_print()

def main():
    example2()

if __name__ == "__main__":
    main()