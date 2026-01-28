"""Tests for input sanitization utilities."""

import pytest

from core.sanitization import (
    clean_search_query,
    sanitize_email,
    sanitize_filename,
    sanitize_html,
    sanitize_string,
    sanitize_text_input,
    sanitize_url,
    validate_phone_number,
    validate_video_url,
)


class TestSanitizeHtml:
    """Test sanitize_html function."""

    def test_escapes_script_tags(self):
        """Test that script tags are escaped."""
        malicious = "<script>alert('xss')</script>"
        result = sanitize_html(malicious)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_escapes_angle_brackets(self):
        """Test that angle brackets are escaped."""
        text = "<div>content</div>"
        result = sanitize_html(text)
        assert "<div>" not in result
        assert "&lt;div&gt;" in result

    def test_escapes_quotes(self):
        """Test that quotes are escaped."""
        text = 'onclick="alert(1)"'
        result = sanitize_html(text)
        assert '"' not in result
        assert "&quot;" in result

    def test_escapes_ampersand(self):
        """Test that ampersands are escaped."""
        text = "a & b"
        result = sanitize_html(text)
        assert "&amp;" in result

    def test_none_input_returns_none(self):
        """Test None input returns None."""
        assert sanitize_html(None) is None

    def test_empty_string_returns_empty(self):
        """Test empty string returns empty."""
        assert sanitize_html("") == ""

    def test_preserves_safe_text(self):
        """Test that safe text is preserved."""
        safe_text = "Hello, World!"
        result = sanitize_html(safe_text)
        assert result == safe_text


class TestSanitizeFilename:
    """Test sanitize_filename function."""

    def test_removes_path_separators(self):
        """Test removal of path separators."""
        assert "/" not in sanitize_filename("path/to/file.txt")
        assert "\\" not in sanitize_filename("path\\to\\file.txt")

    def test_removes_null_bytes(self):
        """Test removal of null bytes."""
        assert "\x00" not in sanitize_filename("file\x00name.txt")

    def test_removes_leading_trailing_dots(self):
        """Test removal of leading/trailing dots."""
        assert not sanitize_filename("...file.txt").startswith(".")
        assert not sanitize_filename("file.txt...").endswith("...")

    def test_replaces_special_chars(self):
        """Test replacement of special characters."""
        result = sanitize_filename("file<>name?.txt")
        assert "<" not in result
        assert ">" not in result
        assert "?" not in result

    def test_limits_length(self):
        """Test filename length limiting."""
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_preserves_extension_on_truncate(self):
        """Test that extension is preserved when truncating."""
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)
        assert result.endswith(".pdf")

    def test_none_input_returns_none(self):
        """Test None input returns None."""
        assert sanitize_filename(None) is None

    def test_preserves_valid_filename(self):
        """Test that valid filenames are preserved."""
        valid = "my_document-v2.pdf"
        assert sanitize_filename(valid) == valid


class TestSanitizeUrl:
    """Test sanitize_url function."""

    def test_blocks_javascript_scheme(self):
        """Test blocking of javascript: scheme."""
        assert sanitize_url("javascript:alert(1)") is None

    def test_blocks_javascript_scheme_case_insensitive(self):
        """Test blocking is case insensitive."""
        assert sanitize_url("JAVASCRIPT:alert(1)") is None
        assert sanitize_url("JaVaScRiPt:alert(1)") is None

    def test_blocks_data_scheme(self):
        """Test blocking of data: scheme."""
        assert sanitize_url("data:text/html,<script>alert(1)</script>") is None

    def test_blocks_vbscript_scheme(self):
        """Test blocking of vbscript: scheme."""
        assert sanitize_url("vbscript:msgbox(1)") is None

    def test_blocks_file_scheme(self):
        """Test blocking of file: scheme."""
        assert sanitize_url("file:///etc/passwd") is None

    def test_allows_http(self):
        """Test that http:// URLs are allowed."""
        url = "http://example.com/page"
        assert sanitize_url(url) == url

    def test_allows_https(self):
        """Test that https:// URLs are allowed."""
        url = "https://example.com/page"
        assert sanitize_url(url) == url

    def test_allows_relative_urls(self):
        """Test that relative URLs starting with / are allowed."""
        url = "/path/to/page"
        assert sanitize_url(url) == url

    def test_blocks_protocol_relative_urls(self):
        """Test blocking of other schemes."""
        assert sanitize_url("ftp://example.com") is None
        assert sanitize_url("mailto:test@test.com") is None

    def test_strips_whitespace(self):
        """Test stripping of whitespace."""
        url = "  https://example.com  "
        assert sanitize_url(url) == "https://example.com"

    def test_none_input_returns_none(self):
        """Test None input returns None."""
        assert sanitize_url(None) is None


