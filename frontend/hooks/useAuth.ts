/**
 * Centralized authentication hook
 * Fixes: Repetitive auth logic, useEffect dependency warnings, memory leaks
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { auth } from '@/lib/api';
import type { User } from '@/types';

interface UseAuthOptions {
  requiredRole?: 'admin' | 'tutor' | 'student' | 'owner';
  redirectTo?: string;
}

interface UseAuthReturn {
  user: User | null;
  loading: boolean;
  error: string | null;
  logout: () => void;
  refetch: () => Promise<void>;
  isAdmin: boolean;
  isTutor: boolean;
  isStudent: boolean;
  isOwner: boolean;
}

export function useAuth(options: UseAuthOptions = {}): UseAuthReturn {
  const { requiredRole, redirectTo = '/' } = options;
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Use ref to prevent multiple simultaneous auth checks
  const isCheckingRef = useRef(false);

  const checkAuth = useCallback(async () => {
    // Prevent concurrent auth checks
    if (isCheckingRef.current) return;

    isCheckingRef.current = true;
    setLoading(true);

    try {
      const currentUser = await auth.getCurrentUser();

      // Role authorization check
      if (requiredRole && currentUser.role !== requiredRole) {
        router.replace('/unauthorized');
        return;
      }

      setUser(currentUser);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed');
      setUser(null);
      router.replace(redirectTo);
    } finally {
      setLoading(false);
      isCheckingRef.current = false;
    }
  }, [requiredRole, redirectTo, router]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const logout = useCallback(() => {
    auth.logout();
    setUser(null);
    router.push('/');
  }, [router]);

  return {
    user,
    loading,
    error,
    logout,
    refetch: checkAuth,
    isAdmin: user?.role === 'admin',
    isTutor: user?.role === 'tutor',
    isStudent: user?.role === 'student',
    isOwner: user?.role === 'owner',
  };
}

/**
 * Hook for protected routes - simpler version
 */
export function useProtectedRoute(requiredRole?: 'admin' | 'tutor' | 'student' | 'owner') {
  return useAuth({ requiredRole });
}
