import type { PaginatedResponse } from './api';

export type { PaginatedResponse };

export interface AdminDashboardStats {
  totalUsers: number;
  activeTutors: number;
  totalSessions: number;
  revenue: number;
  satisfaction: number;
  completionRate: number;
}

export interface AdminActivityItem {
  id: number;
  user: string;
  action: string;
  time: string;
  type: 'success' | 'info' | 'warning' | 'error';
}

export interface PendingTutorProfile {
  id: number;
  user_id: number;
  headline?: string;
  bio?: string;
  hourly_rate?: number;
  profile_status: 'pending_approval' | 'under_review' | 'approved' | 'rejected';
  created_at: string;
  user?: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
  subjects?: Array<{
    id: number;
    name: string;
  }>;
}

export interface TutorApprovalResponse {
  id: number;
  is_approved: boolean;
  profile_status: string;
  approved_at?: string;
  approved_by?: number;
  rejection_reason?: string;
}

export interface TutorRejectionInput {
  rejection_reason: string;
}

export interface SessionMetric {
  metric: string;
  value: string;
  change: string;
}

export interface SubjectDistribution {
  subject: string;
  value: number;
  color: string;
}

export interface MonthlyData {
  month: string;
  revenue: number;
  sessions: number;
}

export interface UserGrowthData {
  month: string;
  tutors: number;
  students: number;
}

export interface AdminUserUpdate {
  email?: string;
  role?: 'student' | 'tutor' | 'admin';
  is_active?: boolean;
}
