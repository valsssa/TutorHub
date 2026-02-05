"""User currency management module.

Provides endpoints for user currency preference management.
"""

from modules.users.currency.router import router as currency_router

__all__ = [
    "currency_router",
]
