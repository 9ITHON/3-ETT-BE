from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import Self

from app.agent.easyTranslate.state import TranslateState
from app.agent.easyTranslate.node import EasyTranslateNode
from langchain_openai import ChatOpenAI
from app.config import Global

class EasyTranslateGraph:
    def __init__(self):
        # 환경변수 검증
        Global.validate_env()

        # streaming 용과 non-streaming 용 llm을 분리 생성
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=Global.env.OPENAI_API_KEY,
            streaming=False
        )
        self.llm_stream = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=Global.env.OPENAI_API_KEY,
            streaming=True
        )

        # 상태 기반 Graph 빌더
        self._builder = StateGraph(TranslateState)
        self.build()
        self.graph: CompiledStateGraph = self._builder.compile()

    def build(self) -> Self:
        # 'translate' 노드에 EasyTranslateNode 주입 (non-streaming)
        node = EasyTranslateNode(self.llm)
        self._builder.add_node("translate", node.invoke)

        # START → translate → END
        self._builder.add_edge(START, "translate")
        self._builder.add_edge("translate", END)

        return self

    def run(self, text: str) -> TranslateState:
        # Graph.invoke: non-streaming 한 번에 최종 상태 반환
        init_state: TranslateState = {"original": text, "translated": []}
        return self.graph.invoke(init_state)

    def stream(self, text: str):
        # 직접 Node.ainvoke 를 사용해 스트리밍
        init_state: TranslateState = {"original": text, "translated": []}
        node = EasyTranslateNode(self.llm_stream)
        # START 로직 없이 바로 Node로
        return node.ainvoke(init_state)
