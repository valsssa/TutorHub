"""
Student Booking Flow E2E Tests

Complete E2E test for student booking journey: Registration → Search → Book → Review
"""

import pytest
from playwright.sync_api import Page, expect


class TestStudentBookingFlow:
    """Complete E2E test for student booking journey"""

    def test_complete_student_journey(
        self,
        page: Page,
        test_student_credentials,
        test_tutor_with_availability
    ):
        """
        Test: Student registers → Searches → Books → Attends → Reviews
        """
        # Step 1: Registration
        page.goto('http://localhost:3000/register')
        page.fill('input[name="email"]', 'newstudent@test.com')
        page.fill('input[name="password"]', 'password123')
        page.fill('input[name="confirmPassword"]', 'password123')
        page.click('text=Student')  # Role selection
        page.click('button:has-text("Sign Up")')

        # Verify redirect to login
        expect(page).to_have_url('http://localhost:3000/login')

        # Step 2: Login
        page.fill('input[name="email"]', 'newstudent@test.com')
        page.fill('input[name="password"]', 'password123')
        page.click('button:has-text("Sign In")')

        # Verify redirect to dashboard
        expect(page).to_have_url('http://localhost:3000/dashboard')
        expect(page.locator('h1')).to_contain_text('Welcome')

        # Step 3: Search for tutors
        page.click('a:has-text("Find Tutors")')
        expect(page).to_have_url('http://localhost:3000/tutors')

        # Apply filters
        page.select_option('select[name="subject"]', '1')  # Math
        page.fill('input[name="max_price"]', '75')

        # Wait for filtered results
        page.wait_for_selector('.tutor-card')

        # Verify tutor cards displayed
        tutor_cards = page.locator('.tutor-card')
        expect(tutor_cards).to_have_count_greater_than(0)

        # Step 4: View tutor profile
        tutor_cards.first.click()
        expect(page).to_have_url(r'http://localhost:3000/tutors/\d+')

        # Verify profile content
        expect(page.locator('h1')).to_be_visible()
        expect(page.locator('.hourly-rate')).to_be_visible()
        expect(page.locator('.reviews-section')).to_be_visible()

        # Step 5: Book session
        page.click('button:has-text("Book Session")')

        # Modal opens
        modal = page.locator('[role="dialog"]')
        expect(modal).to_be_visible()

        # Fill booking form
        modal.select_option('select[name="subject"]', '1')
        modal.fill('input[name="date"]', '2025-02-15')
        modal.select_option('select[name="time"]', '10:00')
        modal.select_option('select[name="duration"]', '60')
        modal.fill('textarea[name="notes"]', 'Looking forward to learning!')

        # Submit booking
        modal.click('button:has-text("Book Session")')

        # Verify success message
        expect(page.locator('.toast-success')).to_contain_text('Booking created')

        # Verify redirect to bookings page
        expect(page).to_have_url('http://localhost:3000/bookings')

        # Step 6: Verify booking appears in list
        booking_card = page.locator('.booking-card').first
        expect(booking_card).to_be_visible()
        expect(booking_card).to_contain_text('Pending')  # Status badge

        # Step 7: Send message to tutor
        booking_card.click('button:has-text("Message")')
        expect(page).to_have_url(r'http://localhost:3000/messages\?thread=\d+')

        # Send message
        page.fill('textarea[placeholder="Type a message"]', 'Hi! Excited for our session.')
        page.click('button[aria-label="Send message"]')

        # Verify message sent
        message_bubble = page.locator('.message-bubble').last
        expect(message_bubble).to_contain_text('Excited for our session')

        # Step 8: Tutor confirms booking (simulate via API)
        # ... (API call to confirm booking) ...

        # Refresh bookings page
        page.goto('http://localhost:3000/bookings')

        # Verify status changed to Confirmed
        expect(booking_card.locator('.status-badge')).to_contain_text('Confirmed')

        # Step 9: Join session (when within window)
        # ... (fast-forward time or use test booking in past) ...

        # Step 10: Submit review
        page.goto('http://localhost:3000/bookings')
        completed_booking = page.locator('.booking-card:has-text("Completed")').first
        completed_booking.click('button:has-text("Review")')

        # Review form
        expect(page).to_have_url(r'http://localhost:3000/bookings/\d+/review')

        # Select 5 stars
        page.click('.star-rating .star:nth-child(5)')

        # Write comment
        page.fill('textarea[name="comment"]', 'Excellent tutor! Very helpful.')

        # Submit
        page.click('button:has-text("Submit Review")')

        # Verify success
        expect(page.locator('.toast-success')).to_contain_text('Review submitted')

        # Verify redirect back to bookings
        expect(page).to_have_url('http://localhost:3000/bookings')

        # Verify review badge on booking
        expect(completed_booking.locator('.review-badge')).to_contain_text('Reviewed')