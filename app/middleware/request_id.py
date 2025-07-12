import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time


class RequestIDMiddleware(BaseHTTPMiddleware):
    """각 요청에 고유 ID를 부여하는 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 요청 시작 시간 기록
        start_time = time.time()
        request.state.start_time = start_time
        
        # 헤더에 요청 ID 추가
        response = await call_next(request)
        
        # 응답 시간 계산
        process_time = time.time() - start_time
        
        # 응답 헤더에 요청 ID와 처리 시간 추가
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


def get_request_id(request: Request) -> str:
    """요청에서 request_id 추출"""
    return getattr(request.state, 'request_id', None)


def get_process_time(request: Request) -> float:
    """요청 처리 시간 계산"""
    start_time = getattr(request.state, 'start_time', None)
    if start_time:
        return time.time() - start_time
    return 0.0
