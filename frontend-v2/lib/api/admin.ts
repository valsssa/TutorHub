import { api } from './client';
import { toQueryString } from '@/lib/utils';
import type {
  AdminDashboardStats,
  AdminActivityItem,
  PendingTutorProfile,
  TutorApprovalResponse,
  TutorRejectionInput,
  SessionMetric,
  SubjectDistribution,
  MonthlyData,
  UserGrowthData,
  AdminUserUpdate,
  PaginatedResponse,
} from '@/types/admin';
import type { AdminUser } from '@/types/owner';

export interface AdminUsersFilters {
  page?: number;
  page_size?: number;
  status?: 'all' | 'active' | 'inactive';
}

export interface AdminTutorsFilters {
  page?: number;
  page_size?: number;
}

export const adminApi = {
  // Dashboard Statistics
  getDashboardStats: () =>
    api.get<AdminDashboardStats>('/admin/dashboard/stats'),

  getRecentActivities: (limit = 10) =>
    api.get<AdminActivityItem[]>(`/admin/dashboard/recent-activities?limit=${limit}`),

  getSessionMetrics: () =>
    api.get<SessionMetric[]>('/admin/dashboard/session-metrics'),

  getSubjectDistribution: () =>
    api.get<SubjectDistribution[]>('/admin/dashboard/subject-distribution'),

  getMonthlyRevenue: (months = 6) =>
    api.get<MonthlyData[]>(`/admin/dashboard/monthly-revenue?months=${months}`),

  getUserGrowth: (months = 6) =>
    api.get<UserGrowthData[]>(`/admin/dashboard/user-growth?months=${months}`),

  // User Management
  listUsers: (filters: AdminUsersFilters = {}) =>
    api.get<PaginatedResponse<AdminUser>>(`/admin/users?${toQueryString(filters)}`),

  updateUser: (userId: number, data: AdminUserUpdate) =>
    api.put<AdminUser>(`/admin/users/${userId}`, data),

  deleteUser: (userId: number) =>
    api.delete<{ message: string }>(`/admin/users/${userId}`),

  // Tutor Approval Workflow
  listPendingTutors: (filters: AdminTutorsFilters = {}) =>
    api.get<PaginatedResponse<PendingTutorProfile>>(`/admin/tutors/pending?${toQueryString(filters)}`),

  listApprovedTutors: (filters: AdminTutorsFilters = {}) =>
    api.get<PaginatedResponse<PendingTutorProfile>>(`/admin/tutors/approved?${toQueryString(filters)}`),

  approveTutor: (tutorId: number) =>
    api.post<TutorApprovalResponse>(`/admin/tutors/${tutorId}/approve`, {}),

  rejectTutor: (tutorId: number, data: TutorRejectionInput) =>
    api.post<TutorApprovalResponse>(`/admin/tutors/${tutorId}/reject`, data),
};
