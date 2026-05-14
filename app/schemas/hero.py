"""
Hero Schemas — Pydantic models for request/response contracts.

Separate from the SQLModel table so that:
  - HeroCreate: controls what the client sends
  - HeroUpdate: allows partial updates
  - HeroOut:    controls what the API returns
"""

from pydantic import BaseModel, Field


class HeroCreate(BaseModel):
    """Schema for creating a new hero."""
    name: str = Field( min_length=3)
    power: str = Field(min_length=3)
    level: int = Field(default=1, ge=1, le=100)

class HeroUpdate(BaseModel):
    """Schema for partial hero updates. All fields optional."""
    name: str | None = None
    power: str | None = None
    level: int | None = None
    active: bool | None = None


class HeroOut(BaseModel):
    """Schema for hero responses."""
    id: int
    name: str
    power: str
    level : int
    active: bool
