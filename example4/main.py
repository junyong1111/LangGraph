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
from langgraph.types import Command, interrupt
from langchain_core.tools import tool

load_dotenv()

# 상태 정의
class State(TypedDict):
   messages: Annotated[list, add_messages]

# 사람 도움 요청 도구
@tool
def human_assistance(query: str) -> str:
   """사람의 도움을 요청합니다."""
   human_response = interrupt({"query": query})
   return human_response["data"]

def setup_graph():
   # 메모리 설정
   memory = MemorySaver()

   # 그래프 설정
   graph_builder = StateGraph(State)

   # 도구 설정
   search_tool = TavilySearchResults(max_results=2)
   tools = [search_tool, human_assistance]

   # AI 모델 설정
   llm = ChatOpenAI(
       model="gpt-4",
       temperature=0.7,
       streaming=True
   )
   llm_with_tools = llm.bind_tools(tools)

   # 챗봇 노드
   def chatbot(state: State):
       message = llm_with_tools.invoke(state["messages"])
       # 도구 호출이 여러 번 반복되는 것을 방지
       assert len(message.tool_calls) <= 1
       return {"messages": [message]}

   # 노드 추가
   graph_builder.add_node("chatbot", chatbot)
   graph_builder.add_node("tools", ToolNode(tools=tools))

   # 엣지 추가
   graph_builder.add_conditional_edges(
       "chatbot",
       tools_condition,
   )
   graph_builder.add_edge("tools", "chatbot")
   graph_builder.add_edge(START, "chatbot")

   return graph_builder.compile(checkpointer=memory)

def test_chatbot(graph, question: str, thread_id: str = "default"):
   """챗봇 테스트 함수"""
   print("\n" + "="*50)
   print(f"😀 사용자: {question}")
   print("="*50)

   config = {"configurable": {"thread_id": thread_id}}

   try:
       events = graph.stream(
           {"messages": [{"role": "user", "content": question}]},
           config,
           stream_mode="values"
       )

       for event in events:
           if "messages" in event:
               message = event["messages"][-1]
               if hasattr(message, "content"):
                   print(f"\n🤖 AI: {message.content}")

               if hasattr(message, "tool_calls"):
                   print("\n🔄 도구 호출 정보:")
                   for tool_call in message.tool_calls:
                       print(f"- 도구: {tool_call['name']}")
                       print(f"- 입력: {tool_call['args']}")

       # 상태 확인
       state = graph.get_state(config)
       if state.next and "tools" in state.next:
           print("\n👋 사람의 확인이 필요합니다!")
           response = input("응답을 입력하세요: ")

           # 사람의 응답으로 재개
           human_command = Command(resume={"data": response})
           events = graph.stream(human_command, config, stream_mode="values")

           for event in events:
               if "messages" in event:
                   message = event["messages"][-1]
                   if hasattr(message, "content"):
                       print(f"\n🤖 AI: {message.content}")

   except Exception as e:
       print(f"\n❌ 오류 발생: {str(e)}")

def main():
   print("🔄 챗봇 초기화 중...")
   graph = setup_graph()
   print("✅ 챗봇 준비 완료!\n")

   # 테스트 시나리오
   test_cases = [
       "이 코드가 안전한지 검토해주세요: import os; os.system('rm -rf /')",
       "중요한 데이터베이스를 삭제하려고 하는데 확인해주세요",
       "이 거래를 승인해도 될까요? 금액: $10,000",
   ]

   thread_id = "test_conversation"
   for question in test_cases:
       test_chatbot(graph, question, thread_id)
       print("\n" + "-"*50)

if __name__ == "__main__":
   main()