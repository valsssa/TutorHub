"""
Admin Workflow E2E Tests

Complete E2E test for admin user management workflow: Login → Manage Users → Approve Tutors → Analytics
"""

import pytest
from playwright.sync_api import Page, expect


class TestAdminWorkflow:
    """E2E test for admin user management workflow"""

    def test_admin_user_management_workflow(self, page: Page, admin_credentials):
        """
        Test: Admin logs in → Manages users → Approves tutors → Views analytics
        """

        # Step 1: Admin Login
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', admin_credentials['email'])
        page.fill('input[name="password"]', admin_credentials['password'])
        page.click('button:has-text("Sign In")')

        # Verify redirect to admin dashboard
        expect(page).to_have_url('http://localhost:3000/admin')

        # Step 2: Admin Dashboard
        expect(page.locator('h1')).to_contain_text('Admin Dashboard')

        # Verify dashboard metrics
        expect(page.locator('.metric-total-users')).to_be_visible()
        expect(page.locator('.metric-active-tutors')).to_be_visible()
        expect(page.locator('.metric-sessions-today')).to_be_visible()
        expect(page.locator('.metric-revenue')).to_be_visible()

        # Verify recent activities
        expect(page.locator('.recent-activities')).to_be_visible()

        # Step 3: User Management
        page.click('button:has-text("User Management")')

        # Verify user table displayed
        user_table = page.locator('.user-management-table')
        expect(user_table).to_be_visible()

        # Verify table headers
        expect(page.locator('th:has-text("Email")')).to_be_visible()
        expect(page.locator('th:has-text("Role")')).to_be_visible()
        expect(page.locator('th:has-text("Status")')).to_be_visible()

        # Verify search and filters
        expect(page.locator('input[placeholder*="Search"]')).to_be_visible()
        expect(page.locator('select[name="role-filter"]')).to_be_visible()

        # Step 4: Update User Role
        # Find a student user
        student_row = page.locator('tr:has-text("student")').first
        expect(student_row).to_be_visible()

        # Click edit button
        student_row.click('button[aria-label="Edit"]')

        # Edit modal opens
        modal = page.locator('[role="dialog"]')
        expect(modal).to_be_visible()

        # Change role to tutor
        modal.select_option('select[name="role"]', 'tutor')
        modal.click('button:has-text("Save")')

        # Verify success message
        expect(page.locator('.toast-success')).to_contain_text('User updated')

        # Step 5: Deactivate User
        # Find another user to deactivate
        user_row = page.locator('tr').nth(2)  # Skip header row
        user_row.click('button[aria-label="Deactivate"]')

        # Confirm dialog
        confirm_dialog = page.locator('[role="dialog"]')
        expect(confirm_dialog).to_contain_text('deactivate')
        confirm_dialog.click('button:has-text("Confirm")')

        # Verify success
        expect(page.locator('.toast-success')).to_contain_text('User deactivated')

        # Step 6: View Pending Tutors
        page.click('button:has-text("Pending Tutors"]')

        # Verify pending tutors list
        pending_list = page.locator('.pending-tutors-list')
        expect(pending_list).to_be_visible()

        # If there are pending tutors, approve one
        pending_tutors = page.locator('.pending-tutor-card')
        if pending_tutors.count() > 0:
            # Click on first pending tutor
            pending_tutors.first.click()

            # Review modal opens
            review_modal = page.locator('[role="dialog"]')
            expect(review_modal).to_contain_text('Review Tutor')

            # Verify profile details visible
            expect(review_modal.locator('.tutor-bio')).to_be_visible()
            expect(review_modal.locator('.certifications-list')).to_be_visible()

            # Approve tutor
            review_modal.click('button:has-text("Approve")')

            # Verify success
            expect(page.locator('.toast-success')).to_contain_text('Tutor approved')

        # Step 7: View Sessions
        page.click('button:has-text("Sessions"]')

        # Verify sessions table
        sessions_table = page.locator('.sessions-table')
        expect(sessions_table).to_be_visible()

        # Verify session details
        expect(page.locator('th:has-text("Student")')).to_be_visible()
        expect(page.locator('th:has-text("Tutor")')).to_be_visible()
        expect(page.locator('th:has-text("Time")')).to_be_visible()

        # Step 8: View Analytics
        page.click('button:has-text("Analytics"]')

        # Verify revenue chart
        revenue_chart = page.locator('.revenue-chart')
        expect(revenue_chart).to_be_visible()

        # Verify subject distribution chart
        subject_chart = page.locator('.subject-distribution-chart')
        expect(subject_chart).to_be_visible()

        # Verify user growth chart
        growth_chart = page.locator('.user-growth-chart')
        expect(growth_chart).to_be_visible()

        # Step 9: Audit Log Review
        page.click('button:has-text("Audit Log"]')

        # Verify audit entries
        audit_table = page.locator('.audit-log-table')
        expect(audit_table).to_be_visible()

        # Verify audit columns
        expect(page.locator('th:has-text("Action")')).to_be_visible()
        expect(page.locator('th:has-text("User")')).to_be_visible()
        expect(page.locator('th:has-text("Timestamp")')).to_be_visible()

        # Step 10: Platform Settings
        page.click('button:has-text("Settings"]')

        # Verify settings tabs
        expect(page.locator('button:has-text("General")')).to_be_visible()
        expect(page.locator('button:has-text("Billing")')).to_be_visible()
        expect(page.locator('button:has-text("Security")')).to_be_visible()

        # Test general settings
        page.click('button:has-text("General")')
        expect(page.locator('input[name="platform-name"]')).to_be_visible()
        expect(page.locator('input[name="default-currency"]')).to_be_visible()

        # Test billing settings
        page.click('button:has-text("Billing")')
        expect(page.locator('input[name="commission-rate"]')).to_be_visible()