"""
Domain entities for public module.

These are pure data classes representing the core public API domain concepts.
No SQLAlchemy or infrastructure dependencies.
"""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class SubjectInfo:
    """Minimal subject information for public display."""

    id: int
    name: str
    category: str | None = None


@dataclass
class PublicTutorProfileEntity:
    """
    Public tutor profile domain entity.

    Contains only information that should be visible to unauthenticated users.
    Sensitive information like contact details is excluded.
    """

    id: int
    user_id: int
    first_name: str
    last_name: str | None = None
    avatar_url: str | None = None
    headline: str | None = None
    bio: str | None = None
    subjects: list[SubjectInfo] = field(default_factory=list)
    average_rating: float | None = None
    total_reviews: int = 0
    completed_sessions: int = 0
    hourly_rate_cents: int | None = None
    currency: str = "USD"
    years_experience: int | None = None
    response_time_hours: int | None = None
    is_featured: bool = False

    @property
    def display_name(self) -> str:
        """Get display name for public profile."""
        if self.last_name:
            return f"{self.first_name} {self.last_name[0]}."
        return self.first_name

    @property
    def full_name(self) -> str:
        """Get full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def hourly_rate_decimal(self) -> Decimal | None:
        """Get hourly rate as decimal."""
        if self.hourly_rate_cents is None:
            return None
        return Decimal(self.hourly_rate_cents) / 100

    @property
    def has_reviews(self) -> bool:
        """Check if tutor has any reviews."""
        return self.total_reviews > 0

    @property
    def subject_names(self) -> list[str]:
        """Get list of subject names."""
        return [s.name for s in self.subjects]

    @property
    def initials(self) -> str:
        """Get tutor's initials for avatar placeholder."""
        initials = ""
        if self.first_name:
            initials += self.first_name[0].upper()
        if self.last_name:
            initials += self.last_name[0].upper()
        return initials or "T"


@dataclass
class SearchResultEntity:
    """
    Search result domain entity.

    Represents a paginated list of tutor search results.
    """

    tutors: list[PublicTutorProfileEntity]
    total_count: int
    page: int
    page_size: int

    @property
    def has_more(self) -> bool:
        """Check if there are more results beyond the current page."""
        return (self.page * self.page_size) < self.total_count

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.page_size <= 0:
            return 0
        return (self.total_count + self.page_size - 1) // self.page_size

    @property
    def is_empty(self) -> bool:
        """Check if search returned no results."""
        return len(self.tutors) == 0

    @property
    def result_count(self) -> int:
        """Get number of results in current page."""
        return len(self.tutors)

    @classmethod
    def empty(cls, page: int = 1, page_size: int = 20) -> "SearchResultEntity":
        """Create an empty search result."""
        return cls(
            tutors=[],
            total_count=0,
            page=page,
            page_size=page_size,
        )
