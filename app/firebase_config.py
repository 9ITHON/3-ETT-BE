from datetime import datetime
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

def save_feedback(rating: str, comment: Optional[str], user_id: Optional[str] = None):
    doc_ref = db.collection("feedbacks").document()
    doc_ref.set({
        "rating": rating,
        "comment": comment,
        "timestamp": datetime.utcnow(),
        "user_id": user_id
    })

def save_entry(user_id: str, translated_text: str, timestamp : str):
    doc_ref = db.collection("entries").document()
    doc_ref.set({
        "user_id": user_id,
        "translated_text": translated_text,
        "timestamp": timestamp
    })


def get_entries_by_user_id(user_id: str):
    docs = db.collection("entries").where("user_id", "==", user_id).order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    return [
        {
            "entry_id": doc.id,
            "translated_text": doc.to_dict().get("translated_text"),
            "timestamp": doc.to_dict().get("timestamp")
        }
        for doc in docs
    ]

def get_entry_by_id(entry_id: str):
    doc_ref = db.collection("entries").document(entry_id)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        return {
            "entry_id": doc.id,
            "translated_text": data.get("translated_text"),
            "timestamp": data.get("timestamp"),
            "user_id": data.get("user_id")
        }
    else:
        return None



def delete_entry(user_id: str, entry_id: str):
    doc_ref = db.collection("entries").document(entry_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError("해당 entry가 존재하지 않습니다.")

    if doc.to_dict().get("user_id") != user_id:
        raise PermissionError("해당 entry를 삭제할 권한이 없습니다.")

    doc_ref.delete()