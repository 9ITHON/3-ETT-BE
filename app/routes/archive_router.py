from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.firebase_config import delete_archive, get_archives_by_user_id, save_archive, get_archive_by_id
from app.utils.auth_utils import get_current_user  # 카카오 인증을 사용하는 함수

class ArchiveSaveRequest(BaseModel):
    translated_text: str
    timestamp: str

router = APIRouter(prefix="/archive")

# /save: 사용자의 번역된 텍스트를 Firestore에 저장하는 엔드포인트
@router.post("/save")
async def save_archive_route(
    request_data: ArchiveSaveRequest,
    user = Depends(get_current_user)
):
    try:
        save_archive(user_id=user, translated_text=request_data.translated_text, timestamp=request_data.timestamp)
        return {
            "code": status.HTTP_200_OK,
            "message": "아카이브에 성공적으로 저장함."
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="저장 중 오류 발생")

# # /list: 사용자가 저장한 모든 번역 기록을 가져오는 엔드포인트
# @router.get("/list")
# async def get_archives(user=Depends(get_current_user)):
#     try:
#         archives = get_archives_by_user_id(user)
#         return {
#             "code": status.HTTP_200_OK,
#             "archives": archives
#         }
#     except Exception as e:
#         print(f"[ERROR] 번역 목록 조회 실패: {e}")
#         raise HTTPException(status_code=500, detail="번역 목록 조회 중 오류 발생")
    
@router.get("/list")
async def get_archives(
    cursor: Optional[str] = None,
    limit: int = 10,
    user=Depends(get_current_user)
):
    try:
        result = get_archives_by_user_id(user, cursor=cursor, limit=limit)
        return {
            "code": status.HTTP_200_OK,
            "archives": result["archives"],
            "next_cursor": result["next_cursor"],
            "has_more": result["has_more"]
        }
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"[ERROR] 번역 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="번역 목록 조회 중 오류 발생")

# /delete/{archive_id}: 특정 번역 기록을 삭제하는 엔드포인트
@router.delete("/delete/{archive_id}")
async def delete_archive_route(
    archive_id: str,
    user = Depends(get_current_user)
):
    try:
        delete_archive(user_id=user, archive_id=archive_id)
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

# /{archive_id}: 특정 번역 기록의 세부 정보를 가져오는 엔드포인트
@router.get("/detail/{archive_id}")
async def get_archive_detail(
    archive_id: str,
    user = Depends(get_current_user)
):
    try:
        archive = get_archive_by_id(archive_id)

        if not archive:
            raise HTTPException(status_code=404, detail="해당 번역을 찾을 수 없습니다.")
        if archive.get("user_id") != user:
            raise HTTPException(status_code=403, detail="해당 번역에 접근 권한이 없습니다.")

        return {
            "code": status.HTTP_200_OK,
            "archive": {
                "translated_text": archive.get("translated_text"),
                "timestamp": archive.get("timestamp"),
                "archive_id": archive_id
            }
        }

    except Exception as e:
        print(f"[ERROR] 상세조회 실패: {e}")
        raise HTTPException(status_code=500, detail="상세 조회 중 오류 발생")

__all__ = ["router"]