from fastapi import Header, HTTPException
from app.database import TOKENS

def get_user_id(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = TOKENS.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id
