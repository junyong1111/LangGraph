from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def example1():
    class State(MessagesState):
        """
        state는 LangGraph에서 중요한 개념이다:

        1. 상태 저장:
        - 각 노드가 처리한 결과나 중간 데이터를 저장
        - 대화 이력, 계산 결과, 임시 데이터 등을 보관

        2. 상태 전달:
        - 한 노드에서 다음 노드로 데이터를 전달하는 매개체
        - 노드 간 정보 공유와 흐름을 관리

        3. 공통 컨텍스트:
        - 그래프의 모든 노드가 접근할 수 있는 공유 공간
        - TypedDict로 정의하여 타입 안정성 보장

        Annotated, add_messages: 지속적으로 메시지를 추가한다는 의미이다.
        """
        counter: int

    llm = ChatOpenAI(
            model="o1-mini",
            timeout=10,
        )

    def chatbot(state: State) -> State:
        state["counter"] =  state.get("counter", 0) + 1
        state["messages"] = [llm.invoke(state["messages"])]
        return state

    # 이전 상태를 기반으로 새로운 입력 추가
    input_state = {
        "messages": [HumanMessage(content="hello")],
        "counter": 0
    }


    def stream_graph_updates(user_input: str):
        for event in graph.stream({"messages": [("user", user_input)]}):
            for value in event.values():
                print("Assistant:", value["messages"][-1].content)

    """
    LangGraph의 기본 구조 예제:

    1. 노드 정의 (node_a):
    - state를 입력받아 처리하고 반환하는 함수
    - counter 증가, alphabet 설정 등 상태 조작 수행
    - State 타입의 입력을 받고 State 타입을 반환

    2. 그래프 구성 (example1):
    - StateGraph: 상태 기반 그래프 생성
    - add_node: 노드 추가 ("chatbot" 이름으로 node_a 함수 등록)
    - add_edge: 노드 간 연결 설정
        * START -> chatbot: 시작점에서 chatbot 노드로
        * chatbot -> END: chatbot 노드에서 종료점으로

    3. 그래프 컴파일:
    - compile(): 정의된 그래프를 실행 가능한 형태로 변환
    - 노드 간의 연결과 데이터 흐름을 확정
    """

    # 그래프 구성

    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot) # node_a함수를 chatbot노드로 등록

    graph_builder.set_entry_point("chatbot") # graph_builder.add_edge(START, "chatbot")
    graph_builder.set_finish_point("chatbot") # graph_builder.add_edge("chatbot", END)

    # 그래프 컴파일
    graph = graph_builder.compile()

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(user_input)





def main():
    example1()

if __name__ == "__main__":
    main()