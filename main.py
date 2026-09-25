from fastapi import FastAPI
from app.routes.login import router as login_router
from app.routes.users import router as users_router
from app.routes.orders import router as orders_router

app = FastAPI(
    title="SentinelAPI Demo Banking API",
    description="Intentionally vulnerable local API for SentinelAPI testing.",
    version="1.0.0",
)

@app.get("/")
def root():
    return {
        "name": "SentinelAPI Demo API",
        "warning": "Intentionally vulnerable. Use locally only.",
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

app.include_router(login_router)
app.include_router(users_router)
app.include_router(orders_router)
