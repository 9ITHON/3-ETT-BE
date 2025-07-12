import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import uuid
import hashlib

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")

import httpx
from fastapi import APIRouter, Body, HTTPException, Header, Query, status
from datetime import datetime, timedelta
from app.firebase_config import db
from app.utils.auth_utils import create_jwt_token, generateUserUUID

class RefreshTokenRequest(BaseModel):
    refresh_token: str

router = APIRouter(prefix="/auth")

KAKAO_CLIENT_ID = os.getenv("KAKAO_REST_API_KEY")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", None)

@router.get("/login")
async def redirect_to_kakao_login():
    kakao_auth_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?response_type=code"
        f"&client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
    )
    return RedirectResponse(url=kakao_auth_url)

@router.get("/login/kakao")
async def kakao_login(code: str):
    print("KAKAO_CLIENT_ID =", KAKAO_CLIENT_ID)
    print("redirect_uri =", KAKAO_REDIRECT_URI)

    # 1. 카카오에 토큰 요청
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    if KAKAO_CLIENT_SECRET:
        token_data["client_secret"] = KAKAO_CLIENT_SECRET

    async with httpx.AsyncClient() as client:
        token_resp = await client.post("https://kauth.kakao.com/oauth/token", data=token_data)
        print("Token Response:", token_resp.status_code, token_resp.text)


    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="카카오 토큰 요청 실패")

    access_token = token_resp.json().get("access_token")
    refresh_token = token_resp.json().get("refresh_token")
    refresh_token_expires_in = token_resp.json().get("refresh_token_expires_in")
    expires_in = token_resp.json().get("expires_in")

    # 2. 사용자 정보 요청
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if user_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보 요청 실패")

    user_info = user_resp.json()
    kakao_id = str(user_info.get("id"))
    profile = user_info.get("kakao_account", {}).get("profile", {})
    nickname = profile.get("nickname")
    email = user_info.get("kakao_account", {}).get("email")

    user_data = {
        "kakao_id": kakao_id,
        "nickname": nickname,
        "email": email
    }

    print("User Data:", user_data)

    # uuid 생성
    user_uuid = await generateUserUUID(user_data)

    # 3. Firestore에 사용자 등록 (없으면)
    user_ref = db.collection("users").document(user_uuid)
    if not user_ref.get().exists:
        user_ref.set({
            "nickname": nickname,
            "created_at": datetime.utcnow().isoformat()
        })

    # JWT 토큰 생성 -> access_token, expires_in
    jwt_token = await create_jwt_token(user_uuid)

    return {
        "code" : status.HTTP_200_OK,
        "access_token": jwt_token.get("access_token"), 
        "access_token_expires_in" : jwt_token.get("access_token_expires_in")
    }

# @router.post("/kakao-refresh")
# async def refresh(data: RefreshTokenRequest = Body(...)):
#     token_data = {
#         "grant_type": "refresh_token",
#         "client_id": KAKAO_CLIENT_ID,
#         "refresh_token": data.refresh_token,
#     }

#     async with httpx.AsyncClient() as client:
#         token_resp = await client.post("https://kauth.kakao.com/oauth/token", data=token_data)

#     if token_resp.status_code != 200:
#         print("Error Response: ", token_resp.text)
#         raise HTTPException(status_code=400, detail="카카오 토큰 갱신 실패")

#     response_data = token_resp.json()
#     new_access_token = response_data.get("access_token")

#     return {
#         "code": status.HTTP_200_OK,
#         "access_token": new_access_token,
#     }


# @router.post("/logout")
# async def logout(authorization: str = Header(...)):
#     logout_url = "https://kapi.kakao.com/v1/user/logout"
    
#     headers = {
#         "Authorization": authorization,
#         "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
#     }

#     async with httpx.AsyncClient() as client:
#         response = await client.post(logout_url, headers=headers)

#     if response.status_code != 200:
#         raise HTTPException(status_code=400, detail="카카오 로그아웃 요청 실패")

#     response_data = response.json()
#     return {
#         "code": status.HTTP_200_OK,
#         "message": f"User {response_data['id']} has been logged out successfully."
#     }