from app.agent.easyTranslate.graph import EasyTranslateGraph
from fastapi import HTTPException

class EasyTranslateService:
    def __init__(self):
        self.graph = EasyTranslateGraph()

    def translate(self, text: str) -> str:
        # 단문 non-streaming 번역
        state = self.graph.run(text)

        print(f"번역 결과: {state['translated'][0]}")
        
        # 리스트로 모인 조각들을 하나의 문자열로
        return "".join(state["translated"])

    def stream_translate(self, text: str):
        # SSE 스트리밍용 generator
        try:
            return self.graph.stream(text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"번역 중 오류: {e}")
