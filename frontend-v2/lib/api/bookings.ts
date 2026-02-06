import { api } from './client';
import { toQueryString } from '@/lib/utils';
import type { Booking, CreateBookingInput, BookingFilters, BookingListResponse } from '@/types';

export const bookingsApi = {
  list: (filters: BookingFilters = {}) =>
    api.get<BookingListResponse>(`/bookings?${toQueryString(filters)}`),

  get: (id: number) =>
    api.get<Booking>(`/bookings/${id}`),

  create: (data: CreateBookingInput) =>
    api.post<Booking>('/bookings', data),

  cancel: (id: number, reason?: string) =>
    api.post<Booking>(`/bookings/${id}/cancel`, { reason }),

  // Tutor-only endpoint for confirming bookings
  confirm: (id: number, notes_tutor?: string) =>
    api.post<Booking>(`/tutor/bookings/${id}/confirm`, { notes_tutor }),

  // Tutor-only endpoint for declining bookings
  decline: (id: number, reason?: string) =>
    api.post<Booking>(`/tutor/bookings/${id}/decline`, { reason }),

  reschedule: (id: number, new_start_at: string) =>
    api.post<Booking>(`/bookings/${id}/reschedule`, { new_start_at }),

  // Tutor marks student as no-show
  markStudentNoShow: (id: number, notes?: string) =>
    api.post<Booking>(`/tutor/bookings/${id}/mark-no-show-student`, { notes }),

  // Student marks tutor as no-show
  markTutorNoShow: (id: number, notes?: string) =>
    api.post<Booking>(`/tutor/bookings/${id}/mark-no-show-tutor`, { notes }),

  // Open a dispute on a booking
  openDispute: (id: number, reason: string) =>
    api.post<Booking>(`/bookings/${id}/dispute`, { reason }),

  // Regenerate meeting link
  regenerateMeeting: (id: number) =>
    api.post<Booking>(`/bookings/${id}/regenerate-meeting`, {}),

  // Record joining a session
  recordJoin: (id: number, notes?: string) =>
    api.post<Booking>(`/bookings/${id}/join`, { notes }),

  getStats: () =>
    api.get<{
      upcoming: number;
      completed: number;
      total_hours: number;
    }>('/bookings/stats'),
};
