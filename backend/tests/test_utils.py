"""Tests for utilities API endpoints."""

from http import HTTPStatus

from core.constants import COUNTRIES, LANGUAGES, PHONE_COUNTRY_CODES, PROFICIENCY_LEVELS


def test_get_countries(client):
    response = client.get("/api/utils/countries")
    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert isinstance(payload, list)
    assert payload == COUNTRIES


def test_get_languages(client):
    response = client.get("/api/utils/languages")
    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert isinstance(payload, list)
    assert payload == LANGUAGES


def test_get_proficiency_levels(client):
    response = client.get("/api/utils/proficiency-levels")
    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert isinstance(payload, list)
    assert payload == PROFICIENCY_LEVELS


def test_get_phone_codes(client):
    response = client.get("/api/utils/phone-codes")
    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert isinstance(payload, list)
    assert payload == PHONE_COUNTRY_CODES
