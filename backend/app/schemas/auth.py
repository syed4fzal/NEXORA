"""
app/schemas/auth.py
~~~~~~~~~~~~~~~~~~~~
Pydantic schemas for authentication requests and responses.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)