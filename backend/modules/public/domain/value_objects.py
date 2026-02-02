"""
Value objects for public module.

Immutable objects that represent domain concepts with validation.
"""

from dataclasses import dataclass
from enum import Enum

from modules.public.domain.exceptions import InvalidSearchParametersError


class SortOrder(str, Enum):
    """Sort order options for tutor search results."""

    RELEVANCE = "RELEVANCE"  # Default sort by search relevance/score
    RATING = "RATING"  # Sort by average rating (highest first)
    PRICE_LOW = "PRICE_LOW"  # Sort by hourly rate (lowest first)
    PRICE_HIGH = "PRICE_HIGH"  # Sort by hourly rate (highest first)
    NEWEST = "NEWEST"  # Sort by profile creation date (newest first)


# Validation constants
MIN_QUERY_LENGTH = 1
MAX_QUERY_LENGTH = 200
MIN_PAGE = 1
MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20
MIN_RATING = 0.0
MAX_RATING = 5.0


@dataclass(frozen=True)
class SearchQuery:
    """
    Validated search query string.

    Immutable value object representing a sanitized search query.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate query string on creation."""
        if not isinstance(self.value, str):
            raise InvalidSearchParametersError(
                parameter="query",
                reason="Query must be a string",
            )

        # Strip whitespace
        stripped = self.value.strip()
        object.__setattr__(self, "value", stripped)

        if len(stripped) > MAX_QUERY_LENGTH:
            raise InvalidSearchParametersError(
                parameter="query",
                reason=f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters",
            )

    @property
    def is_empty(self) -> bool:
        """Check if query is empty or whitespace-only."""
        return len(self.value) == 0

    def __str__(self) -> str:
        """Return the query string."""
        return self.value


@dataclass(frozen=True)
class SearchFilters:
    """
    Validated search filters for tutor search.

    Immutable value object containing optional filter criteria.
    """

    subject_id: int | None = None
    min_rating: float | None = None
    max_price: int | None = None  # Maximum hourly rate in cents
    availability: str | None = None  # Day of week or time range

    def __post_init__(self) -> None:
        """Validate filter values on creation."""
        if self.subject_id is not None and self.subject_id <= 0:
            raise InvalidSearchParametersError(
                parameter="subject_id",
                reason="Subject ID must be a positive integer",
            )

        if self.min_rating is not None:
            if self.min_rating < MIN_RATING or self.min_rating > MAX_RATING:
                raise InvalidSearchParametersError(
                    parameter="min_rating",
                    reason=f"Rating must be between {MIN_RATING} and {MAX_RATING}",
                )

        if self.max_price is not None and self.max_price <= 0:
            raise InvalidSearchParametersError(
                parameter="max_price",
                reason="Maximum price must be a positive value",
            )

        if self.availability is not None:
            valid_days = {
                "monday", "tuesday", "wednesday", "thursday",
                "friday", "saturday", "sunday",
            }
            availability_lower = self.availability.lower()
            if availability_lower not in valid_days and not self._is_valid_time_range(
                self.availability
            ):
                raise InvalidSearchParametersError(
                    parameter="availability",
                    reason="Invalid availability format. Use day name or time range",
                )

    @staticmethod
    def _is_valid_time_range(value: str) -> bool:
        """
        Check if the value is a valid time range format.

        Accepts formats like 'morning', 'afternoon', 'evening', 'night'
        or specific hour ranges like '09:00-12:00'.
        """
        valid_periods = {"morning", "afternoon", "evening", "night"}
        if value.lower() in valid_periods:
            return True

        # Check for HH:MM-HH:MM format
        if "-" in value:
            parts = value.split("-")
            if len(parts) == 2:
                try:
                    for part in parts:
                        hours, minutes = part.strip().split(":")
                        if 0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59:
                            continue
                        return False
                    return True
                except (ValueError, AttributeError):
                    return False
        return False

    @property
    def has_filters(self) -> bool:
        """Check if any filters are set."""
        return any([
            self.subject_id is not None,
            self.min_rating is not None,
            self.max_price is not None,
            self.availability is not None,
        ])


@dataclass(frozen=True)
class PaginationParams:
    """
    Validated pagination parameters.

    Immutable value object for page and page size with limits.
    """

    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        """Validate pagination values on creation."""
        if self.page < MIN_PAGE:
            raise InvalidSearchParametersError(
                parameter="page",
                reason=f"Page must be at least {MIN_PAGE}",
            )

        if self.page_size < MIN_PAGE_SIZE:
            raise InvalidSearchParametersError(
                parameter="page_size",
                reason=f"Page size must be at least {MIN_PAGE_SIZE}",
            )

        if self.page_size > MAX_PAGE_SIZE:
            raise InvalidSearchParametersError(
                parameter="page_size",
                reason=f"Page size cannot exceed {MAX_PAGE_SIZE}",
            )

    @property
    def offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return the limit for database queries."""
        return self.page_size

    @classmethod
    def default(cls) -> "PaginationParams":
        """Create default pagination parameters."""
        return cls(page=1, page_size=DEFAULT_PAGE_SIZE)
