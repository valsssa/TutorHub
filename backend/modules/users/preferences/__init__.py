"""User preferences module.

Provides endpoints for user preference management (timezone, etc).
"""

from modules.users.preferences.router import router as preferences_router

__all__ = [
    "preferences_router",
]
