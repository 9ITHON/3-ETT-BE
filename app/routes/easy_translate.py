import json
from datetime import datetime
from fastapi import APIRouter, Depends, Body, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.services.easyTranslate import EasyTranslateService
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/easy_translate", tags=["쉬운말 번역"])
service = EasyTranslateService()

# 요청/응답 스키마 정의
class TranslateRequest(BaseModel):
    content: str

class TranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    timestamp: str

@router.post("/", response_model=TranslateResponse)
async def easy_translate(
    req: TranslateRequest,
    # user_id: str = Depends(get_current_user),
    summary="일반 모드"
    ):
    text = req.content.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="content가 필요합니다"
        )
    # non-streaming 번역
    translated = service.translate(text)
    return TranslateResponse(
        original_text=text,
        translated_text=translated,
        timestamp=datetime.utcnow().isoformat() + "+00:00"
    )

@router.post(
    "/streaming",
    response_class=StreamingResponse,
    summary="스트리밍 모드 (text/event-stream)"
)
async def easy_translate_streaming(
    req: TranslateRequest,
    # user_id: str = Depends(get_current_user),
):
    text = req.content.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="content가 필요합니다"
        )

    async def event_generator():
        state = None
        # service.stream_translate 는 async generator
        async for s in service.stream_translate(text):
            state = s
            chunk = state["translated"][-1]
            data = json.dumps({"translated_text_chunk": chunk}, ensure_ascii=False)
            yield f"event: translate\ndata: {data}\n\n"

        # done 이벤트
        full = "".join(state["translated"]) if state else ""
        done_payload = {
            "original_text": text,
            "translated_text": full,
            "timestamp": datetime.utcnow().isoformat() + "+00:00"
        }
        yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