class TestSanitizeTextInput:
    """Test sanitize_text_input function."""

    def test_strips_whitespace(self):
        """Test stripping of whitespace."""
        result = sanitize_text_input("  hello  ")
        assert result == "hello"

    def test_removes_null_bytes(self):
        """Test removal of null bytes."""
        result = sanitize_text_input("hello\x00world")
        assert "\x00" not in result

    def test_removes_control_characters(self):
        """Test removal of control characters."""
        result = sanitize_text_input("hello\x01\x02world")
        assert "\x01" not in result
        assert "\x02" not in result

    def test_preserves_newline(self):
        """Test that newlines are preserved."""
        result = sanitize_text_input("hello\nworld")
        assert "\n" in result

    def test_preserves_tab(self):
        """Test that tabs are preserved."""
        result = sanitize_text_input("hello\tworld")
        assert "\t" in result

    def test_escapes_html(self):
        """Test that HTML is escaped."""
        result = sanitize_text_input("<script>alert(1)</script>")
        assert "<script>" not in result

    def test_enforces_max_length(self):
        """Test max length enforcement."""
        long_text = "a" * 1000
        result = sanitize_text_input(long_text, max_length=100)
        assert len(result) == 100

    def test_none_input_returns_none(self):
        """Test None input returns None."""
        assert sanitize_text_input(None) is None

    def test_empty_string_returns_empty(self):
        """Test empty string returns empty after strip."""
        assert sanitize_text_input("   ") == ""


class TestValidatePhoneNumber:
    """Test validate_phone_number function."""

    def test_valid_e164_format(self):
        """Test valid E.164 format."""
        assert validate_phone_number("+1234567890") is True
        assert validate_phone_number("+12345678901234") is True

    def test_strips_formatting(self):
        """Test that formatting characters are stripped."""
        assert validate_phone_number("+1 (234) 567-890") is True

    def test_requires_plus_sign(self):
        """Test that + sign is required."""
        assert validate_phone_number("1234567890") is False

    def test_minimum_length(self):
        """Test minimum length requirement."""
        assert validate_phone_number("+123456") is False  # Too short

    def test_maximum_length(self):
        """Test maximum length requirement."""
        assert validate_phone_number("+1234567890123456") is False  # Too long

    def test_country_code_matching(self):
        """Test country code matching."""
        assert validate_phone_number("+12025551234", country_code="+1") is True
        assert validate_phone_number("+44123456789", country_code="+1") is False

    def test_empty_returns_false(self):
        """Test empty string returns False."""
        assert validate_phone_number("") is False

    def test_none_returns_false(self):
        """Test None returns False."""
        assert validate_phone_number(None) is False


class TestSanitizeEmail:
    """Test sanitize_email function."""

    def test_lowercase_normalization(self):
        """Test email is lowercased."""
        result = sanitize_email("TEST@EXAMPLE.COM")
        assert result == "test@example.com"

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        result = sanitize_email("  test@example.com  ")
        assert result == "test@example.com"

    def test_requires_at_symbol(self):
        """Test that @ symbol is required."""
        assert sanitize_email("invalidemail") is None

    def test_rejects_too_long(self):
        """Test rejection of emails over 254 characters."""
        long_email = "a" * 250 + "@b.com"
        assert sanitize_email(long_email) is None

    def test_valid_email_preserved(self):
        """Test valid email is preserved."""
        email = "user@example.com"
        assert sanitize_email(email) == email

    def test_none_returns_none(self):
        """Test None returns None."""
        assert sanitize_email(None) is None


class TestCleanSearchQuery:
    """Test clean_search_query function."""

    def test_removes_sql_keywords(self):
        """Test removal of SQL keywords."""
        result = clean_search_query("SELECT * FROM users DROP TABLE")
        assert "select" not in result.lower()
        assert "drop" not in result.lower()

    def test_removes_sql_comments(self):
        """Test removal of SQL comment markers."""
        result = clean_search_query("search -- comment")
        assert "--" not in result

        result = clean_search_query("search /* comment */")
        assert "/*" not in result
        assert "*/" not in result

    def test_limits_length(self):
        """Test query length limiting."""
        long_query = "a" * 300
        result = clean_search_query(long_query)
        assert len(result) <= 200

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        result = clean_search_query("  search term  ")
        assert result == "search term"

    def test_preserves_normal_queries(self):
        """Test that normal queries are preserved."""
        query = "python programming tutorials"
        result = clean_search_query(query)
        assert "python" in result
        assert "programming" in result

    def test_none_returns_none(self):
        """Test None returns None."""
        assert clean_search_query(None) is None


