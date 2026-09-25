from fastapi import APIRouter
from app.database import USERS

router = APIRouter()

@router.get("/users/{user_id}")
def get_user(user_id: str):
    # Intentionally vulnerable for local scanner demonstration:
    # no ownership/authorization check and sensitive fields are returned.
    user = USERS.get(user_id)
    if not user:
        return {"error": "User not found"}
    return user

@router.get("/users")
def list_users():
    return list(USERS.values())
