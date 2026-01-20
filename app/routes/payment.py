# from fastapi import APIRouter, Request, HTTPException
# from app.database import db
# from app.schemas.payment import CreatePaymentMethod
# from app.utils.auth import get_current_user
# from app.utils.stripe_client import stripe
# import os
# from datetime import datetime

# router = APIRouter(prefix="/webhook", tags=["Webhook"])

# STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# @router.post("/stripe")
# async def stripe_webhook(request: Request):
#     payload = await request.body()
#     sig_header = request.headers.get("stripe-signature")

#     try:
#         event = stripe.Webhook.construct_event(
#             payload,
#             sig_header,
#             STRIPE_WEBHOOK_SECRET
#         )
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

#     transactions = db["transactions"]

#     # ✅ PAYMENT SUCCESS
#     if event["type"] == "payment_intent.succeeded":
#         intent = event["data"]["object"]

#         transactions.update_one(
#             {"payment_intent_id": intent["id"]},
#             {
#                 "$set": {
#                     "status": "succeeded",
#                     "confirmed_at": datetime.utcnow()
#                 }
#             }
#         )

#         print("✅ Payment confirmed:", intent["id"])

#     # ❌ PAYMENT FAILED
#     elif event["type"] == "payment_intent.payment_failed":
#         intent = event["data"]["object"]

#         transactions.update_one(
#             {"payment_intent_id": intent["id"]},
#             {
#                 "$set": {
#                     "status": "failed",
#                     "confirmed_at": datetime.utcnow()
#                 }
#             }
#         )

#         print("❌ Payment failed:", intent["id"])

#     return {"status": "ok"}

# @router.post("/add-card")
# def add_card(
#     data: CreatePaymentMethod,
#     current_user=Depends(get_current_user)
# ):
#     users_collection = db["users"]
#     payments_collection = db["payment_methods"]

#     user = users_collection.find_one({
#         "_id": ObjectId(current_user["user_id"])
#     })

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     try:
#         payment_method = stripe.PaymentMethod.create(
#             type="card",
#             card={
#                 "number": data.card_number,
#                 "exp_month": data.exp_month,
#                 "exp_year": data.exp_year,
#                 "cvc": data.cvc
#             },
#             metadata={
#                 "user_id": str(user["_id"]),
#                 "email": user["email"]
#             }
#         )

#         stripe.PaymentMethod.attach(
#             payment_method.id,
#             customer=user["stripe_customer_id"]
#         )

#         card = payment_method.card
#         brand = card.brand if card else None
#         last4 = card.last4 if card else None

#         payments_collection.insert_one({
#             "user_id": user["_id"],
#             "stripe_payment_method_id": payment_method.id,
#             "brand": brand,
#             "last4": last4
#         })

#         return {
#             "message": "Card added successfully ✅",
#             "payment_method_id": payment_method.id,
#             "brand": brand,
#             "last4": last4
#         }

#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException
from app.database import db
from app.schemas.payment import ChargeRequest, CreatePaymentMethod
from app.utils.auth import get_current_user
from app.utils.stripe_client import stripe
from bson import ObjectId

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

@router.post("/add-card")
def add_card(
    data: CreatePaymentMethod,
    current_user=Depends(get_current_user)
):
    users_collection = db["users"]
    payments_collection = db["payment_methods"]

    user = users_collection.find_one({
        "_id": ObjectId(current_user["user_id"])
    })

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # ✅ Stripe test token use karo (tok_visa)
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={
                "token": data.token
            },
            metadata={
                "user_id": str(user["_id"]),
                "email": user["email"]
            }
        )

        # ✅ Customer ke sath attach
        stripe.PaymentMethod.attach(
            payment_method.id,
            customer=user["stripe_customer_id"]
        )

        card = payment_method.card

        payments_collection.insert_one({
            "user_id": user["_id"],
            "stripe_payment_method_id": payment_method.id,
            "brand": card.brand, # type: ignore
            "last4": card.last4 # type: ignore
        })

        return {
            "message": "Card added successfully ✅",
            "payment_method_id": payment_method.id,
            "brand": card.brand, # type: ignore
            "last4": card.last4 # type: ignore
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.post("/charge")
def charge_user(
    data: ChargeRequest,
    current_user=Depends(get_current_user)
):
    users_collection = db["users"]
    payments_collection = db["payment_methods"]

    user = users_collection.find_one({
        "_id": ObjectId(current_user["user_id"])
    })

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # user ka saved card lo
    payment_method = payments_collection.find_one({
        "user_id": user["_id"]
    })

    if not payment_method:
        raise HTTPException(
            status_code=400,
            detail="No card found for this user"
        )

    try:
        intent = stripe.PaymentIntent.create(
            amount=data.amount,
            currency=data.currency,
            customer=user["stripe_customer_id"],
            payment_method=payment_method["stripe_payment_method_id"],
            off_session=True,
            confirm=True,
            metadata={
                "user_id": str(user["_id"]),
                "email": user["email"]
            }
        )

        return {
            "message": "Payment successful ✅",
            "payment_intent_id": intent.id,
            "status": intent.status
        }

    except stripe.error.CardError as e: # type: ignore
        raise HTTPException(status_code=400, detail=e.user_message)
