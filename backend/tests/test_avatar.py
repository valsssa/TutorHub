"""Tests for avatar upload and management."""

from __future__ import annotations

import asyncio
from io import BytesIO
from typing import Any

import pytest
from PIL import Image

from models import User


class FakeAvatarStorage:
    """In-memory storage stub used for avatar tests."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted: set[str] = set()
        self.ttl = 300

    async def upload_file(self, key: str, file_path: str, *, content_type: str) -> None:
        data = await asyncio.to_thread(_read_bytes, file_path)
        self.objects[key] = data

    async def delete_file(self, key: str) -> None:
        self.deleted.add(key)
        self.objects.pop(key, None)

    async def generate_presigned_url(self, key: str) -> str:
        if key not in self.objects:
            raise AssertionError("Requested URL for missing key")
        return f"https://example.com/{key}?signature=test"

    def url_ttl(self) -> int:
        return self.ttl


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as file_obj:
        return file_obj.read()


def _create_png_bytes(size: tuple[int, int] = (256, 256), color: tuple[int, int, int] = (10, 20, 200)) -> bytes:
    image = Image.new("RGB", size, color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def fake_avatar_storage(monkeypatch) -> FakeAvatarStorage:
    from modules.users.avatar import service as avatar_service_module

    storage = FakeAvatarStorage()
    monkeypatch.setattr(avatar_service_module, "get_avatar_storage", lambda: storage)
    return storage


def test_upload_avatar_success(client, student_token, db_session, fake_avatar_storage: FakeAvatarStorage):
    image_bytes = _create_png_bytes()

    response = client.post(
        "/api/users/me/avatar",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("avatar.png", image_bytes, "image/png")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert "avatar_url" in payload and payload["avatar_url"].startswith("https://example.com/")
    assert payload["expires_at"]

    # Ensure avatar stored and metadata persisted
    db_session.expire_all()
    stored_user = db_session.query(User).filter_by(email="student@test.com").first()
    assert stored_user and stored_user.avatar_key
    assert stored_user.avatar_key in fake_avatar_storage.objects


def test_upload_avatar_rejects_large_file(client, student_token, fake_avatar_storage: FakeAvatarStorage):
    oversized_bytes = b"x" * (2_000_001)

    response = client.post(
        "/api/users/me/avatar",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("huge.png", oversized_bytes, "image/png")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Avatar exceeds 2 MB limit"


def test_upload_avatar_rejects_corrupt_image(client, student_token, fake_avatar_storage: FakeAvatarStorage):
    corrupt_bytes = b"not-an-image"

    response = client.post(
        "/api/users/me/avatar",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("broken.png", corrupt_bytes, "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] in {
        "Invalid image data",
        "Failed to process avatar",
    }


def test_delete_avatar_clears_metadata_and_storage(
    client, student_token, db_session, fake_avatar_storage: FakeAvatarStorage
):
    # Upload first
    image_bytes = _create_png_bytes()
    upload_response = client.post(
        "/api/users/me/avatar",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("avatar.png", image_bytes, "image/png")},
    )
    assert upload_response.status_code == 201

    # Delete avatar
    delete_response = client.delete(
        "/api/users/me/avatar",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["detail"] == "Avatar removed successfully"

    db_session.expire_all()
    stored_user = db_session.query(User).filter_by(email="student@test.com").first()
    assert stored_user and stored_user.avatar_key is None

    # Ensure object removed from fake storage
    assert not fake_avatar_storage.objects


def test_admin_can_update_avatar_with_audit_log(
    client,
    admin_token,
    student_user,
    db_session,
    fake_avatar_storage: FakeAvatarStorage,
    caplog,
):
    caplog.set_level("INFO", logger="audit.avatar")

    image_bytes = _create_png_bytes(color=(200, 50, 90))
    response = client.patch(
        f"/api/admin/users/{student_user.id}/avatar",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("avatar.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["avatar_url"].startswith("https://example.com/")

    db_session.expire_all()
    stored_user = db_session.get(User, student_user.id)
    assert stored_user and stored_user.avatar_key in fake_avatar_storage.objects

    audit_logs = [record for record in caplog.records if record.name == "audit.avatar"]
    assert audit_logs, "Expected audit log entry for admin avatar update"
