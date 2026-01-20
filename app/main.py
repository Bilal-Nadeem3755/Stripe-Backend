from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.payment import router as payment_router
from app.routes.webhook import router as webhook_router

app = FastAPI(
    title="Stripe Backend",
    version="0.1.0"
)

# ✅ ROUTERS INCLUDE
app.include_router(auth_router)
app.include_router(payment_router)
app.include_router(webhook_router)


@app.get("/")
def root():
    return {"message": "Stripe Backend Running"}
