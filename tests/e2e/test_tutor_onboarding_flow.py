"""
Tutor Onboarding Flow E2E Tests

Complete E2E test for tutor onboarding journey: Registration → Onboarding → Approval → Accept Booking
"""

import pytest
from playwright.sync_api import Page, expect


class TestTutorOnboardingFlow:
    """Complete E2E test for tutor onboarding journey"""

    def test_tutor_onboarding_to_first_booking(
        self,
        page: Page,
        admin_credentials
    ):
        """
        Test: Tutor registers → Onboards → Waits approval → Accepts booking
        """

        # Step 1: Register as tutor
        page.goto('http://localhost:3000/register')
        page.fill('input[name="email"]', 'newtutor@test.com')
        page.fill('input[name="password"]', 'password123')
        page.fill('input[name="confirmPassword"]', 'password123')
        page.click('text=Tutor')  # Role selection
        page.click('button:has-text("Sign Up")')

        # Auto-login after registration
        expect(page).to_have_url('http://localhost:3000/tutor/onboarding')

        # Step 2: Onboarding - Personal Info
        page.fill('input[name="firstName"]', 'Alice')
        page.fill('input[name="lastName"]', 'Johnson')
        page.fill('input[name="phone"]', '+1234567890')
        page.select_option('select[name="country"]', 'US')
        page.select_option('select[name="primarySubject"]', '1')  # Math
        page.fill('textarea[name="introduction"]', 'Experienced math tutor...')
        page.click('button:has-text("Next")')

        # Step 2b: Education
        page.click('button:has-text("Add Education")')
        page.fill('input[name="degree"]', 'Bachelor of Science')
        page.fill('input[name="school"]', 'MIT')
        page.fill('input[name="field"]', 'Mathematics')
        page.fill('input[name="startYear"]', '2015')
        page.fill('input[name="endYear"]', '2019')
        page.click('button:has-text("Next")')

        # Step 2c: Certifications
        page.click('button:has-text("Add Certification")')
        page.fill('input[name="certName"]', 'Teaching Certificate')
        page.fill('input[name="organization"]', 'State Board')
        page.fill('input[name="issueDate"]', '2020-01-15')
        # Upload file
        page.set_input_files('input[type="file"]', 'test_files/certificate.pdf')
        page.click('button:has-text("Next")')

        # Step 2d: Availability
        # Set Monday availability
        page.click('input[name="monday"]')  # Enable Monday
        page.fill('input[name="mondayStart"]', '09:00')
        page.fill('input[name="mondayEnd"]', '17:00')
        # Repeat for other days...
        page.click('button:has-text("Next")')

        # Step 2e: Teaching Details
        page.fill('input[name="experienceYears"]', '5')
        page.fill('textarea[name="bio"]', 'I specialize in algebra and calculus...')
        # Select subjects
        page.click('input[value="1"]')  # Math
        page.select_option('select[name="subject1Proficiency"]', 'C2')
        page.click('button:has-text("Next")')

        # Step 2f: Languages
        page.click('button:has-text("Add Language")')
        page.select_option('select[name="language"]', 'en')
        page.select_option('select[name="proficiency"]', 'C2')
        page.click('button:has-text("Next")')

        # Step 2g: Pricing
        page.fill('input[name="hourlyRate"]', '50')
        # Add package
        page.click('button:has-text("Add Package")')
        page.fill('input[name="packageName"]', '5 sessions')
        page.fill('input[name="sessionCount"]', '5')
        page.fill('input[name="packagePrice"]', '225')
        page.click('button:has-text("Next")')

        # Step 2h: Review & Submit
        expect(page.locator('h2')).to_contain_text('Review Your Profile')
        page.click('input[name="agreeTerms"]')
        page.click('button:has-text("Submit for Approval")')

        # Verify submission success
        expect(page).to_have_url('http://localhost:3000/tutor/profile/submitted')
        expect(page.locator('.status-message')).to_contain_text('under review')

        # Step 3: Admin approves profile
        # Open new page/context for admin
        admin_page = page.context.new_page()
        admin_page.goto('http://localhost:3000/login')
        admin_page.fill('input[name="email"]', admin_credentials['email'])
        admin_page.fill('input[name="password"]', admin_credentials['password'])
        admin_page.click('button:has-text("Sign In")')

        # Navigate to admin dashboard
        expect(admin_page).to_have_url('http://localhost:3000/admin')

        # Click User Management tab
        admin_page.click('button:has-text("User Management")')

        # Find pending tutor
        pending_section = admin_page.locator('.pending-tutors-section')
        tutor_row = pending_section.locator('tr:has-text("newtutor@test.com")')
        expect(tutor_row).to_be_visible()

        # Click to view profile
        tutor_row.click()

        # Review modal opens
        modal = admin_page.locator('[role="dialog"]')
        expect(modal).to_be_visible()
        expect(modal).to_contain_text('Alice Johnson')

        # Approve tutor
        modal.click('button:has-text("Approve")')

        # Verify success
        expect(admin_page.locator('.toast-success')).to_contain_text('Tutor approved')

        # Close admin page
        admin_page.close()

        # Step 4: Tutor receives notification and accesses dashboard
        # Refresh tutor page
        page.reload()

        # Navigate to dashboard
        page.goto('http://localhost:3000/dashboard')

        # Verify tutor dashboard displayed
        expect(page.locator('h1')).to_contain_text('Tutor Dashboard')
        expect(page.locator('.earnings-summary')).to_be_visible()

        # Step 5: Receive booking request (simulate via API)
        # ... create booking via API ...

        # Reload dashboard
        page.reload()

        # Verify pending request appears
        pending_requests = page.locator('.pending-requests-section')
        expect(pending_requests.locator('.booking-card')).to_have_count(1)

        # Step 6: Approve booking
        booking_card = pending_requests.locator('.booking-card').first
        booking_card.click('button:has-text("Approve")')

        # Confirm modal
        confirm_modal = page.locator('[role="dialog"]')
        confirm_modal.click('button:has-text("Confirm")')

        # Verify success
        expect(page.locator('.toast-success')).to_contain_text('Booking confirmed')

        # Verify booking moved to upcoming
        upcoming_section = page.locator('.upcoming-sessions-section')
        expect(upcoming_section.locator('.booking-card')).to_have_count(1)