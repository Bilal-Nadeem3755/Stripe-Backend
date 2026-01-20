from fastapi import APIRouter, HTTPException, status
from app.database import db
from app.schemas.user import UserSignup
from app.models.user import hash_password
from app.utils.stripe_client import stripe
from app.schemas.user import UserSignup, UserLogin
from app.models.user import hash_password, verify_password
from app.utils.jwt import create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup")
def signup(user: UserSignup):
    users_collection = db["users"]

    # 1️⃣ Check email already exists
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 2️⃣ Create Stripe Customer with metadata
    stripe_customer = stripe.Customer.create(
        email=user.email,
        metadata={
            "role": "user"
        }
    )

    # 3️⃣ Hash password
    hashed_password = hash_password(user.password)

    # 4️⃣ Save user in MongoDB
    new_user = {
        "email": user.email,
        "password": hashed_password,
        "stripe_customer_id": stripe_customer.id
    }

    result = users_collection.insert_one(new_user)

    return {
        "message": "User registered successfully ✅",
        "user_id": str(result.inserted_id),
        "stripe_customer_id": stripe_customer.id
    }

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users_collection = db["users"]

    # Swagger ka "username" actually email hota hai
    email = form_data.username
    password = form_data.password

    # 1️⃣ User find karo
    db_user = users_collection.find_one({"email": email})

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 2️⃣ Password verify (Argon2)
    if not verify_password(password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 3️⃣ JWT token generate
    token = create_access_token({
        "user_id": str(db_user["_id"]),
        "email": db_user["email"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }
