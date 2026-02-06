import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '@/lib/api/admin';
import type { AdminUsersFilters, AdminTutorsFilters } from '@/lib/api/admin';
import type { AdminUserUpdate, TutorRejectionInput } from '@/types/admin';

export const adminKeys = {
  all: ['admin'] as const,
  dashboardStats: () => [...adminKeys.all, 'dashboard-stats'] as const,
  recentActivities: (limit?: number) => [...adminKeys.all, 'recent-activities', limit] as const,
  sessionMetrics: () => [...adminKeys.all, 'session-metrics'] as const,
  subjectDistribution: () => [...adminKeys.all, 'subject-distribution'] as const,
  monthlyRevenue: (months?: number) => [...adminKeys.all, 'monthly-revenue', months] as const,
  userGrowth: (months?: number) => [...adminKeys.all, 'user-growth', months] as const,
  users: () => [...adminKeys.all, 'users'] as const,
  usersList: (filters: AdminUsersFilters) => [...adminKeys.users(), 'list', filters] as const,
  pendingTutors: () => [...adminKeys.all, 'pending-tutors'] as const,
  pendingTutorsList: (filters: AdminTutorsFilters) => [...adminKeys.pendingTutors(), 'list', filters] as const,
  approvedTutors: () => [...adminKeys.all, 'approved-tutors'] as const,
  approvedTutorsList: (filters: AdminTutorsFilters) => [...adminKeys.approvedTutors(), 'list', filters] as const,
};

// Dashboard hooks
export function useAdminDashboardStats() {
  return useQuery({
    queryKey: adminKeys.dashboardStats(),
    queryFn: adminApi.getDashboardStats,
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useAdminRecentActivities(limit = 10) {
  return useQuery({
    queryKey: adminKeys.recentActivities(limit),
    queryFn: () => adminApi.getRecentActivities(limit),
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useAdminSessionMetrics() {
  return useQuery({
    queryKey: adminKeys.sessionMetrics(),
    queryFn: adminApi.getSessionMetrics,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useAdminSubjectDistribution() {
  return useQuery({
    queryKey: adminKeys.subjectDistribution(),
    queryFn: adminApi.getSubjectDistribution,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useAdminMonthlyRevenue(months = 6) {
  return useQuery({
    queryKey: adminKeys.monthlyRevenue(months),
    queryFn: () => adminApi.getMonthlyRevenue(months),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useAdminUserGrowth(months = 6) {
  return useQuery({
    queryKey: adminKeys.userGrowth(months),
    queryFn: () => adminApi.getUserGrowth(months),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// User management hooks
export function useAdminUsers(filters: AdminUsersFilters = {}) {
  return useQuery({
    queryKey: adminKeys.usersList(filters),
    queryFn: () => adminApi.listUsers(filters),
  });
}

export function useUpdateAdminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: AdminUserUpdate }) =>
      adminApi.updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminKeys.dashboardStats() });
    },
  });
}

export function useDeleteAdminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: number) => adminApi.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminKeys.dashboardStats() });
    },
  });
}

// Tutor approval hooks
export function usePendingTutors(filters: AdminTutorsFilters = {}) {
  return useQuery({
    queryKey: adminKeys.pendingTutorsList(filters),
    queryFn: () => adminApi.listPendingTutors(filters),
  });
}

export function useApprovedTutors(filters: AdminTutorsFilters = {}) {
  return useQuery({
    queryKey: adminKeys.approvedTutorsList(filters),
    queryFn: () => adminApi.listApprovedTutors(filters),
  });
}

export function useApproveTutor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tutorId: number) => adminApi.approveTutor(tutorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminKeys.pendingTutors() });
      queryClient.invalidateQueries({ queryKey: adminKeys.approvedTutors() });
      queryClient.invalidateQueries({ queryKey: adminKeys.dashboardStats() });
      queryClient.invalidateQueries({ queryKey: adminKeys.recentActivities() });
    },
  });
}

export function useRejectTutor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tutorId, data }: { tutorId: number; data: TutorRejectionInput }) =>
      adminApi.rejectTutor(tutorId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminKeys.pendingTutors() });
      queryClient.invalidateQueries({ queryKey: adminKeys.dashboardStats() });
    },
  });
}
