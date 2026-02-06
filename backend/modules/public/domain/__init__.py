"""
Public module domain layer.

Contains domain entities, value objects, exceptions, and repository protocols
for the public API functionality (tutor search, public profiles, etc.).
"""

from modules.public.domain.entities import (
    PublicTutorProfileEntity,
    SearchResultEntity,
    SubjectInfo,
)
from modules.public.domain.exceptions import (
    InvalidSearchParametersError,
    PublicApiError,
    RateLimitExceededError,
    TutorProfileNotPublicError,
)
from modules.public.domain.repositories import PublicTutorRepository
from modules.public.domain.value_objects import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_QUERY_LENGTH,
    MIN_PAGE,
    MIN_PAGE_SIZE,
    PaginationParams,
    SearchFilters,
    SearchQuery,
    SortOrder,
)

__all__ = [
    # Entities
    "PublicTutorProfileEntity",
    "SearchResultEntity",
    "SubjectInfo",
    # Exceptions
    "PublicApiError",
    "TutorProfileNotPublicError",
    "InvalidSearchParametersError",
    "RateLimitExceededError",
    # Value Objects
    "SearchQuery",
    "SearchFilters",
    "PaginationParams",
    "SortOrder",
    # Constants
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "MAX_QUERY_LENGTH",
    "MIN_PAGE",
    "MIN_PAGE_SIZE",
    # Repository Protocol
    "PublicTutorRepository",
]
