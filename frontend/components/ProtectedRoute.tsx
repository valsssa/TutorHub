"use client";

import { useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";
import { auth } from "@/lib/api";
import { User } from "@/types";
import { isProfileComplete } from "@/lib/displayName";
import LoadingSpinner from "./LoadingSpinner";
import Navbar from "./Navbar";
import Footer from "./Footer";
import ErrorBoundary from "./ErrorBoundary";
import CompleteProfile from "./CompleteProfile";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: "admin" | "tutor" | "student";
  showNavbar?: boolean;
  /** Skip profile completion check (for pages that handle it themselves) */
  skipProfileCheck?: boolean;
}

export default function ProtectedRoute({
  children,
  requiredRole,
  showNavbar = true,
  skipProfileCheck = false,
}: ProtectedRouteProps) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [showProfileComplete, setShowProfileComplete] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const token = Cookies.get("token");

      if (!token) {
        setLoading(false);
        router.replace("/");
        return;
      }

      try {
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);

        // Check role requirement
        if (requiredRole && currentUser.role !== requiredRole) {
          setLoading(false);
          router.replace("/unauthorized");
          return;
        }

        // Check if profile is incomplete (missing names)
        // Show CompleteProfile gate unless skipProfileCheck is true
        if (!skipProfileCheck && !isProfileComplete(currentUser)) {
          setShowProfileComplete(true);
        }

        setLoading(false);
      } catch (error) {
        Cookies.remove("token");
        Cookies.remove("token_expiry");
        setLoading(false);
        router.replace("/");
      }
    };

    checkAuth();
  }, [router, requiredRole, skipProfileCheck]);

  // Handle profile completion
  const handleProfileComplete = (updatedUser: User) => {
    setUser(updatedUser);
    setShowProfileComplete(false);
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return null;
  }

  // Show CompleteProfile gate if user has incomplete profile
  if (showProfileComplete) {
    return (
      <CompleteProfile
        user={user}
        onComplete={handleProfileComplete}
      />
    );
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col transition-colors duration-200">
        {showNavbar && <Navbar user={user} />}
        <main id="main-content" role="main" className="flex-1">
          <ErrorBoundary inline={false}>
            {children}
          </ErrorBoundary>
        </main>
        {showNavbar && <Footer />}
      </div>
    </ErrorBoundary>
  );
}
