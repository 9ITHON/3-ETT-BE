from datetime import datetime, timedelta
import uuid, hashlib
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path
import httpx
import os
import jwt

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")

KAKAO_CLIENT_ID = os.getenv("KAKAO_REST_API_KEY")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", None)

ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)

async def create_jwt_token(user_uuid: str):
    now = datetime.utcnow()
    
    access_payload = {
        "sub": user_uuid,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access"
    }

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": access_token,
        "access_token_expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }

# def verify_refresh_token(token: str) -> str:
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         if payload.get("type") != "refresh":
#             raise HTTPException(status_code=401, detail="refresh 토큰 아님")
#         return payload.get("sub")  # user_uuid
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="refresh 토큰 만료")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="refresh 토큰이 잘못됨")

async def generateUserUUID(user_data: dict) -> str:

    kakao_id = user_data.get("kakao_id", "")
    email = user_data.get("email", "")
    nickname = user_data.get("nickname", "")
    
    # 1. 시드 문자열 생성 (Java의 String.format처럼)
    seed = f"kakao_{kakao_id}_{email}_{nickname}"
    
    # 2. SHA-256 해시 적용
    hash_bytes = hashlib.sha256(seed.encode('utf-8')).digest()
    
    # 3. 해시 바이트를 기반으로 UUID 생성
    user_uuid = uuid.UUID(bytes=hash_bytes[:16])  # 16바이트로 잘라야 함

    return str(user_uuid)

# 1. 인증 필수인 경우
async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 정보가 없습니다")

    access_token = auth_header.replace("Bearer ", "")

    try:
        # 카카오 사용자 정보 요청
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="access 토큰 아님")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰 만료")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="잘못된 토큰")
    

# 인증이 선택인 경우
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[str]:
    if credentials is None:
        return None

    access_token = credentials.credentials

    try:
        # JWT 디코딩
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")  # user_uuid 반환
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
