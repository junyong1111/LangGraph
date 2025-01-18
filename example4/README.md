# LangGraph Example 4: Human-in-the-Loop Workflow 🤝

이 예제는 LangGraph를 사용하여 AI와 사람이 협업하는 워크플로우를 구현하는 방법을 보여줍니다. 중요한 결정이나 검토가 필요한 경우 사람의 승인을 받고 처리할 수 있다.

## 주요 기능 🎯

1. 실시간 사람 개입
   - AI가 중요한 결정에서 사람의 승인을 요청
   - `interrupt` 기능을 통한 워크플로우 일시 중지
   - 사람의 응답에 따른 처리 재개

2. 도구 통합
   - 웹 검색 도구 (Tavily)
   - 사람 도움 요청 도구 (`human_assistance`)

3. 상태 관리
   - `MemorySaver`를 통한 대화 상태 유지
   - 중단된 상태에서의 복구 가능

## 설치 방법 ⚙️

```bash
# 필요한 패키지 설치
pip install langchain langgraph langchain-openai python-dotenv

# .env 파일 설정
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
```

## 사용 예시 💡

```python
# 기본 사용
test_chatbot(graph, "이 코드가 안전한가요?")

# 출력 예시
😀 사용자: 이 코드가 안전한가요?
🤖 AI: 코드를 검토하기 위해 전문가의 도움을 요청하겠습니다.
👋 사람의 확인이 필요합니다!
응답을 입력하세요: 이 코드는 안전하지 않습니다. 수정이 필요합니다.
```

## 테스트 시나리오 🧪

1. 코드 안전성 검토
   ```
   이 코드가 안전한지 검토해주세요: import os; os.system('rm -rf /')
   ```

2. 데이터베이스 작업 승인
   ```
   중요한 데이터베이스를 삭제하려고 하는데 확인해주세요
   ```

3. 금융 거래 승인
   ```
   이 거래를 승인해도 될까요? 금액: $10,000
   ```

## 주요 구성 요소 설명 📚

1. `human_assistance` 도구
```python
@tool
def human_assistance(query: str) -> str:
    """사람의 도움을 요청합니다."""
    human_response = interrupt({"query": query})
    return human_response["data"]
```

2. 상태 관리
```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
```

## 주의사항 ⚠️

1. API 키 설정
   - OpenAI API 키 필요
   - Tavily API 키 필요

2. 실행 환경
   - Python 3.9 이상 필요
   - 인터넷 연결 필요

3. 사용 제한
   - API 호출 비용 발생 가능
   - 실시간 응답 필요

## 확장 가능성 🚀

1. 추가 기능
   - 웹 인터페이스 구현
   - 승인 프로세스 다양화
   - 로깅 시스템 추가

2. 커스터마이징
   - 다양한 도구 추가
   - 승인 조건 설정
   - 응답 형식 변경

## 참고 자료 📖

- [LangGraph 공식 문서](https://python.langchain.com/docs/langgraph)
- [Human-in-the-Loop 패턴](https://python.langchain.com/docs/langgraph/patterns)
- [Tool Calling 가이드](https://python.langchain.com/docs/modules/model_io/tools)