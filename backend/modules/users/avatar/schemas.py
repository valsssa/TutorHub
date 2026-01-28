"""Pydantic schemas for avatar endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, HttpUrl


class AvatarResponse(BaseModel):
    """Response returned after avatar upload/fetch operations."""

    avatar_url: HttpUrl
    expires_at: datetime


class AvatarDeleteResponse(BaseModel):
    """Response returned after avatar deletion."""

    detail: str
