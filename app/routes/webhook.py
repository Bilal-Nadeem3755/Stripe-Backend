from fastapi import APIRouter, Request, HTTPException, status
from app.utils.stripe_client import stripe
from app.database import db
import os

router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"]
)

# 🔐 Stripe webhook secret (Stripe CLI se milta hai)
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if not STRIPE_WEBHOOK_SECRET:
    raise RuntimeError("❌ STRIPE_WEBHOOK_SECRET missing in environment variables")

@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # ❌ Agar Stripe-Signature hi na ho
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header"
        )

    # 🔐 Signature verify
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError: # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe signature"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # =========================
    # ✅ EVENT HANDLING START
    # =========================

    event_type = event["type"]
    data = event["data"]["object"]

    # ✅ Payment Intent Success
    if event_type == "payment_intent.succeeded":
        payment_intent_id = data["id"]
        customer_id = data.get("customer")

        print("✅ Payment succeeded:", payment_intent_id)

        # 🧠 Example DB update
        db["payments"].insert_one({
            "payment_intent_id": payment_intent_id,
            "customer_id": customer_id,
            "status": "succeeded"
        })

    # ❌ Payment Failed
    elif event_type == "payment_intent.payment_failed":
        payment_intent_id = data["id"]

        print("❌ Payment failed:", payment_intent_id)

        db["payments"].insert_one({
            "payment_intent_id": payment_intent_id,
            "status": "failed"
        })

    # 💳 Payment Method Attached
    elif event_type == "payment_method.attached":
        payment_method = data
        customer_id = payment_method.get("customer")

        print("💳 Card attached to customer:", customer_id)

    # ⚠️ Unhandled events (safe ignore)
    else:
        print("ℹ️ Unhandled event:", event_type)

    return {"status": "success"}
