"""
User Schemas — Pydantic models for request/response contracts.
"""

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str
    password: str

class UserOut(BaseModel):
    """Schema for user responses (password excluded)."""
    id: int
    username: str
    is_admin: bool