class TestSanitizeString:
    """Test sanitize_string function."""

    def test_strips_whitespace(self):
        """Test whitespace stripping."""
        result = sanitize_string("  text  ")
        assert result == "text"

    def test_removes_null_bytes(self):
        """Test null byte removal."""
        result = sanitize_string("te\x00xt")
        assert "\x00" not in result

    def test_escapes_html_by_default(self):
        """Test HTML is escaped by default."""
        result = sanitize_string("<b>bold</b>")
        assert "<b>" not in result

    def test_allows_html_when_specified(self):
        """Test HTML is preserved when allow_html=True."""
        result = sanitize_string("<b>bold</b>", allow_html=True)
        assert "<b>bold</b>" in result

    def test_enforces_max_length(self):
        """Test max length enforcement."""
        result = sanitize_string("a" * 100, max_length=50)
        assert len(result) == 50

    def test_none_returns_none(self):
        """Test None returns None."""
        assert sanitize_string(None) is None


class TestValidateVideoUrl:
    """Test validate_video_url function."""

    def test_valid_youtube_url(self):
        """Test valid YouTube URLs."""
        assert validate_video_url("https://youtube.com/watch?v=abc123") is True
        assert validate_video_url("https://www.youtube.com/watch?v=abc123") is True
        assert validate_video_url("https://youtu.be/abc123") is True

    def test_valid_vimeo_url(self):
        """Test valid Vimeo URLs."""
        assert validate_video_url("https://vimeo.com/123456789") is True

    def test_valid_loom_url(self):
        """Test valid Loom URLs."""
        assert validate_video_url("https://loom.com/share/abc123") is True

    def test_valid_wistia_url(self):
        """Test valid Wistia URLs."""
        assert validate_video_url("https://wistia.com/medias/abc123") is True

    def test_valid_vidyard_url(self):
        """Test valid Vidyard URLs."""
        assert validate_video_url("https://vidyard.com/watch/abc123") is True

    def test_http_protocol(self):
        """Test http:// protocol is accepted."""
        assert validate_video_url("http://youtube.com/watch?v=abc") is True

    def test_requires_http_protocol(self):
        """Test that protocol is required."""
        assert validate_video_url("youtube.com/watch?v=abc") is False

    def test_rejects_unknown_domains(self):
        """Test rejection of unknown video domains."""
        assert validate_video_url("https://unknown.com/video") is False
        assert validate_video_url("https://example.com/video.mp4") is False

    def test_none_returns_false(self):
        """Test None returns False."""
        assert validate_video_url(None) is False

    def test_empty_returns_false(self):
        """Test empty string returns False."""
        assert validate_video_url("") is False


class TestSanitizationEdgeCases:
    """Test edge cases and security scenarios."""

    def test_nested_xss_attempt(self):
        """Test nested XSS attempts."""
        nested = "<<script>script>alert(1)<</script>/script>"
        result = sanitize_html(nested)
        assert "<script>" not in result.lower()

    def test_unicode_in_filename(self):
        """Test Unicode handling in filenames."""
        result = sanitize_filename("文件名.txt")
        assert len(result) > 0  # Should not crash
        # Non-ASCII replaced with underscores
        assert ".txt" in result

    def test_url_with_unicode(self):
        """Test URL with Unicode characters."""
        # Unicode in path should be allowed
        url = "https://example.com/путь"
        result = sanitize_url(url)
        assert result == url

    def test_very_long_input(self):
        """Test handling of very long inputs."""
        long_text = "a" * 100000
        result = sanitize_text_input(long_text, max_length=1000)
        assert len(result) == 1000

    def test_html_encoding_bypass(self):
        """Test prevention of HTML encoding bypass attempts."""
        bypass_attempts = [
            "&#60;script&#62;alert(1)&#60;/script&#62;",
            "%3Cscript%3Ealert(1)%3C/script%3E",
        ]
        for attempt in bypass_attempts:
            result = sanitize_html(attempt)
            # After sanitization, should not execute
            assert "script>" not in result.lower()
