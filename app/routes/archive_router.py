from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.firebase_config import delete_entry, get_entries_by_user_id, save_entry, get_entry_by_id
from app.utils.auth_utils import get_current_user  # 카카오 인증을 사용하는 함수

class EntrySaveRequest(BaseModel):
    translated_text: str
    timestamp: str

router = APIRouter(prefix="/entry")

# /save: 사용자의 번역된 텍스트를 Firestore에 저장하는 엔드포인트
@router.post("/save")
async def save_entry_route(
    request_data: EntrySaveRequest,
    user = Depends(get_current_user)  # get_current_user에서 kakao_id를 가져옵니다
):
    try:
        # 사용자 인증된 kakao_id를 기반으로 Firestore에 번역 기록 저장
        save_entry(user_id=user, translated_text=request_data.translated_text, timestamp=request_data.timestamp)
        return {
            "code": status.HTTP_200_OK,
            "message": "아카이브에 성공적으로 저장함."
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="저장 중 오류 발생")

# /list: 사용자가 저장한 모든 번역 기록을 가져오는 엔드포인트
@router.get("/list")
async def get_entries(user=Depends(get_current_user)):  # get_current_user에서 kakao_id를 가져옵니다
    try:
        # 사용자의 번역 기록을 가져오는 함수 호출
        entries = get_entries_by_user_id(user)
        return {
            "code": status.HTTP_200_OK,
            "entries": entries
        }
    except Exception as e:
        print(f"[ERROR] 번역 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="번역 목록 조회 중 오류 발생")

# /delete/{entry_id}: 특정 번역 기록을 삭제하는 엔드포인트
@router.delete("/{entry_id}")
async def delete_entry_route(
    entry_id: str,
    user = Depends(get_current_user)  # get_current_user에서 kakao_id를 가져옵니다
):
    try:
        # 사용자가 해당 번역 기록을 삭제할 수 있도록 Firestore에서 삭제
        delete_entry(user_id=user, entry_id=entry_id)
        return {
            "code": 200,
            "message": "번역이 성공적으로 삭제되었습니다."
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        print(f"[ERROR] 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="삭제 중 오류 발생")

# /{entry_id}: 특정 번역 기록의 세부 정보를 가져오는 엔드포인트
@router.get("/{entry_id}")
async def get_entry_detail(
    entry_id: str,
    user = Depends(get_current_user)  # get_current_user에서 kakao_id를 가져옵니다
):
    try:
        # 번역 기록의 세부 정보를 가져오는 함수 호출
        entry = get_entry_by_id(entry_id)

        if not entry:
            raise HTTPException(status_code=404, detail="해당 번역을 찾을 수 없습니다.")
        if entry.get("user_id") != user:
            raise HTTPException(status_code=403, detail="해당 번역에 접근 권한이 없습니다.")

        return {
            "code": status.HTTP_200_OK,
            "entry": {
                "translated_text": entry.get("translated_text"),
                "timestamp": entry.get("timestamp"),
                "entry_id": entry_id
            }
        }

    except Exception as e:
        print(f"[ERROR] 상세조회 실패: {e}")
        raise HTTPException(status_code=500, detail="상세 조회 중 오류 발생")
    
__all__ = ["router"]
