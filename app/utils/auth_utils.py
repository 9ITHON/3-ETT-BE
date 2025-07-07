from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import httpx
import os

KAKAO_CLIENT_ID = os.getenv("KAKAO_REST_API_KEY")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", None)

security = HTTPBearer(auto_error=False)

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
