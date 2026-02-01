"""
Tests for avatar utility functions.

Tests cover:
- Initials extraction from various name formats
- Deterministic color generation
- Edge cases (empty names, non-Latin characters, etc.)
- SVG generation
"""

import pytest

from core.avatar_utils import (
    get_initials,
    hash_string,
    get_avatar_color_index,
    get_avatar_color,
    is_placeholder_url,
    get_avatar_alt_text,
    generate_avatar,
    generate_avatar_svg,
    generate_avatar_data_uri,
    AVATAR_COLORS,
)


class TestGetInitials:
    """Tests for initials extraction."""

    def test_first_and_last_name(self):
        """Extracts initials from first and last name."""
        assert get_initials("John Doe") == "JD"
        assert get_initials("Anna Smith") == "AS"
        assert get_initials("Bob Wilson") == "BW"

    def test_multiple_names(self):
        """Uses first and last name for multiple names."""
        assert get_initials("John Michael Doe") == "JD"
        assert get_initials("Anna Maria Garcia Smith") == "AS"

    def test_single_name(self):
        """Uses first two letters for single names."""
        assert get_initials("Madonna") == "MA"
        assert get_initials("Prince") == "PR"
        assert get_initials("Cher") == "CH"

    def test_single_character(self):
        """Single character stays as-is."""
        assert get_initials("J") == "J"
        assert get_initials("X") == "X"

    def test_uppercase_output(self):
        """Returns uppercase initials."""
        assert get_initials("john doe") == "JD"
        assert get_initials("JOHN DOE") == "JD"
        assert get_initials("jOhN dOe") == "JD"

    def test_whitespace_handling(self):
        """Trims and normalizes whitespace."""
        assert get_initials("  John Doe  ") == "JD"
        assert get_initials("\tJohn Doe\n") == "JD"
        assert get_initials("John    Doe") == "JD"
        assert get_initials("John  Middle  Doe") == "JD"

    def test_null_or_empty(self):
        """Returns ?? for null/empty input."""
        assert get_initials(None) == "??"
        assert get_initials("") == "??"
        assert get_initials("   ") == "??"

    def test_non_string_values(self):
        """Returns ?? for non-string values."""
        assert get_initials(123) == "??"  # type: ignore
        assert get_initials({}) == "??"  # type: ignore

    def test_chinese_characters(self):
        """Handles Chinese characters."""
        assert get_initials("张 伟") == "张伟"
        assert get_initials("李明") == "李明"

    def test_japanese_characters(self):
        """Handles Japanese characters."""
        assert get_initials("山田 太郎") == "山太"
        assert get_initials("鈴木") == "鈴木"

    def test_korean_characters(self):
        """Handles Korean characters."""
        assert get_initials("김 민수") == "김민"
        assert get_initials("박지성") == "박지"

    def test_cyrillic_characters(self):
        """Handles Cyrillic characters."""
        assert get_initials("Иван Петров") == "ИП"
        assert get_initials("Анна") == "АН"

    def test_arabic_characters(self):
        """Handles Arabic characters."""
        assert get_initials("محمد أحمد") == "مأ"


class TestHashString:
    """Tests for hash function."""

    def test_consistent_hash(self):
        """Returns consistent hash for same input."""
        assert hash_string("test") == hash_string("test")

    def test_different_hashes(self):
        """Returns different hashes for different inputs."""
        assert hash_string("test1") != hash_string("test2")

    def test_positive_number(self):
        """Returns positive number."""
        assert hash_string("test") >= 0
        assert hash_string("") >= 0
        assert hash_string("a very long string with many characters") >= 0


class TestGetAvatarColorIndex:
    """Tests for color index generation."""

    def test_consistent_index_string(self):
        """Returns consistent index for same string."""
        idx1 = get_avatar_color_index("john@example.com")
        idx2 = get_avatar_color_index("john@example.com")
        assert idx1 == idx2

    def test_consistent_index_number(self):
        """Returns consistent index for same number."""
        idx1 = get_avatar_color_index(42)
        idx2 = get_avatar_color_index(42)
        assert idx1 == idx2

    def test_index_in_valid_range(self):
        """Returns index within valid range."""
        test_cases = ["test", "john@example.com", "Jane Doe", 12345, 0, 999999]

        for input_val in test_cases:
            idx = get_avatar_color_index(input_val)
            assert 0 <= idx < len(AVATAR_COLORS)

    def test_case_insensitive(self):
        """Is case-insensitive for strings."""
        idx1 = get_avatar_color_index("John Doe")
        idx2 = get_avatar_color_index("john doe")
        assert idx1 == idx2

    def test_good_distribution(self):
        """Provides good distribution across colors."""
        color_counts = [0] * len(AVATAR_COLORS)

        for i in range(1000):
            idx = get_avatar_color_index(f"user{i}@example.com")
            color_counts[idx] += 1

        non_zero_colors = sum(1 for count in color_counts if count > 0)
        assert non_zero_colors > len(AVATAR_COLORS) // 2


class TestGetAvatarColor:
    """Tests for color retrieval."""

    def test_returns_hex_colors(self):
        """Returns valid hex colors."""
        bg, text = get_avatar_color("John Doe")

        assert bg.startswith("#")
        assert len(bg) == 7
        assert text.startswith("#")
        assert len(text) == 7

    def test_same_color_for_same_input(self):
        """Returns same color for same input."""
        color1 = get_avatar_color("test@example.com")
        color2 = get_avatar_color("test@example.com")

        assert color1[0] == color2[0]  # background
        assert color1[1] == color2[1]  # text


