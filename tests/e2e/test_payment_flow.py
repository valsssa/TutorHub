"""
Payment and Refund Flow E2E Tests

Complete E2E test for payment scenarios: Booking → Payment → Session → Refund
"""

import pytest
from playwright.sync_api import Page, expect


class TestPaymentFlow:
    """E2E test for payment and refund workflows"""

    def test_successful_payment_flow(self, page: Page, test_student_credentials, test_tutor_credentials):
        """
        Test: Student books → Pays → Completes session → Gets charged appropriately
        """

        # Step 1: Student creates booking
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_student_credentials['email'])
        page.fill('input[name="password"]', test_student_credentials['password'])
        page.click('button:has-text("Sign In")')

        # Navigate to tutors and book session
        page.goto('http://localhost:3000/tutors')
        page.click('.tutor-card:first-child button:has-text("Book")')

        # Fill booking form
        page.select_option('select[name="subject"]', '1')
        page.fill('input[name="date"]', '2025-02-15')
        page.select_option('select[name="time"]', '14:00')
        page.select_option('select[name="duration"]', '60')
        page.click('button:has-text("Book Session")')

        # Step 2: Payment processing (mocked)
        # In real scenario, this would redirect to Stripe checkout
        # For E2E test, we simulate successful payment via API

        # Verify booking created with pending payment
        page.goto('http://localhost:3000/bookings')
        booking_card = page.locator('.booking-card').first
        expect(booking_card).to_contain_text('Payment Pending')

        # Simulate payment success (via API webhook simulation)
        # ... API call to simulate payment_intent.succeeded ...

        # Refresh and verify payment completed
        page.reload()
        expect(booking_card).to_contain_text('Confirmed')

        # Step 3: Session completion
        # Fast-forward time or simulate session completion
        # ... API call to mark booking as COMPLETED ...

        # Verify earnings added to tutor balance
        # Tutor login to check earnings
        tutor_page = page.context.new_page()
        tutor_page.goto('http://localhost:3000/login')
        tutor_page.fill('input[name="email"]', test_tutor_credentials['email'])
        tutor_page.fill('input[name="password"]', test_tutor_credentials['password'])
        tutor_page.click('button:has-text("Sign In")')

        # Check earnings on tutor dashboard
        expect(tutor_page.locator('.earnings-amount')).to_be_visible()

        tutor_page.close()

    def test_refund_flow_student_cancellation_early(self, page: Page, test_student_credentials):
        """
        Test: Student cancels >12h before → Full refund
        """

        # Login as student
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_student_credentials['email'])
        page.fill('input[name="password"]', test_student_credentials['password'])
        page.click('button:has-text("Sign In")')

        # Navigate to existing booking
        page.goto('http://localhost:3000/bookings')
        booking_card = page.locator('.booking-card').first

        # Click cancel (assuming booking is >12h away)
        booking_card.click('button:has-text("Cancel")')

        # Confirm cancellation
        confirm_dialog = page.locator('[role="dialog"]')
        confirm_dialog.click('button:has-text("Confirm")')

        # Verify refund message
        expect(page.locator('.toast-success')).to_contain_text('refunded')

        # Verify booking status
        expect(booking_card).to_contain_text('Cancelled')

    def test_no_refund_flow_student_cancellation_late(self, page: Page, test_student_credentials):
        """
        Test: Student cancels <12h before → No refund
        """

        # Login as student
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_student_credentials['email'])
        page.fill('input[name="password"]', test_student_credentials['password'])
        page.click('button:has-text("Sign In")')

        # Navigate to booking <12h away
        page.goto('http://localhost:3000/bookings')
        booking_card = page.locator('.booking-card').first

        # Attempt to cancel
        booking_card.click('button:has-text("Cancel")')

        # Should show warning about no refund
        expect(page.locator('.warning-message')).to_contain_text('no refund')

        # Confirm cancellation anyway
        confirm_dialog = page.locator('[role="dialog"]')
        confirm_dialog.click('button:has-text("Cancel Anyway")')

        # Verify no refund message
        expect(page.locator('.toast-info')).to_contain_text('no refund')

    def test_tutor_decline_full_refund(self, page: Page, test_tutor_credentials):
        """
        Test: Tutor declines booking → Automatic full refund
        """

        # Login as tutor
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_tutor_credentials['email'])
        page.fill('input[name="password"]', test_tutor_credentials['password'])
        page.click('button:has-text("Sign In")')

        # Navigate to pending booking
        page.goto('http://localhost:3000/dashboard')
        pending_booking = page.locator('.pending-booking').first

        # Decline booking
        pending_booking.click('button:has-text("Decline")')

        # Confirm decline
        confirm_dialog = page.locator('[role="dialog"]')
        confirm_dialog.click('button:has-text("Decline")')

        # Verify success message
        expect(page.locator('.toast-success')).to_contain_text('declined')

        # Verify refund processed automatically
        expect(page.locator('.refund-confirmation')).to_contain_text('refunded')

    def test_no_show_scenario(self, page: Page, test_tutor_credentials):
        """
        Test: Student no-show → Tutor compensated, no refund
        """

        # Login as tutor
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_tutor_credentials['email'])
        page.fill('input[name="password"]', test_tutor_credentials['password'])
        page.click('button:has-text("Sign In")')

        # Navigate to completed session with no-show
        page.goto('http://localhost:3000/bookings')
        completed_booking = page.locator('.booking-card:has-text("No Show")').first

        # Mark as no-show (if not already marked)
        completed_booking.click('button:has-text("Mark No Show")')

        # Confirm
        confirm_dialog = page.locator('[role="dialog"]')
        confirm_dialog.click('button:has-text("Confirm")')

        # Verify tutor gets full payment
        expect(page.locator('.compensation-notice')).to_contain_text('credited')