"""
Value objects for the auth domain.

Value objects are immutable objects that represent domain concepts
with no identity. They are validated on creation and compared by value.
"""

import re
from dataclasses import dataclass
from typing import NewType

from modules.auth.domain.exceptions import PasswordTooWeakError

# Type aliases for IDs - provides type safety without runtime overhead
UserId = NewType("UserId", int)
SessionId = NewType("SessionId", int)

# Constants
EMAIL_MAX_LENGTH = 254  # RFC 5321
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"

TOKEN_MIN_LENGTH = 16
TOKEN_MAX_LENGTH = 512

ROLE_STUDENT = "student"
ROLE_TUTOR = "tutor"
ROLE_ADMIN = "admin"
ROLE_OWNER = "owner"
VALID_ROLES = frozenset({ROLE_STUDENT, ROLE_TUTOR, ROLE_ADMIN, ROLE_OWNER})


@dataclass(frozen=True)
class Email:
    """
    Validated email address value object.

    Ensures email is properly formatted and normalized (lowercase).

    Attributes:
        value: The normalized email address
    """

    value: str

    def __post_init__(self) -> None:
        """Validate and normalize email on creation."""
        if not self.value:
            raise ValueError("Email cannot be empty")

        normalized = self.value.strip().lower()

        if len(normalized) > EMAIL_MAX_LENGTH:
            raise ValueError(
                f"Email exceeds maximum length of {EMAIL_MAX_LENGTH} characters"
            )

        if not EMAIL_PATTERN.match(normalized):
            raise ValueError(f"Invalid email format: {self.value}")

        # Use object.__setattr__ because dataclass is frozen
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def domain(self) -> str:
        """Extract the domain part of the email."""
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """Extract the local part (before @) of the email."""
        return self.value.split("@")[0]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if an email is valid without raising."""
        if not value or len(value) > EMAIL_MAX_LENGTH:
            return False
        return bool(EMAIL_PATTERN.match(value.strip().lower()))


@dataclass(frozen=True)
class PlainPassword:
    """
    Validated plaintext password value object.

    Validates password strength requirements:
    - Length: 8-128 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Note: This should never be persisted. Use only for validation
    before hashing.

    Attributes:
        value: The plaintext password (validated)
    """

    value: str

    def __post_init__(self) -> None:
        """Validate password strength on creation."""
        requirements: list[str] = []

        if len(self.value) < PASSWORD_MIN_LENGTH:
            requirements.append(f"at least {PASSWORD_MIN_LENGTH} characters")
        if len(self.value) > PASSWORD_MAX_LENGTH:
            requirements.append(f"at most {PASSWORD_MAX_LENGTH} characters")
        if not any(c.isupper() for c in self.value):
            requirements.append("one uppercase letter")
        if not any(c.islower() for c in self.value):
            requirements.append("one lowercase letter")
        if not any(c.isdigit() for c in self.value):
            requirements.append("one digit")
        if not any(c in PASSWORD_SPECIAL_CHARS for c in self.value):
            requirements.append("one special character")

        if requirements:
            raise PasswordTooWeakError(requirements)

    def __str__(self) -> str:
        """Return masked representation for safety."""
        return "***REDACTED***"

    def __repr__(self) -> str:
        """Return masked representation for safety."""
        return "PlainPassword(***REDACTED***)"

    @classmethod
    def check_strength(cls, password: str) -> list[str]:
        """
        Check password strength and return list of unmet requirements.

        Returns:
            Empty list if password meets all requirements,
            otherwise list of requirement descriptions.
        """
        requirements: list[str] = []

        if len(password) < PASSWORD_MIN_LENGTH:
            requirements.append(f"at least {PASSWORD_MIN_LENGTH} characters")
        if len(password) > PASSWORD_MAX_LENGTH:
            requirements.append(f"at most {PASSWORD_MAX_LENGTH} characters")
        if not any(c.isupper() for c in password):
            requirements.append("one uppercase letter")
        if not any(c.islower() for c in password):
            requirements.append("one lowercase letter")
        if not any(c.isdigit() for c in password):
            requirements.append("one digit")
        if not any(c in PASSWORD_SPECIAL_CHARS for c in password):
            requirements.append("one special character")

        return requirements

    @classmethod
    def is_valid(cls, password: str) -> bool:
        """Check if a password meets all requirements without raising."""
        return len(cls.check_strength(password)) == 0


@dataclass(frozen=True)
class HashedPassword:
    """
    Value object representing a hashed password.

    This wraps a password hash string with type safety.
    The hash should be created using bcrypt or similar secure algorithm.

    Attributes:
        value: The password hash string
    """

    value: str

    def __post_init__(self) -> None:
        """Validate that hash is not empty."""
        if not self.value:
            raise ValueError("Password hash cannot be empty")
        if not self.value.startswith("$2"):
            # Basic bcrypt format check
            raise ValueError("Invalid password hash format")

    def __str__(self) -> str:
        """Return masked representation for safety."""
        return "***HASH***"

    def __repr__(self) -> str:
        """Return masked representation for safety."""
        return "HashedPassword(***HASH***)"


@dataclass(frozen=True)
class Token:
    """
    Validated token value object.

    Used for JWT access tokens, refresh tokens, reset tokens, etc.

    Attributes:
        value: The token string
        token_type: Type of token (access, refresh, reset, verification)
    """

    value: str
    token_type: str = "access"

    def __post_init__(self) -> None:
        """Validate token on creation."""
        if not self.value:
            raise ValueError("Token cannot be empty")

        if len(self.value) < TOKEN_MIN_LENGTH:
            raise ValueError(f"Token too short (min {TOKEN_MIN_LENGTH} characters)")

        if len(self.value) > TOKEN_MAX_LENGTH:
            raise ValueError(f"Token too long (max {TOKEN_MAX_LENGTH} characters)")

        valid_types = {"access", "refresh", "reset", "verification", "email_verify"}
        if self.token_type not in valid_types:
            raise ValueError(f"Invalid token type: {self.token_type}")

    def __str__(self) -> str:
        """Return masked representation for security."""
        if len(self.value) <= 8:
            return "***"
        return f"{self.value[:4]}...{self.value[-4:]}"

    def __repr__(self) -> str:
        """Return masked representation for security."""
        return f"Token({self.token_type}={self})"


@dataclass(frozen=True)
class UserRole:
    """
    Validated user role value object.

    Ensures role is one of the valid role types.

    Attributes:
        value: The role string (student, tutor, admin, owner)
    """

    value: str

    def __post_init__(self) -> None:
        """Validate role on creation."""
        if not self.value:
            raise ValueError("Role cannot be empty")

        normalized = self.value.lower().strip()

        if normalized not in VALID_ROLES:
            raise ValueError(
                f"Invalid role: {self.value}. Must be one of: {', '.join(VALID_ROLES)}"
            )

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def is_student(self) -> bool:
        """Check if role is student."""
        return self.value == ROLE_STUDENT

    @property
    def is_tutor(self) -> bool:
        """Check if role is tutor."""
        return self.value == ROLE_TUTOR

    @property
    def is_admin(self) -> bool:
        """Check if role is admin."""
        return self.value == ROLE_ADMIN

    @property
    def is_owner(self) -> bool:
        """Check if role is owner."""
        return self.value == ROLE_OWNER

    @property
    def can_access_admin_panel(self) -> bool:
        """Check if role has admin panel access."""
        return self.value in {ROLE_ADMIN, ROLE_OWNER}

    @classmethod
    def student(cls) -> "UserRole":
        """Create a student role."""
        return cls(ROLE_STUDENT)

    @classmethod
    def tutor(cls) -> "UserRole":
        """Create a tutor role."""
        return cls(ROLE_TUTOR)

    @classmethod
    def admin(cls) -> "UserRole":
        """Create an admin role."""
        return cls(ROLE_ADMIN)

    @classmethod
    def owner(cls) -> "UserRole":
        """Create an owner role."""
        return cls(ROLE_OWNER)

    @classmethod
    def is_valid(cls, role: str) -> bool:
        """Check if a role string is valid without raising."""
        return role.lower().strip() in VALID_ROLES


@dataclass(frozen=True)
class IpAddress:
    """
    Validated IP address value object.

    Supports both IPv4 and IPv6 addresses.

    Attributes:
        value: The IP address string
    """

    value: str

    # IPv4 pattern
    IPV4_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    # Simplified IPv6 pattern (allows common formats)
    IPV6_PATTERN = re.compile(r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$")

    def __post_init__(self) -> None:
        """Validate IP address on creation."""
        if not self.value:
            raise ValueError("IP address cannot be empty")

        normalized = self.value.strip().lower()

        # Allow "unknown" as a special value
        if normalized == "unknown":
            object.__setattr__(self, "value", normalized)
            return

        # Check IPv4
        if self.IPV4_PATTERN.match(normalized):
            object.__setattr__(self, "value", normalized)
            return

        # Check IPv6
        if self.IPV6_PATTERN.match(normalized) or "::" in normalized:
            object.__setattr__(self, "value", normalized)
            return

        raise ValueError(f"Invalid IP address format: {self.value}")

    def __str__(self) -> str:
        return self.value

    @property
    def is_unknown(self) -> bool:
        """Check if IP address is unknown."""
        return self.value == "unknown"

    @property
    def is_ipv4(self) -> bool:
        """Check if this is an IPv4 address."""
        return bool(self.IPV4_PATTERN.match(self.value))

    @property
    def is_ipv6(self) -> bool:
        """Check if this is an IPv6 address."""
        return not self.is_ipv4 and not self.is_unknown

    @property
    def is_localhost(self) -> bool:
        """Check if this is a localhost address."""
        return self.value in {"127.0.0.1", "::1", "localhost"}

    @classmethod
    def unknown(cls) -> "IpAddress":
        """Create an unknown IP address placeholder."""
        return cls("unknown")

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if an IP address is valid without raising."""
        if not value:
            return False
        normalized = value.strip().lower()
        return (
            normalized == "unknown"
            or bool(cls.IPV4_PATTERN.match(normalized))
            or bool(cls.IPV6_PATTERN.match(normalized))
            or "::" in normalized
        )
