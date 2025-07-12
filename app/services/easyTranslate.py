import time
from app.agent.easyTranslate.graph import EasyTranslateGraph
from fastapi import HTTPException
from app.utils.logger import logger


class EasyTranslateService:
    def __init__(self):
        self.graph = EasyTranslateGraph()
        logger.info("EasyTranslateService 초기화 완료")

    def translate(self, text: str, user_id: str = None, request_id: str = None) -> str:
        """단문 non-streaming 번역"""
        start_time = time.time()
        
        try:
            # 번역 요청 로그
            logger.log_translation_request(text, user_id, request_id)
            
            # 번역 실행
            state = self.graph.run(text)
            
            # 번역 결과 추출
            result = "".join(state["translated"])
            
            # 처리 시간 계산
            duration = time.time() - start_time
            
            # 성공 로그
            logger.log_translation_success(text, result, duration, user_id, request_id)
            
            # 콘솔 출력 (기존 코드 유지)
            print(f"번역 결과: {state['translated'][0] if state['translated'] else 'No translation'}")
            
            return result
            
        except Exception as e:
            # 에러 로그
            logger.log_translation_error(text, e, user_id, request_id)
            
            # 기존 예외 처리
            raise HTTPException(status_code=500, detail=f"번역 중 오류: {e}")

    async def stream_translate(self, text: str, user_id: str = None, request_id: str = None):
        """SSE 스트리밍용 generator"""
        start_time = time.time()
        chunk_count = 0
        
        try:
            # 스트리밍 시작 로그
            logger.log_streaming_start(text, user_id, request_id)
            
            # 스트리밍 번역 실행
            async for state in self.graph.stream(text):
                chunk_count += 1
                
                # 주기적으로 청크 로그
                logger.log_streaming_chunk(chunk_count, user_id, request_id)
                
                yield state
            
            # 스트리밍 완료 로그
            duration = time.time() - start_time
            logger.log_streaming_complete(chunk_count, duration, user_id, request_id)
            
        except Exception as e:
            # 스트리밍 에러 로그
            logger.log_translation_error(text, e, user_id, request_id)
            raise HTTPException(status_code=500, detail=f"스트리밍 번역 중 오류: {e}")
