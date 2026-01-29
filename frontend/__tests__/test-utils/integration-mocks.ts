/**
 * Integration Test Mocks and Utilities
 *
 * Shared mock data and helper functions for integration tests.
 * These mocks simulate realistic API responses for component integration testing.
 */

import type { User, TutorProfile, Subject, BookingDTO, MessageThread, Message } from '@/types';

// ============================================================================
// User Mocks
// ============================================================================

export const mockStudentUser: User = {
  id: 1,
  email: 'student@example.com',
  role: 'student',
  is_active: true,
  is_verified: true,
  first_name: 'John',
  last_name: 'Doe',
  timezone: 'America/New_York',
  currency: 'USD',
  avatar_url: null,
  avatarUrl: null,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  country: 'US',
  bio: 'Learning enthusiast',
  learning_goal: 'Master calculus',
};

export const mockTutorUser: User = {
  id: 2,
  email: 'tutor@example.com',
  role: 'tutor',
  is_active: true,
  is_verified: true,
  first_name: 'Sarah',
  last_name: 'Johnson',
  timezone: 'America/New_York',
  currency: 'USD',
  avatar_url: 'https://example.com/avatar.jpg',
  avatarUrl: 'https://example.com/avatar.jpg',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  country: 'US',
  bio: null,
  learning_goal: null,
};

export const mockAdminUser: User = {
  id: 3,
  email: 'admin@example.com',
  role: 'admin',
  is_active: true,
  is_verified: true,
  first_name: 'Admin',
  last_name: 'User',
  timezone: 'UTC',
  currency: 'USD',
  avatar_url: null,
  avatarUrl: null,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  country: null,
  bio: null,
  learning_goal: null,
};

export const mockOwnerUser: User = {
  id: 4,
  email: 'owner@example.com',
  role: 'owner',
  is_active: true,
  is_verified: true,
  first_name: 'Platform',
  last_name: 'Owner',
  timezone: 'UTC',
  currency: 'USD',
  avatar_url: null,
  avatarUrl: null,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  country: null,
  bio: null,
  learning_goal: null,
};

// ============================================================================
// Subject Mocks
// ============================================================================

export const mockSubjects: Subject[] = [
  { id: 1, name: 'Mathematics' },
  { id: 2, name: 'Physics' },
  { id: 3, name: 'Chemistry' },
  { id: 4, name: 'English' },
  { id: 5, name: 'Computer Science' },
  { id: 6, name: 'Calculus' },
  { id: 7, name: 'Statistics' },
];

// ============================================================================
// Tutor Profile Mocks
// ============================================================================

export const mockTutorProfile: Partial<TutorProfile> = {
  id: 1,
  user_id: 2,
  title: 'Mathematics Expert',
  headline: 'PhD in Applied Mathematics',
  bio: 'Experienced tutor with 10+ years of teaching experience',
  hourly_rate: 75,
  average_rating: 4.9,
  total_reviews: 125,
  experience_years: 10,
  languages: ['English', 'Spanish'],
  status: 'approved',
  video_url: 'https://youtube.com/watch?v=example',
};

export const mockTutorsList = [
  {
    id: 1,
    name: 'Dr. Sarah Johnson',
    title: 'Mathematics Expert',
    hourly_rate: 75,
    average_rating: 4.9,
    total_reviews: 125,
    subjects: ['Mathematics', 'Calculus'],
    experience_years: 10,
    avatar_url: null,
  },
  {
    id: 2,
    name: 'Prof. Mike Chen',
    title: 'Physics Tutor',
    hourly_rate: 60,
    average_rating: 4.7,
    total_reviews: 89,
    subjects: ['Physics', 'Mathematics'],
    experience_years: 8,
    avatar_url: null,
  },
  {
    id: 3,
    name: 'Emily Parker',
    title: 'Chemistry Specialist',
    hourly_rate: 45,
    average_rating: 4.5,
    total_reviews: 45,
    subjects: ['Chemistry'],
    experience_years: 5,
    avatar_url: null,
  },
];

// ============================================================================
// Booking Mocks
// ============================================================================

