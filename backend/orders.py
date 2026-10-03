from fastapi import APIRouter, Depends
from app.auth import get_user_id
from app.database import ORDERS

router = APIRouter()

@router.get("/orders/{order_id}")
def get_order(order_id: str, current_user: str = Depends(get_user_id)):
    # Intentionally vulnerable: current_user is authenticated but ownership
    # is NOT checked against the order owner.
    order = ORDERS.get(order_id)
    if not order:
        return {"error": "Order not found"}
    return order

@router.get("/profile")
def profile(current_user: str = Depends(get_user_id)):
    return {"user_id": current_user, "message": "Authenticated profile"}
