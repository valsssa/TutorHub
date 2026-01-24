"""Favorites Pydantic schemas."""

from pydantic import BaseModel, Field
from datetime import datetime


class FavoriteCreate(BaseModel):
    """Schema for creating a favorite."""
    
    tutor_profile_id: int = Field(..., gt=0, description="ID of the tutor profile to save")


class FavoriteResponse(BaseModel):
    """Schema for favorite response."""
    
    id: int
    student_id: int
    tutor_profile_id: int
    created_at: datetime

    class Config:
        from_attributes = True
