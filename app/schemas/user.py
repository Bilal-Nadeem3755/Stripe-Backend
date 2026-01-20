from pydantic import BaseModel, EmailStr

class UserSignup(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    stripe_customer_id: str

class UserLogin(BaseModel):
     email: EmailStr
     password: str


    
