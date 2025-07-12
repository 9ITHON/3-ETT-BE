from datetime import datetime, timedelta
import uuid, hashlib
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import httpx
import os
import jwt

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
    refresh_payload = {
        "sub": user_uuid,
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh"
    }

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_token_expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token_expires_in": REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    }

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
        user_resp = await httpx.AsyncClient().get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="카카오 사용자 정보 요청 실패")

        user_info = user_resp.json()
        kakao_id = str(user_info.get("id"))

        # 사용자 인증 확인
        return kakao_id
    except Exception as e:
        print(f"[ERROR] 인증 실패: {e}")
        raise HTTPException(status_code=401, detail="카카오 인증 실패")

# 2. 인증이 선택인 경우
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[str]:
    if credentials is None:
        return None

    access_token = credentials.credentials

    try:
        # 카카오 사용자 정보 요청
        user_resp = await httpx.AsyncClient().get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_resp.status_code != 200:
            return None

        user_info = user_resp.json()
        kakao_id = str(user_info.get("id"))
        return kakao_id
    except Exception as e:
        print(f"[ERROR] 인증 실패: {e}")
        return None
