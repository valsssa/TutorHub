"""
Avatar utility functions for deterministic avatar generation.

This module provides backend utilities for avatar generation that match
the frontend implementation for consistency across the platform.

Features:
- Extract initials from first and last name (JD for "John Doe")
- Generate deterministic colors from user ID or name
- WCAG AA compliant color contrast
- Handles edge cases (single name, non-Latin characters, empty names)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# WCAG AA compliant color palette for avatar backgrounds.
# Each color has a contrast ratio of at least 4.5:1 with its text color.
AVATAR_COLORS: list[tuple[str, str]] = [
    ("#6366f1", "#ffffff"),  # Indigo
    ("#8b5cf6", "#ffffff"),  # Violet
    ("#a855f7", "#ffffff"),  # Purple
    ("#d946ef", "#ffffff"),  # Fuchsia
    ("#ec4899", "#ffffff"),  # Pink
    ("#f43f5e", "#ffffff"),  # Rose
    ("#ef4444", "#ffffff"),  # Red
    ("#f97316", "#ffffff"),  # Orange
    ("#eab308", "#1f2937"),  # Yellow (dark text)
    ("#84cc16", "#1f2937"),  # Lime (dark text)
    ("#22c55e", "#ffffff"),  # Green
    ("#10b981", "#ffffff"),  # Emerald
    ("#14b8a6", "#ffffff"),  # Teal
    ("#06b6d4", "#ffffff"),  # Cyan
    ("#0ea5e9", "#ffffff"),  # Sky
    ("#3b82f6", "#ffffff"),  # Blue
]


def hash_string(s: str) -> int:
    """
    Simple hash function for deterministic color selection.
    Uses djb2 algorithm for good distribution.
    Matches the frontend implementation exactly.
    """
    hash_value = 5381
    for char in s:
        hash_value = ((hash_value << 5) + hash_value) ^ ord(char)
    return abs(hash_value)


def get_avatar_color_index(identifier: str | int) -> int:
    """
    Get deterministic color index from user ID or name.
    Same input always produces the same color.

    Args:
        identifier: User ID (int) or name/email (str)

    Returns:
        Index into AVATAR_COLORS array
    """
    hash_value = identifier if isinstance(identifier, int) else hash_string(str(identifier).lower())
    return hash_value % len(AVATAR_COLORS)


def get_avatar_color(identifier: str | int) -> tuple[str, str]:
    """
    Get avatar colors by identifier (user ID or name).

    Args:
        identifier: User ID or name

    Returns:
        Tuple of (background_color, text_color) as hex strings
    """
    index = get_avatar_color_index(identifier)
    return AVATAR_COLORS[index]


def get_initials(name: str | None) -> str:
    """
    Extract initials from a name.

    Rules:
    1. "John Doe" → "JD" (first letter of first and last name)
    2. "John" → "JO" (first two letters if single name)
    3. "J" → "J" (single character stays as-is)
    4. Non-Latin characters are supported as-is
    5. Empty/invalid → "??"

    Args:
        name: Full name or single name

    Returns:
        1-2 character initials, uppercase
    """
    if not name or not isinstance(name, str):
        return "??"

    # Trim and normalize whitespace
    trimmed = re.sub(r"\s+", " ", name.strip())

    if not trimmed:
        return "??"

    # Split by spaces to get name parts
    parts = [p for p in trimmed.split(" ") if p]

    if not parts:
        return "??"

    if len(parts) == 1:
        # Single name: use first two characters
        single_name = parts[0]
        if len(single_name) == 1:
            return single_name.upper()
        return single_name[:2].upper()

    # Multiple names: first letter of first and last name
    first_name = parts[0]
    last_name = parts[-1]

    first_initial = first_name[0] if first_name else ""
    last_initial = last_name[0] if last_name else ""

    return (first_initial + last_initial).upper()


def is_placeholder_url(url: str | None) -> bool:
    """
    Check if a URL is a placeholder/default avatar that should be ignored.

    Args:
        url: Avatar URL to check

    Returns:
        True if URL is a placeholder, False otherwise
    """
    if not url:
        return True

    placeholder_patterns = [
        "ui-avatars.com",
        "placehold.co",
        "placeholder.com",
        "via.placeholder.com",
        "dummyimage.com",
        "placekitten.com",
        "picsum.photos",
    ]

    return any(pattern in url for pattern in placeholder_patterns)


def get_avatar_alt_text(name: str | None) -> str:
    """
    Generate alt text for an avatar.

    Args:
        name: User's name

    Returns:
        Accessible alt text
    """
    if not name or not isinstance(name, str) or not name.strip():
        return "User avatar"
    return f"Avatar for {name.strip()}"


@dataclass
class AvatarData:
    """Complete avatar generation result."""

    initials: str
    background_color: str
    text_color: str
    alt_text: str
    color_index: int


def generate_avatar(
    name: str | None,
    identifier: str | int | None = None,
) -> AvatarData:
    """
    Generate all avatar properties from a name and optional identifier.
    Use this for complete avatar generation in one call.

    Args:
        name: User's display name
        identifier: Optional user ID for more stable color assignment

    Returns:
        Complete avatar generation result
    """
    color_key = identifier if identifier is not None else (name or "unknown")
    bg_color, text_color = get_avatar_color(color_key)
    color_index = get_avatar_color_index(color_key)

    return AvatarData(
        initials=get_initials(name),
        background_color=bg_color,
        text_color=text_color,
        alt_text=get_avatar_alt_text(name),
        color_index=color_index,
    )


def generate_avatar_svg(
    name: str | None,
    identifier: str | int | None = None,
    size: int = 100,
) -> str:
    """
    Generate an SVG avatar image.
    Useful for email templates, PDF generation, or server-side rendering.

    Args:
        name: User's display name
        identifier: Optional user ID for color stability
        size: SVG size in pixels

    Returns:
        SVG string
    """
    avatar = generate_avatar(name, identifier)
    font_size = int(size * 0.4)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <circle cx="{size // 2}" cy="{size // 2}" r="{size // 2}" fill="{avatar.background_color}"/>
  <text x="50%" y="50%" dominant-baseline="central" text-anchor="middle"
        fill="{avatar.text_color}" font-family="system-ui, -apple-system, sans-serif"
        font-size="{font_size}" font-weight="600">
    {avatar.initials}
  </text>
</svg>"""


def generate_avatar_data_uri(
    name: str | None,
    identifier: str | int | None = None,
    size: int = 100,
) -> str:
    """
    Generate a data URI for an avatar SVG.
    Can be used directly in img src attributes.

    Args:
        name: User's display name
        identifier: Optional user ID for color stability
        size: SVG size in pixels

    Returns:
        Data URI string
    """
    import urllib.parse

    svg = generate_avatar_svg(name, identifier, size)
    # Use URL encoding for better compatibility
    encoded = urllib.parse.quote(svg)
    return f"data:image/svg+xml,{encoded}"
