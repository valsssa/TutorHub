import { api } from './client';
import type { User, AuthTokens, LoginInput, RegisterInput } from '@/types';

export const authApi = {
  login: (data: LoginInput) =>
    api.postForm<AuthTokens>('/auth/login', {
      username: data.email,
      password: data.password,
    }),

  register: (data: RegisterInput) =>
    api.post<User>('/auth/register', data),

  me: () =>
    api.get<User>('/auth/me'),

  logout: () =>
    api.post<{ message: string }>('/auth/logout'),

  forgotPassword: (email: string) =>
    api.post<{ message: string }>('/auth/password/reset-request', { email }),

  resetPassword: (token: string, newPassword: string) =>
    api.post<{ message: string }>('/auth/password/reset-confirm', { token, new_password: newPassword }),

  verifyResetToken: (token: string) =>
    api.post<{ message: string }>('/auth/password/verify-token', { token }),

  verifyEmail: (token: string) =>
    api.post<{ message: string }>('/auth/verify-email', { token }),

  updateProfile: (data: Partial<User>) =>
    api.put<User>('/auth/me', data),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<{ message: string }>('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
};
