"""Favorites Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from math import ceil

from pydantic import BaseModel, Field


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


class TutorSubjectSummary(BaseModel):
    """Minimal subject info for tutor summary."""

    id: int
    name: str

    class Config:
        from_attributes = True


class TutorSummary(BaseModel):
    """Summary of tutor profile for favorites listing."""

    id: int
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    title: str
    headline: str | None = None
    hourly_rate: Decimal
    average_rating: float = 0.0
    total_reviews: int = 0
    total_sessions: int = 0
    profile_photo_url: str | None = None
    subjects: list[TutorSubjectSummary] = Field(default_factory=list)

    class Config:
        from_attributes = True


class FavoriteWithTutorResponse(BaseModel):
    """Favorite response with embedded tutor profile data."""

    id: int
    student_id: int
    tutor_profile_id: int
    created_at: datetime
    tutor: TutorSummary | None = None

    class Config:
        from_attributes = True


class FavoritesCheckRequest(BaseModel):
    """Schema for batch checking favorites."""

    tutor_profile_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of tutor profile IDs to check (max 100)"
    )


class FavoritesCheckResponse(BaseModel):
    """Schema for batch favorites check response."""

    favorited_ids: list[int] = Field(
        default_factory=list,
        description="List of tutor profile IDs that are in user's favorites"
    )


class FavoriteCheckResponse(BaseModel):
    """Schema for single favorite check response."""

    is_favorited: bool = Field(..., description="Whether the tutor is in user's favorites")
    favorite: FavoriteResponse | None = Field(
        None,
        description="Favorite details if favorited, null otherwise"
    )


class PaginatedFavoritesResponse(BaseModel):
    """Paginated response for favorites list."""

    items: list[FavoriteResponse] = Field(description="List of favorites for current page")
    total: int = Field(description="Total number of favorites")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

    @classmethod
    def create(
        cls,
        items: list[FavoriteResponse],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedFavoritesResponse":
        """Create paginated response with computed metadata.

        Args:
            items: List of favorites for current page
            total: Total number of favorites
            page: Current page number
            page_size: Number of items per page

        Returns:
            PaginatedFavoritesResponse instance
        """
        total_pages = ceil(total / page_size) if page_size > 0 else 0

        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