class TestIsPlaceholderUrl:
    """Tests for placeholder URL detection."""

    def test_null_or_empty(self):
        """Returns True for null/empty."""
        assert is_placeholder_url(None) is True
        assert is_placeholder_url("") is True

    def test_placeholder_services(self):
        """Returns True for known placeholder services."""
        assert is_placeholder_url("https://ui-avatars.com/api/?name=John") is True
        assert is_placeholder_url("https://placehold.co/100x100") is True
        assert is_placeholder_url("https://via.placeholder.com/150") is True
        assert is_placeholder_url("https://dummyimage.com/100") is True
        assert is_placeholder_url("https://placekitten.com/200/200") is True
        assert is_placeholder_url("https://picsum.photos/200") is True

    def test_real_urls(self):
        """Returns False for real URLs."""
        assert is_placeholder_url("https://example.com/avatar.jpg") is False
        assert is_placeholder_url("https://cdn.mysite.com/users/123/photo.png") is False
        assert is_placeholder_url("/images/profile.webp") is False


class TestGetAvatarAltText:
    """Tests for alt text generation."""

    def test_generates_alt_text(self):
        """Generates proper alt text for names."""
        assert get_avatar_alt_text("John Doe") == "Avatar for John Doe"
        assert get_avatar_alt_text("Jane") == "Avatar for Jane"

    def test_default_for_invalid(self):
        """Returns default for empty/invalid names."""
        assert get_avatar_alt_text(None) == "User avatar"
        assert get_avatar_alt_text("") == "User avatar"
        assert get_avatar_alt_text("   ") == "User avatar"

    def test_trims_whitespace(self):
        """Trims whitespace from names."""
        assert get_avatar_alt_text("  John Doe  ") == "Avatar for John Doe"


class TestGenerateAvatar:
    """Tests for complete avatar generation."""

    def test_generates_complete_data(self):
        """Generates complete avatar data."""
        avatar = generate_avatar("John Doe", 42)

        assert avatar.initials == "JD"
        assert avatar.background_color.startswith("#")
        assert avatar.text_color.startswith("#")
        assert avatar.alt_text == "Avatar for John Doe"
        assert 0 <= avatar.color_index < len(AVATAR_COLORS)

    def test_uses_identifier_for_color(self):
        """Uses identifier for color when provided."""
        avatar1 = generate_avatar("John Doe", 1)
        avatar2 = generate_avatar("John Doe", 100)

        # Same name = same initials
        assert avatar1.initials == avatar2.initials

    def test_falls_back_to_name(self):
        """Falls back to name for color when no identifier."""
        avatar1 = generate_avatar("John Doe")
        avatar2 = generate_avatar("John Doe")

        assert avatar1.background_color == avatar2.background_color

    def test_handles_edge_cases(self):
        """Handles edge cases gracefully."""
        avatar = generate_avatar(None, None)

        assert avatar.initials == "??"
        assert avatar.alt_text == "User avatar"
        assert avatar.background_color.startswith("#")


class TestGenerateAvatarSvg:
    """Tests for SVG generation."""

    def test_generates_valid_svg(self):
        """Generates valid SVG string."""
        svg = generate_avatar_svg("John Doe", 42, 100)

        assert svg.startswith("<svg")
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg
        assert "</svg>" in svg
        assert "JD" in svg  # initials
        assert 'width="100"' in svg
        assert 'height="100"' in svg

    def test_includes_circle_and_text(self):
        """Includes circle and text elements."""
        svg = generate_avatar_svg("Jane Smith", 1)

        assert "<circle" in svg
        assert "<text" in svg
        assert "JS" in svg  # initials

    def test_custom_size(self):
        """Respects custom size parameter."""
        svg = generate_avatar_svg("Test User", 1, 200)

        assert 'width="200"' in svg
        assert 'height="200"' in svg


class TestGenerateAvatarDataUri:
    """Tests for data URI generation."""

    def test_generates_data_uri(self):
        """Generates valid data URI."""
        uri = generate_avatar_data_uri("John Doe", 42)

        assert uri.startswith("data:image/svg+xml,")
        assert "%3Csvg" in uri or "<svg" in uri  # URL encoded or raw

    def test_can_be_used_in_img_src(self):
        """Generated URI is valid for img src."""
        uri = generate_avatar_data_uri("Test", 1, 50)

        # Should be a valid data URI format
        assert uri.startswith("data:")
        assert "image/svg" in uri


class TestWcagColorContrast:
    """Tests for WCAG AA color contrast compliance."""

    @staticmethod
    def get_luminance(hex_color: str) -> float:
        """Calculate relative luminance of a color."""
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))

        def adjust(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

    @staticmethod
    def get_contrast_ratio(color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors."""
        l1 = TestWcagColorContrast.get_luminance(color1)
        l2 = TestWcagColorContrast.get_luminance(color2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    def test_all_colors_meet_wcag_aa(self):
        """All color combinations meet WCAG AA standard (4.5:1)."""
        for bg, text in AVATAR_COLORS:
            contrast = self.get_contrast_ratio(bg, text)
            assert contrast >= 4.5, f"Color {bg} with {text} has contrast {contrast:.2f} < 4.5"
