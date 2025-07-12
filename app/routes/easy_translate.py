import json
from datetime import datetime
from fastapi import APIRouter, Depends, Body, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.services.easyTranslate import EasyTranslateService
from app.utils.auth_utils import get_current_user
from app.utils.logger import logger
from app.middleware.request_id import get_request_id


router = APIRouter(prefix="/easy-translate", tags=["쉬운말 번역"])
service = EasyTranslateService()

# 요청/응답 스키마 정의
class TranslateRequest(BaseModel):
    content: str

class TranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    timestamp: str

@router.post("", response_model=TranslateResponse)
async def easy_translate(
    req: TranslateRequest,
    request: Request,
    # user_id: str = Depends(get_current_user),
    ):
    text = req.content.strip()
    request_id = get_request_id(request)
    user_id = None  # 현재 주석 처리됨
    
    # 입력 검증 로그
    logger.info(f"번역 API 호출 - 엔드포인트: /easy-translate", request_id=request_id)
    
    if not text:
        logger.warning("빈 텍스트 요청", request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="content가 필요합니다"
        )
    
    # 번역 실행
    translated = service.translate(text, user_id, request_id)
    
    # 응답 생성
    response = TranslateResponse(
        original_text=text,
        translated_text=translated,
        timestamp=datetime.utcnow().isoformat()
    )
    
    logger.info(f"번역 API 완료 - 응답 길이: {len(translated)}자", request_id=request_id)
    
    return response

@router.post(
    "/streaming",
    response_class=StreamingResponse,
)
async def easy_translate_streaming(
    req: TranslateRequest,
    request: Request,
    # user_id: str = Depends(get_current_user),
):
    text = req.content.strip()
    request_id = get_request_id(request)
    user_id = None  # 현재 주석 처리됨
    
    # 입력 검증 로그
    logger.info(f"스트리밍 번역 API 호출 - 엔드포인트: /easy-translate/streaming", request_id=request_id)
    
    if not text:
        logger.warning("빈 텍스트 요청 (스트리밍)", request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="content가 필요합니다"
        )

    async def event_generator():
        state = None
        chunk_count = 0
        
        try:
            # 스트리밍 번역 실행
            async for s in service.stream_translate(text, user_id, request_id):
                state = s
                chunk_count += 1
                chunk = state["translated"][-1]
                data = json.dumps({"translated_text_chunk": chunk}, ensure_ascii=False)
                yield f"event: translate\ndata: {data}\n\n"

            # done 이벤트
            full = "".join(state["translated"]) if state else ""
            done_payload = {
                "original_text": text,  
                "translated_text": full,
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
            
            logger.info(f"스트리밍 번역 API 완료 - 총 청크: {chunk_count}개", request_id=request_id)
            
        except Exception as e:
            logger.error(f"스트리밍 번역 API 에러: {str(e)}", request_id=request_id)
            error_payload = {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"event: error\ndata: {json.dumps(error_payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
