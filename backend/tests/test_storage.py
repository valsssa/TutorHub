"""Tests for core storage image processing."""

from io import BytesIO

from PIL import Image

from core import storage


def _make_image_bytes(size: tuple[int, int], *, format: str = "PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color=(25, 50, 75)).save(buffer, format=format)
    return buffer.getvalue()


def test_process_image_upscales_small_assets():
    """Images smaller than the minimum dimension should be upscaled automatically."""
    original = _make_image_bytes((120, 200))
    processed, content_type, extension = storage._process_image(original, original_content_type="image/png")

    with Image.open(BytesIO(processed)) as image:
        width, height = image.size

    assert width >= storage.MIN_IMAGE_DIMENSION
    assert height >= storage.MIN_IMAGE_DIMENSION
    assert content_type == "image/png"
    assert extension == "png"


def test_process_image_downscales_large_assets():
    """Images exceeding the maximum dimension should be reduced while keeping aspect ratio."""
    original = _make_image_bytes((8000, 5000))
    processed, content_type, extension = storage._process_image(original, original_content_type="image/jpeg")

    with Image.open(BytesIO(processed)) as image:
        width, height = image.size

    assert width <= storage.MAX_IMAGE_DIMENSION
    assert height <= storage.MAX_IMAGE_DIMENSION
    assert content_type == "image/jpeg"
    assert extension == "jpg"