export const createMockBooking = (overrides: Partial<BookingDTO> = {}): BookingDTO => ({
  id: 1,
  tutor_profile_id: 1,
  student_id: 1,
  subject_id: 1,
  start_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
  end_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString(),
  topic: 'Test Topic',
  notes: 'Test Notes',
  hourly_rate: 75,
  total_amount: 75,
  status: 'confirmed',
  meeting_url: 'https://zoom.us/j/123456789',
  pricing_option_id: null,
  pricing_type: 'hourly',
  subject_name: 'Mathematics',
  student_name: 'John Doe',
  student: {
    id: 1,
    name: 'John Doe',
    email: 'student@example.com',
  },
  tutor_earnings_cents: 6375,
  lesson_type: 'regular',
  student_timezone: 'America/New_York',
  created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

export const mockUpcomingBookings = [
  createMockBooking({
    id: 1,
    status: 'confirmed',
    start_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
  }),
  createMockBooking({
    id: 2,
    status: 'confirmed',
    start_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
    subject_name: 'Physics',
  }),
];

export const mockPendingBookings = [
  createMockBooking({
    id: 3,
    status: 'pending',
    start_at: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
  }),
];

// ============================================================================
// Message Mocks
// ============================================================================

export const mockMessageThreads: MessageThread[] = [
  {
    other_user_id: 2,
    other_user_email: 'tutor@example.com',
    booking_id: null,
    last_message: 'Looking forward to our session!',
    last_message_time: new Date(Date.now() - 3600000).toISOString(),
    unread_count: 2,
    total_messages: 15,
  },
  {
    other_user_id: 3,
    other_user_email: 'tutor2@example.com',
    booking_id: 123,
    last_message: 'Great progress today!',
    last_message_time: new Date(Date.now() - 86400000).toISOString(),
    unread_count: 0,
    total_messages: 8,
  },
];

export const mockMessages: Message[] = [
  {
    id: 1,
    sender_id: 1,
    recipient_id: 2,
    booking_id: null,
    message: 'Hi, I would like to book a session',
    is_read: true,
    created_at: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: 2,
    sender_id: 2,
    recipient_id: 1,
    booking_id: null,
    message: 'Hello! I would be happy to help.',
    is_read: true,
    created_at: new Date(Date.now() - 5400000).toISOString(),
  },
  {
    id: 3,
    sender_id: 1,
    recipient_id: 2,
    booking_id: null,
    message: 'I need help with calculus',
    is_read: false,
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
];

// ============================================================================
// Review Mocks
// ============================================================================

export const mockReviews = [
  {
    id: 1,
    reviewer_name: 'Alice Smith',
    reviewer_id: 5,
    tutor_profile_id: 1,
    booking_id: 10,
    rating: 5,
    comment: 'Excellent tutor! Helped me understand complex concepts.',
    created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 2,
    reviewer_name: 'Bob Johnson',
    reviewer_id: 6,
    tutor_profile_id: 1,
    booking_id: 11,
    rating: 4,
    comment: 'Very patient and knowledgeable.',
    created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

// ============================================================================
// Notification Mocks
// ============================================================================

export const mockNotifications = [
  {
    id: 1,
    type: 'booking_confirmed',
    title: 'Booking Confirmed',
    message: 'Your session with Dr. Sarah Johnson has been confirmed',
    is_read: false,
    created_at: new Date(Date.now() - 3600000).toISOString(),
    link: '/bookings/1',
  },
  {
    id: 2,
    type: 'new_message',
    title: 'New Message',
    message: 'You have a new message from your tutor',
    is_read: false,
    created_at: new Date(Date.now() - 7200000).toISOString(),
    link: '/messages',
  },
];

export const mockNotificationPreferences = {
  email_enabled: true,
  push_enabled: true,
  sms_enabled: false,
  session_reminders_enabled: true,
  booking_requests_enabled: true,
  learning_nudges_enabled: false,
  review_prompts_enabled: true,
  achievements_enabled: true,
  marketing_enabled: false,
  quiet_hours_start: '22:00',
  quiet_hours_end: '08:00',
  preferred_notification_time: null,
  max_daily_notifications: 10,
  max_weekly_nudges: 3,
};

// ============================================================================
// Admin Dashboard Mocks
// ============================================================================

export const mockAdminStats = {
  total_users: 1250,
  active_tutors: 45,
  sessions_today: 23,
  revenue_today: 1150.5,
  pending_tutors: 8,
  total_sessions: 15420,
  system_health: 'good',
  database_connections: 12,
  active_websockets: 45,
};

export const mockRecentActivities = [
  {
    id: 1,
    action: 'user_registered',
    description: 'New student registered',
    timestamp: new Date().toISOString(),
    user_email: 'new@example.com',
  },
  {
    id: 2,
    action: 'tutor_approved',
    description: 'Tutor profile approved',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    user_email: 'tutor@example.com',
  },
];

// ============================================================================
// Availability Mocks
// ============================================================================

export const mockAvailabilitySlots = [
  { id: 1, day_of_week: 1, start_time: '09:00', end_time: '17:00' },
  { id: 2, day_of_week: 3, start_time: '09:00', end_time: '17:00' },
  { id: 3, day_of_week: 5, start_time: '09:00', end_time: '17:00' },
];

export const mockAvailableTimeSlots = [
  { start_time: '2025-02-01T09:00:00Z', end_time: '2025-02-01T10:00:00Z', duration_minutes: 60 },
  { start_time: '2025-02-01T10:00:00Z', end_time: '2025-02-01T11:00:00Z', duration_minutes: 60 },
  { start_time: '2025-02-01T14:00:00Z', end_time: '2025-02-01T15:00:00Z', duration_minutes: 60 },
];

// ============================================================================
// Pagination Helpers
// ============================================================================

export const createPaginatedResponse = <T>(
  items: T[],
  page: number = 1,
  pageSize: number = 20,
  total?: number
) => ({
  items,
  total: total ?? items.length,
  page,
  page_size: pageSize,
  total_pages: Math.ceil((total ?? items.length) / pageSize),
});

// ============================================================================
// Test Helpers
// ============================================================================

/**
 * Creates a delayed promise for testing loading states
 */
export const delayedResponse = <T>(data: T, delayMs: number = 500): Promise<T> => {
  return new Promise((resolve) => setTimeout(() => resolve(data), delayMs));
};

/**
 * Creates a rejected promise for testing error states
 */
export const errorResponse = (
  message: string,
  status: number = 500
): Promise<never> => {
  return Promise.reject({
    response: {
      status,
      data: { detail: message },
    },
  });
};

/**
 * Mock WebSocket return value
 */
export const createMockWebSocket = (overrides = {}) => ({
  isConnected: true,
  lastMessage: null,
  sendTyping: jest.fn(),
  sendMessage: jest.fn(),
  ...overrides,
});

/**
 * Mock toast hooks
 */
export const createMockToast = () => ({
  showSuccess: jest.fn(),
  showError: jest.fn(),
  showInfo: jest.fn(),
  showWarning: jest.fn(),
});

/**
 * Mock router hooks
 */
export const createMockRouter = (overrides = {}) => ({
  push: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
  back: jest.fn(),
  ...overrides,
});
