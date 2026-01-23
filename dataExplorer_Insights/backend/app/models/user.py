"""
User models
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class User(BaseModel):
    """User model"""
    id: int
    email: str
    is_active: bool = True
    created_at: Optional[datetime] = None


class UserCreate(BaseModel):
    """User creation model"""
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str
