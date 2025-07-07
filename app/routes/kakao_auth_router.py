import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")

import httpx
from fastapi import APIRouter, HTTPException, Query, status
from datetime import datetime, timedelta
from app.firebase_config import db

router = APIRouter(prefix="/auth")

KAKAO_CLIENT_ID = os.getenv("KAKAO_REST_API_KEY")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", None)

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

    print("kakao_id : " ,kakao_id)

    # 3. Firestore에 사용자 등록 (없으면)
    user_ref = db.collection("users").document(kakao_id)
    if not user_ref.get().exists:
        user_ref.set({
            "nickname": nickname,
            "created_at": datetime.utcnow().isoformat()
        })

    return {
        "code" : status.HTTP_200_OK,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh_token_expires_in": refresh_token_expires_in,
        "user": {
            "id": kakao_id,
            "nickname": nickname
        }
    }

@router.post("/refresh")
async def refresh(refresh_token: str = Query(...)):
    # 1. 카카오에 토큰 요청
    token_data = {
        "grant_type": "refresh_token",
        "client_id": KAKAO_CLIENT_ID,
        "refresh_token": refresh_token,
    }

    # 카카오의 토큰 갱신 API 호출
    async with httpx.AsyncClient() as client:
        token_resp = await client.post("https://kauth.kakao.com/oauth/token", data=token_data)

    if token_resp.status_code != 200:
        print("Error Response: ", token_resp.text)
        raise HTTPException(status_code=400, detail="카카오 토큰 갱신 실패")

    # 새로운 액세스 토큰과 리프레시 토큰을 응답으로 반환
    response_data = token_resp.json()
    
    new_access_token = response_data.get("access_token")

    return {
        "code": status.HTTP_200_OK,
        "access_token": new_access_token,
    }

@router.post("/logout")
async def logout(access_token: str = Query(...), target_id: str = Query(...)):
    # 카카오 로그아웃 요청 URL
    logout_url = "https://kapi.kakao.com/v1/user/logout"
    
    # 로그아웃 요청 본문 데이터
    data = {
        "target_id_type": "user_id",  # user_id로 고정
        "target_id": target_id  # 로그아웃시킬 사용자 ID
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",  # 액세스 토큰을 Authorization 헤더에 포함
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(logout_url, headers=headers, data=data)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="카카오 로그아웃 요청 실패")

    # 로그아웃 성공 시 응답 처리
    response_data = response.json()
    return {
        "code": status.HTTP_200_OK,
        "message": f"User {response_data['id']} has been logged out successfully."
    }
