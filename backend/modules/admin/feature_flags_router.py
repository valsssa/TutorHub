"""
Feature Flags Admin API

Endpoints for managing feature flags.

Only accessible by admin users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.dependencies import get_current_admin_user
from core.feature_flags import (
    FeatureFlag,
    FeatureState,
    feature_flags,
)
from models import User

router = APIRouter(prefix="/admin/features", tags=["admin-features"])

# Public router for checking feature flags without authentication
public_router = APIRouter(prefix="/features", tags=["features"])


# Request/Response Models


class FeatureFlagResponse(BaseModel):
    """Feature flag response."""

    name: str
    state: str
    percentage: int
    allowlist: list[str]
    denylist: list[str]
    description: str
    created_at: str | None
    updated_at: str | None

    @classmethod
    def from_flag(cls, flag: FeatureFlag) -> "FeatureFlagResponse":
        """Create response from feature flag."""
        return cls(
            name=flag.name,
            state=flag.state.value,
            percentage=flag.percentage,
            allowlist=flag.allowlist,
            denylist=flag.denylist,
            description=flag.description,
            created_at=flag.created_at.isoformat() if flag.created_at else None,
            updated_at=flag.updated_at.isoformat() if flag.updated_at else None,
        )


class CreateFeatureFlagRequest(BaseModel):
    """Request to create a feature flag."""

    name: str = Field(..., min_length=1, max_length=100)
    state: str = Field(default="disabled")
    percentage: int = Field(default=0, ge=0, le=100)
    allowlist: list[str] = Field(default_factory=list)
    denylist: list[str] = Field(default_factory=list)
    description: str = Field(default="", max_length=500)


class UpdateFeatureFlagRequest(BaseModel):
    """Request to update a feature flag."""

    state: str | None = None
    percentage: int | None = Field(default=None, ge=0, le=100)
    allowlist: list[str] | None = None
    denylist: list[str] | None = None
    description: str | None = Field(default=None, max_length=500)


class SetPercentageRequest(BaseModel):
    """Request to set percentage rollout."""

    percentage: int = Field(..., ge=0, le=100)


class ModifyListRequest(BaseModel):
    """Request to add/remove users from lists."""

    user_ids: list[str] = Field(..., min_length=1)


class CheckFeatureRequest(BaseModel):
    """Request to check feature for user."""

    user_id: str | None = None


class CheckFeatureResponse(BaseModel):
    """Response for feature check."""

    name: str
    enabled: bool
    user_id: str | None


# Endpoints


@router.get("", response_model=list[FeatureFlagResponse])
async def list_feature_flags(
    current_user: User = Depends(get_current_admin_user),
) -> list[FeatureFlagResponse]:
    """List all feature flags."""
    flags = await feature_flags.list_flags()
    return [FeatureFlagResponse.from_flag(f) for f in flags]


@router.get("/{name}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    name: str,
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlagResponse:
    """Get a specific feature flag."""
    flag = await feature_flags.get_flag(name)
    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{name}' not found",
        )
    return FeatureFlagResponse.from_flag(flag)


@router.post("", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    request: CreateFeatureFlagRequest,
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlagResponse:
    """Create a new feature flag."""
    # Check if already exists
    existing = await feature_flags.get_flag(request.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Feature flag '{request.name}' already exists",
        )

    # Validate state
    try:
        state = FeatureState(request.state)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state: {request.state}. Valid states: {[s.value for s in FeatureState]}",
        )

    flag = FeatureFlag(
        name=request.name,
        state=state,
        percentage=request.percentage,
        allowlist=request.allowlist,
        denylist=request.denylist,
        description=request.description,
    )
    await feature_flags.set_flag(flag)

    return FeatureFlagResponse.from_flag(flag)


@router.put("/{name}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    name: str,
    request: UpdateFeatureFlagRequest,
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlagResponse:
    """Update a feature flag."""
    flag = await feature_flags.get_flag(name)
    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{name}' not found",
        )

    if request.state is not None:
        try:
            flag.state = FeatureState(request.state)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state: {request.state}",
            )

    if request.percentage is not None:
        flag.percentage = request.percentage

    if request.allowlist is not None:
        flag.allowlist = request.allowlist

    if request.denylist is not None:
        flag.denylist = request.denylist

    if request.description is not None:
        flag.description = request.description

    await feature_flags.set_flag(flag)
    return FeatureFlagResponse.from_flag(flag)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature_flag(
    name: str,
    current_user: User = Depends(get_current_admin_user),
) -> None:
    """Delete a feature flag."""
    deleted = await feature_flags.delete_flag(name)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{name}' not found",
        )


@router.post("/{name}/enable", response_model=FeatureFlagResponse)
async def enable_feature_flag(
    name: str,
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlagResponse:
    """Enable a feature flag for everyone."""
    flag = await feature_flags.enable(name)
    return FeatureFlagResponse.from_flag(flag)


@router.post("/{name}/disable", response_model=FeatureFlagResponse)
async def disable_feature_flag(
    name: str,
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlagResponse:
    """Disable a feature flag for everyone."""
    flag = await feature_flags.disable(name)
    return FeatureFlagResponse.from_flag(flag)


@router.post("/{name}/percentage", response_model=FeatureFlagResponse)
async def set_feature_percentage(
    name: str,
    request: SetPercentageRequest,
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlagResponse:
    """Set feature flag to percentage rollout."""
    flag = await feature_flags.set_percentage(name, request.percentage)
    return FeatureFlagResponse.from_flag(flag)


@router.post("/{name}/allowlist/add", response_model=FeatureFlagResponse)
async def add_to_allowlist(
    name: str,
    request: ModifyListRequest,
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlagResponse:
    """Add users to feature flag allowlist."""
    flag = await feature_flags.add_to_allowlist(name, request.user_ids)
    return FeatureFlagResponse.from_flag(flag)


@router.post("/{name}/allowlist/remove", response_model=FeatureFlagResponse)
async def remove_from_allowlist(
    name: str,
    request: ModifyListRequest,
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlagResponse:
    """Remove users from feature flag allowlist."""
    try:
        flag = await feature_flags.remove_from_allowlist(name, request.user_ids)
        return FeatureFlagResponse.from_flag(flag)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{name}/denylist/add", response_model=FeatureFlagResponse)
async def add_to_denylist(
    name: str,
    request: ModifyListRequest,
    current_user: User = Depends(get_current_admin_user),
) -> FeatureFlagResponse:
    """Add users to feature flag denylist."""
    flag = await feature_flags.add_to_denylist(name, request.user_ids)
    return FeatureFlagResponse.from_flag(flag)


@router.post("/{name}/check", response_model=CheckFeatureResponse)
async def check_feature_for_user(
    name: str,
    request: CheckFeatureRequest,
    current_user: User = Depends(get_current_admin_user),
) -> CheckFeatureResponse:
    """Check if feature is enabled for a specific user."""
    if request.user_id:
        enabled = await feature_flags.is_enabled_for_user(name, request.user_id)
    else:
        enabled = await feature_flags.is_enabled(name)

    return CheckFeatureResponse(
        name=name,
        enabled=enabled,
        user_id=request.user_id,
    )


@router.post("/cache/invalidate", status_code=status.HTTP_204_NO_CONTENT)
async def invalidate_cache(
    current_user: User = Depends(get_current_admin_user),
) -> None:
    """Invalidate all feature flag caches."""
    feature_flags.invalidate_cache()


# Public endpoints for checking feature flags (no authentication required)


@public_router.get("/{name}/check", response_model=CheckFeatureResponse)
async def public_check_feature(
    name: str,
    user_id: str | None = None,
) -> CheckFeatureResponse:
    """
    Check if a feature is enabled (public endpoint).

    This endpoint can be called without authentication to check
    if a feature flag is enabled. Optionally pass a user_id for
    percentage rollouts.
    """
    if user_id:
        enabled = await feature_flags.is_enabled_for_user(name, user_id)
    else:
        enabled = await feature_flags.is_enabled(name)

    return CheckFeatureResponse(
        name=name,
        enabled=enabled,
        user_id=user_id,
    )
