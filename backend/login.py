from fastapi import APIRouter
from pydantic import BaseModel
from app.database import USERS

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(payload: LoginRequest):
    for user_id, user in USERS.items():
        if user["username"] == payload.username and user["password"] == payload.password:
            return {
                "access_token": "riya-demo-token" if user_id == "1" else "sheetal-demo-token",
                "token_type": "bearer",
                "user_id": user_id,
            }
    return {"message": "Invalid credentials"}
