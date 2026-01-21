"""
Tutor Availability Management E2E Tests

Complete E2E test for availability scheduling: Set Schedule → Block Time → Handle Conflicts
"""

import pytest
from playwright.sync_api import Page, expect


class TestAvailabilityManagement:
    """E2E test for tutor availability management"""

    def test_set_recurring_availability(self, page: Page, test_tutor_credentials):
        """
        Test: Tutor sets weekly recurring availability schedule
        """

        # Login as tutor
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_tutor_credentials['email'])
        page.fill('input[name="password"]', test_tutor_credentials['password'])
        page.click('button:has-text("Sign In")')

        # Navigate to availability management
        page.goto('http://localhost:3000/tutor/availability')

        # Verify calendar view loads
        expect(page.locator('.availability-calendar')).to_be_visible()

        # Set Monday availability
        page.click('button:has-text("Add Time Slot"]')
        modal = page.locator('[role="dialog"]')

        # Select Monday
        modal.select_option('select[name="day"]', 'monday')

        # Set time range
        modal.fill('input[name="startTime"]', '09:00')
        modal.fill('input[name="endTime"]', '17:00')

        # Save
        modal.click('button:has-text("Save")')

        # Verify success message
        expect(page.locator('.toast-success')).to_contain_text('Availability updated')

        # Verify Monday shows as available in calendar
        monday_slots = page.locator('.calendar-day[data-day="monday"] .time-slot.available')
        expect(monday_slots).to_have_count_greater_than(0)

        # Add Tuesday availability
        page.click('button:has-text("Add Time Slot"]')
        modal = page.locator('[role="dialog"]')

        modal.select_option('select[name="day"]', 'tuesday')
        modal.fill('input[name="startTime"]', '10:00')
        modal.fill('input[name="endTime"]', '16:00')
        modal.click('button:has-text("Save")')

        # Verify both days show availability
        expect(page.locator('.calendar-day[data-day="monday"] .time-slot.available')).to_be_visible()
        expect(page.locator('.calendar-day[data-day="tuesday"] .time-slot.available')).to_be_visible()

    def test_create_blackout_period(self, page: Page, test_tutor_credentials):
        """
        Test: Tutor blocks time for vacation/holiday
        """

        # Login as tutor
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_tutor_credentials['email'])
        page.fill('input[name="password"]', test_tutor_credentials['password'])
        page.click('button:has-text("Sign In")')

        # Navigate to availability
        page.goto('http://localhost:3000/tutor/availability')

        # Click "Block Time"
        page.click('button:has-text("Block Time"]')

        # Fill blackout form
        modal = page.locator('[role="dialog"]')
        modal.fill('input[name="startDate"]', '2025-12-20')
        modal.fill('input[name="endDate"]', '2025-12-27')
        modal.fill('input[name="reason"]', 'Holiday vacation')

        # Save blackout
        modal.click('button:has-text("Block Time")')

        # Verify success
        expect(page.locator('.toast-success')).to_contain_text('Time blocked')

        # Verify blocked period shows in calendar
        blocked_period = page.locator('.calendar-day.blocked')
        expect(blocked_period).to_be_visible()

    def test_availability_conflict_prevention(self, page: Page, test_tutor_credentials):
        """
        Test: System prevents booking conflicts with availability
        """

        # Login as tutor
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_tutor_credentials['email'])
        page.fill('input[name="password"]', test_tutor_credentials['password'])
        page.click('button:has-text("Sign In")')

        # Set availability first
        page.goto('http://localhost:3000/tutor/availability')
        page.click('button:has-text("Add Time Slot"]')

        modal = page.locator('[role="dialog"]')
        modal.select_option('select[name="day"]', 'wednesday')
        modal.fill('input[name="startTime"]', '14:00')
        modal.fill('input[name="endTime"]', '16:00')
        modal.click('button:has-text("Save")')

        # Now try to book outside availability (as student)
        # Switch to student context
        student_page = page.context.new_page()
        student_page.goto('http://localhost:3000/login')
        student_page.fill('input[name="email"]', 'student@test.com')
        student_page.fill('input[name="password"]', 'password123')
        student_page.click('button:has-text("Sign In")')

        # Navigate to tutor's profile
        student_page.goto('http://localhost:3000/tutors/1')  # Assuming tutor ID 1

        # Try to book on Wednesday at 18:00 (outside availability)
        student_page.click('button:has-text("Book Session")')
        booking_modal = student_page.locator('[role="dialog"]')

        booking_modal.select_option('select[name="subject"]', '1')
        booking_modal.fill('input[name="date"]', '2025-01-22')  # Wednesday
        booking_modal.select_option('select[name="time"]', '18:00')  # Outside availability
        booking_modal.select_option('select[name="duration"]', '60')

        # Submit booking
        booking_modal.click('button:has-text("Book Session")')

        # Should show error - time not available
        expect(student_page.locator('.error-message')).to_contain_text('not available')

        # Try to book during available time
        booking_modal.select_option('select[name="time"]', '14:00')  # During availability
        booking_modal.click('button:has-text("Book Session")')

        # Should succeed
        expect(student_page.locator('.toast-success')).to_contain_text('Booking created')

        student_page.close()

    def test_buffer_time_enforcement(self, page: Page, test_tutor_credentials):
        """
        Test: System enforces buffer time between consecutive bookings
        """

        # Login as tutor and set availability
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_tutor_credentials['email'])
        page.fill('input[name="password"]', test_tutor_credentials['password'])
        page.click('button:has-text("Sign In")')

        page.goto('http://localhost:3000/tutor/availability')
        page.click('button:has-text("Add Time Slot"]')

        modal = page.locator('[role="dialog"]')
        modal.select_option('select[name="day"]', 'friday')
        modal.fill('input[name="startTime"]', '09:00')
        modal.fill('input[name="endTime"]', '17:00')
        modal.click('button:has-text("Save")')

        # As student, book first session
        student_page = page.context.new_page()
        student_page.goto('http://localhost:3000/login')
        student_page.fill('input[name="email"]', 'student@test.com')
        student_page.fill('input[name="password"]', 'password123')
        student_page.click('button:has-text("Sign In")')

        student_page.goto('http://localhost:3000/tutors/1')
        student_page.click('button:has-text("Book Session")')

        booking_modal = student_page.locator('[role="dialog"]')
        booking_modal.select_option('select[name="subject"]', '1')
        booking_modal.fill('input[name="date"]', '2025-01-24')  # Friday
        booking_modal.select_option('select[name="time"]', '10:00')
        booking_modal.select_option('select[name="duration"]', '60')
        booking_modal.click('button:has-text("Book Session")')

        expect(student_page.locator('.toast-success')).to_contain_text('Booking created')

        # Try to book immediately after (10:00-11:00, then 11:00-12:00)
        # This should conflict due to buffer time (assuming 5-15 min buffer)
        student_page.click('button:has-text("Book Session"]')

        booking_modal = student_page.locator('[role="dialog"]')
        booking_modal.select_option('select[name="time"]', '11:00')  # Immediately after
        booking_modal.click('button:has-text("Book Session")')

        # Should show buffer time conflict error
        expect(student_page.locator('.error-message')).to_contain_text('buffer time')

        student_page.close()

    def test_timezone_handling(self, page: Page, test_tutor_credentials):
        """
        Test: Availability respects timezone differences between tutor and student
        """

        # Set tutor timezone (assume UTC-5)
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', test_tutor_credentials['email'])
        page.fill('input[name="password"]', test_tutor_credentials['password'])
        page.click('button:has-text("Sign In")')

        page.goto('http://localhost:3000/profile')
        page.click('button:has-text("Edit Profile"]')
        modal = page.locator('[role="dialog"]')
        modal.select_option('select[name="timezone"]', 'America/New_York')
        modal.click('button:has-text("Save")')

        # Set availability for 9am-5pm EST
        page.goto('http://localhost:3000/tutor/availability')
        page.click('button:has-text("Add Time Slot"]')

        modal = page.locator('[role="dialog"]')
        modal.select_option('select[name="day"]', 'thursday')
        modal.fill('input[name="startTime"]', '09:00')
        modal.fill('input[name="endTime"]', '17:00')
        modal.click('button:has-text("Save")')

        # Student in different timezone (assume UTC+0) should see correct times
        student_page = page.context.new_page()
        student_page.goto('http://localhost:3000/login')
        student_page.fill('input[name="email"]', 'student@test.com')
        student_page.fill('input[name="password"]', 'password123')
        student_page.click('button:has-text("Sign In")')

        student_page.goto('http://localhost:3000/profile')
        student_page.click('button:has-text("Edit Profile"]')
        modal = student_page.locator('[role="dialog"]')
        modal.select_option('select[name="timezone"]', 'Europe/London')
        modal.click('button:has-text("Save")')

        # View tutor availability - should show 2pm-10pm GMT (9am-5pm EST = 14:00-22:00 GMT)
        student_page.goto('http://localhost:3000/tutors/1')
        expect(student_page.locator('.available-times')).to_contain_text('14:00 - 22:00')

        student_page.close()