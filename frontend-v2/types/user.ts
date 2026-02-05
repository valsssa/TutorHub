export type UserRole = 'student' | 'tutor' | 'admin' | 'owner';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  avatar_url?: string;
  is_active: boolean;
  is_verified?: boolean;
  timezone?: string;
  currency?: string;
  preferred_language?: string;
  locale?: string;
  created_at: string;
  updated_at?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in?: number;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: 'student' | 'tutor';
}
