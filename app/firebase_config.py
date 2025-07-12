from datetime import datetime
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore
from app.utils.logger import logger
import pytz

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()



def save_feedback(rating: str, comment: Optional[str], user_id: Optional[str] = None):
    doc_ref = db.collection("feedbacks").document()
    doc_ref.set({
        "rating": rating,
        "comment": comment,
        "timestamp": datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%dT%H:%M:%S"),
        "user_id": user_id
    })

def save_archive(user_id: str, translated_text: str, timestamp : str):
    doc_ref = db.collection("archives").document()
    doc_ref.set({
        "user_id": user_id,
        "translated_text": translated_text,
        "timestamp": timestamp
    })

def get_archives_by_user_id(user_id: str):
    docs = db.collection("archives").where("user_id", "==", user_id).order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    return [
        {
            "archive_id": doc.id,
            "translated_text": doc.to_dict().get("translated_text"),
            "timestamp": doc.to_dict().get("timestamp")
        }
        for doc in docs
    ]

# def get_archives_by_user_id(user_id: str, cursor: Optional[str] = None, limit: int = 10):
#     db = firestore.client()

#     query = db.collection("archives") \
#               .where("user_id", "==", user_id) \
#               .order_by("timestamp", direction=firestore.Query.DESCENDING)

#     if cursor:
#         try:
#             cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
#             query = query.start_after({"timestamp": cursor_dt})
#         except ValueError:
#             raise ValueError("커서 timestamp 형식이 올바르지 않습니다.")

#     docs = list(query.limit(limit + 1).stream())

#     archives = []
#     for doc in docs:
#         data = doc.to_dict()
#         archives.append({
#             "archive_id": doc.id,
#             "translated_text": data.get("translated_text"),
#             "timestamp": data.get("timestamp")
#         })

#     has_more = len(archives) > limit
#     archives = archives[:limit]
#     next_cursor = archives[-1]["timestamp"].isoformat() if has_more else None

#     return {
#         "archives": archives,
#         "next_cursor": next_cursor,
#         "has_more": has_more
#     }

def get_archive_by_id(archive_id: str):
    doc_ref = db.collection("archives").document(archive_id)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        return {
            "archive_id": doc.id,
            "translated_text": data.get("translated_text"),
            "timestamp": data.get("timestamp"),
            "user_id": data.get("user_id")
        }
    else:
        return None

def delete_archive(user_id: str, archive_id: str):
    doc_ref = db.collection("archives").document(archive_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError("해당 archive가 존재하지 않습니다.")

    if doc.to_dict().get("user_id") != user_id:
        raise PermissionError("해당 archive를 삭제할 권한이 없습니다.")

    doc_ref.delete()

def search_archives_query(user_id: str, query: str):
    """사용자 아카이브에서 검색"""
    try:
        docs = db.collection("archives") \
                  .where("user_id", "==", user_id) \
                  .order_by("timestamp", direction=firestore.Query.DESCENDING) \
                  .stream()
        
        results = []
        query_lower = query.lower()
        
        for doc in docs:
            doc_data = doc.to_dict()
            translated_text = doc_data.get("translated_text", "")
            
            # 문자열이든 배열이든 처리
            if isinstance(translated_text, str):
                if query_lower in translated_text.lower():
                    results.append(doc_data)
            elif isinstance(translated_text, list):
                if any(query_lower in text.lower() for text in translated_text):
                    results.append(doc_data)

        logger.info(f"검색 결과: {len(results)}개 문서", user_id=user_id, query=query)
        return results
    
    except Exception as e:
        print(f"검색 중 오류 발생: {e}")
        return []
