"""API router for avatar management endpoints."""

import logging

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from core.rate_limiting import limiter

from sqlalchemy.orm import Session

from core.config import settings
from core.dependencies import get_current_user
from database import get_db
from models import User
from modules.users.avatar.schemas import AvatarDeleteResponse, AvatarResponse
from modules.users.avatar.service import AvatarService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


def _service(db: Session) -> AvatarService:
    return AvatarService(db=db)


@router.post("/me/avatar", response_model=AvatarResponse, status_code=201)
@limiter.limit("3/minute")
async def upload_my_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AvatarResponse:
    """Upload or replace the authenticated user's avatar."""
    service = _service(db)
    result = await service.upload_for_user(user=current_user, upload=file)
    logger.info(
        "User %s uploaded avatar",
        current_user.email,
        extra={"user_id": current_user.id},
    )
    return result


@router.get("/me/avatar", response_model=AvatarResponse)
@limiter.limit("30/minute")
async def get_my_avatar(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AvatarResponse:
    """Retrieve a signed URL for the authenticated user's avatar."""
    service = _service(db)
    result = await service.fetch_for_user(current_user)
    response.headers["Cache-Control"] = f"private, max-age={min(settings.AVATAR_STORAGE_URL_TTL_SECONDS, 300)}"
    response.headers["Pragma"] = "no-cache"
    return result


@router.delete("/me/avatar", response_model=AvatarDeleteResponse)
@limiter.limit("5/minute")
async def delete_my_avatar(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AvatarDeleteResponse:
    """Delete the authenticated user's avatar."""
    service = _service(db)
    result = await service.delete_for_user(current_user)
    logger.info(
        "User %s removed avatar",
        current_user.email,
        extra={"user_id": current_user.id},
    )
    return result
