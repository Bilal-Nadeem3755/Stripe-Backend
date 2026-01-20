# app/schemas/payment.py
from pydantic import BaseModel

class CreatePaymentMethod(BaseModel):
    token: str   # e.g. "tok_visa"

class ChargeRequest(BaseModel):
    amount: int   # 1000 = $10.00
    currency: str = "usd"

class CreatePaymentIntent(BaseModel):
    payment_method_id: str
    amount: int  # amount in cents (e.g. 500 = Rs 500 ya $5)    