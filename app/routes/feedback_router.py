from fastapi import APIRouter, Depends, HTTPException, status
from app.utils.auth_utils import get_optional_user  # 로그인 상태에 따라
from app.firebase_config import save_feedback
from pydantic import BaseModel
from typing import Optional

class FeedbackRequest(BaseModel):
    rating: str  # 최고예요 | 별로예요
    comment: Optional[str] = None
    
router = APIRouter(prefix="/feedback")

@router.post("")
async def submit_feedback(
    payload: FeedbackRequest,
    user: Optional[str] = Depends(get_optional_user)  # 비로그인 가능하게 하려면 Optional 처리도 가능
):
    try:
        save_feedback(
            rating=payload.rating,
            comment=payload.comment,
            user_id=user if user else None
        )
        return {
            "code": status.HTTP_200_OK,
            "message": "피드백이 저장됨."
        }
    except Exception as e:
        print(f"[ERROR] 피드백 저장 실패: {e}")
        raise HTTPException(status_code=500, detail="Feedback 저장 실패")