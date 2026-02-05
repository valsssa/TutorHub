"""Avatar management package.

Provides endpoints for user avatar upload, retrieval, and deletion.
"""

from modules.users.avatar.router import router as avatar_router
from modules.users.avatar.schemas import AvatarDeleteResponse, AvatarResponse
from modules.users.avatar.service import AvatarService

__all__ = [
    "avatar_router",
    "AvatarService",
    "AvatarResponse",
    "AvatarDeleteResponse",
]
