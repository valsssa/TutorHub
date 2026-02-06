import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bookingsApi } from '@/lib/api';
import { tutorKeys } from './use-tutors';
import { useAuth } from './use-auth';
import type { BookingFilters, CreateBookingInput } from '@/types';

export const bookingKeys = {
  all: ['bookings'] as const,
  lists: () => [...bookingKeys.all, 'list'] as const,
  list: (filters: BookingFilters) => [...bookingKeys.lists(), filters] as const,
  details: () => [...bookingKeys.all, 'detail'] as const,
  detail: (id: number) => [...bookingKeys.details(), id] as const,
  stats: () => [...bookingKeys.all, 'stats'] as const,
};

export function useBookings(filters: BookingFilters = {}) {
  const { user } = useAuth();
  return useQuery({
    queryKey: bookingKeys.list(filters),
    queryFn: () => bookingsApi.list(filters),
    enabled: !!user,
  });
}

export function useBooking(id: number) {
  return useQuery({
    queryKey: bookingKeys.detail(id),
    queryFn: () => bookingsApi.get(id),
    enabled: !!id,
  });
}

export function useBookingStats() {
  const { user } = useAuth();
  return useQuery({
    queryKey: bookingKeys.stats(),
    queryFn: bookingsApi.getStats,
    enabled: !!user,
  });
}

export function useCreateBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateBookingInput) => bookingsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: bookingKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tutorKeys.all });
    },
  });
}

export function useCancelBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) =>
      bookingsApi.cancel(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: bookingKeys.lists() });
      queryClient.invalidateQueries({ queryKey: bookingKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: tutorKeys.all });
    },
  });
}

export function useConfirmBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => bookingsApi.confirm(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: bookingKeys.lists() });
      queryClient.invalidateQueries({ queryKey: bookingKeys.detail(id) });
    },
  });
}

export function useDeclineBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) =>
      bookingsApi.decline(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: bookingKeys.lists() });
      queryClient.invalidateQueries({ queryKey: bookingKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: tutorKeys.all });
    },
  });
}

export function useRescheduleBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, new_start_at }: { id: number; new_start_at: string }) =>
      bookingsApi.reschedule(id, new_start_at),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: bookingKeys.lists() });
      queryClient.invalidateQueries({ queryKey: bookingKeys.detail(id) });
    },
  });
}
