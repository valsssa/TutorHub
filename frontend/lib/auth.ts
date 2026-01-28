/**
 * Authentication utilities
 */
import type { User } from "@/types";

export const authUtils = {
  /**
   * Check if user has a specific role
   */
  hasRole(user: User | null, role: string): boolean {
    return user?.role === role;
  },

  /**
   * Check if user is admin
   */
  isAdmin(user: User | null): boolean {
    return this.hasRole(user, "admin");
  },

  /**
   * Check if user is tutor
   */
  isTutor(user: User | null): boolean {
    return this.hasRole(user, "tutor");
  },

  /**
   * Check if user is student
   */
  isStudent(user: User | null): boolean {
    return this.hasRole(user, "student");
  },

  /**
   * Get role display name
   */
  getRoleDisplayName(role: string): string {
    switch (role) {
      case "admin":
        return "Administrator";
      case "tutor":
        return "Tutor";
      case "student":
        return "Student";
      default:
        return role;
    }
  },

  /**
   * Get role color for badges
   */
  getRoleColor(role: string): string {
    switch (role) {
      case "admin":
        return "bg-red-100 text-red-800";
      case "tutor":
        return "bg-blue-100 text-blue-800";
      case "student":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  },

  /**
   * Check if user can access admin panel
   */
  canAccessAdmin(user: User | null): boolean {
    return this.isAdmin(user);
  },

  /**
   * Alias for canAccessAdmin for backward compatibility
   */
  canAccessAdminPanel(user: User | null): boolean {
    return this.isAdmin(user);
  },

  /**
   * Check if user can create tutor profile
   */
  canCreateTutorProfile(user: User | null): boolean {
    return this.isTutor(user);
  },

  /**
   * Check if user can book sessions
   */
  canBookSessions(user: User | null): boolean {
    return this.isStudent(user);
  },

  /**
   * Determine whether a user can access a route.
   * Admin routes -> admin only, tutor routes -> tutor only,
   * everything else requires an authenticated user.
   */
  canAccessRoute(user: User | null, path: string): boolean {
    if (!user) {
      return false;
    }

    if (path.startsWith("/admin")) {
      return this.isAdmin(user);
    }

    if (path.startsWith("/tutor")) {
      return this.isTutor(user);
    }

    return true;
  },
};
