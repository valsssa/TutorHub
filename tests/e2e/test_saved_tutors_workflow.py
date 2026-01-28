"""E2E tests for saved tutors workflow."""

import pytest
from playwright.sync_api import Page, expect


def test_saved_tutors_workflow(page: Page, test_user_credentials: dict):
    """Test the complete saved tutors workflow from saving to viewing."""
    # Login as student
    page.goto("http://localhost:3000/login")

    page.fill('input[type="email"]', test_user_credentials["student"]["email"])
    page.fill('input[type="password"]', test_user_credentials["student"]["password"])
    page.click('button[type="submit"]')

    # Wait for redirect to dashboard
    page.wait_for_url("http://localhost:3000/dashboard")

    # Navigate to tutors page
    page.goto("http://localhost:3000/tutors")

    # Wait for tutors to load
    page.wait_for_selector('[data-testid="tutor-card"]')

    # Get the first tutor card
    tutor_cards = page.query_selector_all('[data-testid="tutor-card"]')
    assert len(tutor_cards) > 0, "Should have at least one tutor"

    first_tutor = tutor_cards[0]

    # Get tutor ID from the card (assuming it's in a data attribute or href)
    tutor_link = first_tutor.query_selector('a')
    href = tutor_link.get_attribute('href')
    tutor_id = href.split('/')[-1]  # Extract ID from /tutors/{id}

    # Click on the tutor to view profile
    tutor_link.click()
    page.wait_for_url(f"http://localhost:3000/tutors/{tutor_id}")

    # Save the tutor (click heart icon)
    save_button = page.locator('[data-testid="save-tutor-btn"], .save-button, [aria-label*="save"]').first
    initial_state = save_button.get_attribute('aria-label') or save_button.text_content()

    # Click save button
    save_button.click()

    # Verify success message appears
    success_toast = page.locator('.toast-success, [data-testid="toast-success"]').first
    expect(success_toast).to_be_visible()

    # Navigate to saved tutors page
    page.goto("http://localhost:3000/saved-tutors")

    # Verify the saved tutor appears
    page.wait_for_selector('[data-testid="tutor-card"]')
    saved_tutors = page.query_selector_all('[data-testid="tutor-card"]')
    assert len(saved_tutors) > 0, "Should have at least one saved tutor"

    # Verify the saved tutor is the one we just saved
    saved_tutor_ids = []
    for card in saved_tutors:
        link = card.query_selector('a')
        if link:
            card_href = link.get_attribute('href')
            card_id = card_href.split('/')[-1]
            saved_tutor_ids.append(card_id)

    assert tutor_id in saved_tutor_ids, f"Saved tutor {tutor_id} should be in saved tutors list"

    # Remove from favorites
    remove_button = page.locator('[data-testid="remove-favorite-btn"], [aria-label*="remove"]').first
    remove_button.click()

    # Verify success message
    remove_toast = page.locator('.toast-success, [data-testid="toast-success"]').last
    expect(remove_toast).to_be_visible()

    # Refresh saved tutors page
    page.reload()
    page.wait_for_load_state('networkidle')

    # Verify tutor is no longer in saved list
    remaining_tutors = page.query_selector_all('[data-testid="tutor-card"]')

    # Check that the removed tutor is not in the list anymore
    remaining_ids = []
    for card in remaining_tutors:
        link = card.query_selector('a')
        if link:
            card_href = link.get_attribute('href')
            card_id = card_href.split('/')[-1]
            remaining_ids.append(card_id)

    assert tutor_id not in remaining_ids, f"Removed tutor {tutor_id} should not be in saved tutors list"


def test_saved_tutors_empty_state(page: Page, test_user_credentials: dict):
    """Test empty state when no tutors are saved."""
    # Login as student
    page.goto("http://localhost:3000/login")

    page.fill('input[type="email"]', test_user_credentials["student"]["email"])
    page.fill('input[type="password"]', test_user_credentials["student"]["password"])
    page.click('button[type="submit"]')

    page.wait_for_url("http://localhost:3000/dashboard")

    # Navigate directly to saved tutors page
    page.goto("http://localhost:3000/saved-tutors")

    # Verify empty state is shown
    empty_title = page.locator('text=No Saved Tutors Yet').first
    expect(empty_title).to_be_visible()

    empty_description = page.locator('text=Start exploring tutors and save the ones you\'re interested in').first
    expect(empty_description).to_be_visible()

    # Verify CTA buttons are present
    browse_button = page.locator('text=Browse Tutors').first
    expect(browse_button).to_be_visible()

    dashboard_button = page.locator('text=Go to Dashboard').first
    expect(dashboard_button).to_be_visible()


def test_saved_tutors_unauthenticated_access(page: Page):
    """Test that saved tutors page redirects unauthenticated users."""
    page.goto("http://localhost:3000/saved-tutors")

    # Should redirect to login
    page.wait_for_url("http://localhost:3000/login")

    # Verify we're on login page
    login_form = page.locator('form').first
    expect(login_form).to_be_visible()


def test_saved_tutors_wrong_role(page: Page, test_user_credentials: dict):
    """Test that non-student users cannot access saved tutors."""
    # Login as tutor
    page.goto("http://localhost:3000/login")

    page.fill('input[type="email"]', test_user_credentials["tutor"]["email"])
    page.fill('input[type="password"]', test_user_credentials["tutor"]["password"])
    page.click('button[type="submit"]')

    page.wait_for_url("http://localhost:3000/dashboard")

    # Try to access saved tutors page
    page.goto("http://localhost:3000/saved-tutors")

    # Should redirect or show unauthorized message
    # Note: This depends on how the frontend handles role-based access
    # The API will return 403, so frontend should handle this appropriately
    unauthorized_message = page.locator('text=Unauthorized, text=Access denied, text=403').first
    expect(unauthorized_message.or(page.locator('text=Login').first)).to_be_visible()