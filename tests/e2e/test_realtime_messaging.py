"""
Real-Time Messaging E2E Tests

Complete E2E test for WebSocket messaging: Connect → Send → Receive → Read Receipts → Edit/Delete
"""

import pytest
from playwright.sync_api import Page, expect


class TestRealtimeMessaging:
    """E2E test for real-time messaging with WebSocket"""

    def test_bidirectional_messaging_with_websocket(
        self,
        page: Page,
        context
    ):
        """
        Test: Two users send messages in real-time via WebSocket
        """

        # Open two browser pages (student and tutor)
        student_page = page
        tutor_page = context.new_page()

        # Login student
        student_page.goto('http://localhost:3000/login')
        student_page.fill('input[name="email"]', 'student@test.com')
        student_page.fill('input[name="password"]', 'password123')
        student_page.click('button:has-text("Sign In")')

        # Login tutor
        tutor_page.goto('http://localhost:3000/login')
        tutor_page.fill('input[name="email"]', 'tutor@test.com')
        tutor_page.fill('input[name="password"]', 'password123')
        tutor_page.click('button:has-text("Sign In")')

        # Student navigates to messages
        student_page.goto('http://localhost:3000/messages')
        expect(student_page.locator('.connection-status')).to_contain_text('Connected')

        # Student opens thread with tutor
        student_page.click('text=tutor@test.com')

        # Tutor navigates to messages
        tutor_page.goto('http://localhost:3000/messages')
        expect(tutor_page.locator('.connection-status')).to_contain_text('Connected')

        # Student sends message
        student_message = 'Hi, I have a question about tomorrow\'s session.'
        student_page.fill('textarea[placeholder="Type a message"]', student_message)
        student_page.click('button[aria-label="Send message"]')

        # Verify message appears in student's view
        expect(student_page.locator('.message-bubble.sent').last).to_contain_text(student_message)

        # Verify message appears in tutor's view (real-time)
        expect(tutor_page.locator('.message-bubble.received').last).to_contain_text(
            student_message,
            timeout=5000  # Wait for WebSocket delivery
        )

        # Verify unread badge appears for tutor
        expect(tutor_page.locator('.unread-badge')).to_be_visible()

        # Tutor clicks thread (marks as read)
        tutor_page.click('text=student@test.com')

        # Unread badge disappears
        expect(tutor_page.locator('.unread-badge')).not_to_be_visible()

        # Verify read receipt sent to student
        expect(student_page.locator('.message-bubble.sent').last.locator('.read-checkmark')).to_be_visible(
            timeout=3000
        )

        # Tutor sends reply
        tutor_message = 'Hi! Sure, what would you like to know?'
        tutor_page.fill('textarea', tutor_message)
        tutor_page.click('button[aria-label="Send message"]')

        # Verify reply appears in tutor's view
        expect(tutor_page.locator('.message-bubble.sent').last).to_contain_text(tutor_message)

        # Verify reply appears in student's view (real-time)
        expect(student_page.locator('.message-bubble.received').last).to_contain_text(
            tutor_message,
            timeout=5000
        )

        # Test typing indicator
        tutor_page.fill('textarea', 'I am typing...')

        # Student sees typing indicator
        expect(student_page.locator('.typing-indicator')).to_contain_text('is typing', timeout=3000)

        # Tutor stops typing (clears input)
        tutor_page.fill('textarea', '')

        # Typing indicator disappears
        expect(student_page.locator('.typing-indicator')).not_to_be_visible(timeout=4000)

        # Test message editing
        # Student edits last message
        student_last_message = student_page.locator('.message-bubble.sent').last
        student_last_message.hover()
        student_last_message.click('button[aria-label="Edit"]')

        # Edit input appears
        edit_input = student_page.locator('textarea.edit-mode')
        expect(edit_input).to_be_visible()

        # Change text
        edit_input.fill('Hi, I have a question about next week\'s session.')
        student_page.click('button:has-text("Save")')

        # Verify edited message
        expect(student_page.locator('.message-bubble.sent').last).to_contain_text('next week')
        expect(student_page.locator('.message-bubble.sent').last.locator('.edited-label')).to_be_visible()

        # Verify edit appears in tutor's view (real-time)
        expect(tutor_page.locator('.message-bubble.received').first).to_contain_text(
            'next week',
            timeout=3000
        )
        expect(tutor_page.locator('.message-bubble.received').first.locator('.edited-label')).to_be_visible()

        # Test message deletion
        # Student deletes message
        student_page.locator('.message-bubble.sent').last.hover()
        student_page.click('button[aria-label="Delete"]')

        # Confirm deletion
        student_page.click('button:has-text("Delete")')

        # Verify message replaced with "Message deleted"
        expect(student_page.locator('.message-bubble').last).to_contain_text('Message deleted')

        # Verify deletion reflected in tutor's view
        expect(tutor_page.locator('.message-bubble').last).to_contain_text(
            'Message deleted',
            timeout=3000
        )

        # Close tutor page
        tutor_page.close()

    def test_file_attachment_messaging(self, page: Page, context):
        """
        Test: Send and receive file attachments in messages
        """

        # Login users
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', 'student@test.com')
        page.fill('input[name="password"]', 'password123')
        page.click('button:has-text("Sign In")')

        tutor_page = context.new_page()
        tutor_page.goto('http://localhost:3000/login')
        tutor_page.fill('input[name="email"]', 'tutor@test.com')
        tutor_page.fill('input[name="password"]', 'password123')
        tutor_page.click('button:has-text("Sign In")')

        # Navigate to conversation
        page.goto('http://localhost:3000/messages')
        page.click('text=tutor@test.com')

        tutor_page.goto('http://localhost:3000/messages')
        tutor_page.click('text=student@test.com')

        # Student sends file attachment
        page.click('button[aria-label="Attach file"]')
        page.set_input_files('input[type="file"]', 'test_files/homework.pdf')

        # Add message text
        page.fill('textarea', 'Please review my homework')
        page.click('button[aria-label="Send message"]')

        # Verify file appears in student's view
        expect(page.locator('.file-attachment')).to_be_visible()
        expect(page.locator('.file-attachment')).to_contain_text('homework.pdf')

        # Verify file appears in tutor's view (real-time)
        expect(tutor_page.locator('.file-attachment')).to_be_visible(timeout=5000)
        expect(tutor_page.locator('.file-attachment')).to_contain_text('homework.pdf')

        # Tutor downloads file
        tutor_page.click('.file-attachment .download-button')

        # Verify download completes (check network requests)
        # ... verify download request made ...

        tutor_page.close()

    def test_message_thread_management(self, page: Page):
        """
        Test: Message thread creation, listing, and archiving
        """

        # Login
        page.goto('http://localhost:3000/login')
        page.fill('input[name="email"]', 'student@test.com')
        page.fill('input[name="password"]', 'password123')
        page.click('button:has-text("Sign In")')

        # Navigate to messages
        page.goto('http://localhost:3000/messages')

        # Verify thread list shows conversations
        thread_list = page.locator('.message-threads')
        expect(thread_list).to_be_visible()

        # Verify thread shows last message preview
        first_thread = thread_list.locator('.thread-item').first
        expect(first_thread.locator('.last-message')).to_be_visible()

        # Verify unread count badge
        unread_threads = page.locator('.thread-item .unread-count')
        if unread_threads.count() > 0:
            expect(unread_threads.first).to_contain_text(r'\d+')

        # Click on thread
        first_thread.click()

        # Verify navigation to conversation
        expect(page).to_have_url(r'http://localhost:3000/messages\?thread=\d+')

        # Verify message history loads
        expect(page.locator('.message-list')).to_be_visible()
        expect(page.locator('.message-bubble')).to_have_count_greater_than(0)