"use client";

import { useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";
import { auth } from "@/lib/api";
import { User } from "@/types";
import LoadingSpinner from "./LoadingSpinner";
import Navbar from "./Navbar";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: "admin" | "tutor" | "student";
  showNavbar?: boolean;
}

export default function ProtectedRoute({
  children,
  requiredRole,
  showNavbar = true,
}: ProtectedRouteProps) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = Cookies.get("token");

      if (!token) {
        setLoading(false);
        router.replace("/login");
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

        setLoading(false);
      } catch (error) {
        Cookies.remove("token");
        setLoading(false);
        router.replace("/login");
      }
    };

    checkAuth();
  }, [router, requiredRole]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {showNavbar && <Navbar user={user} />}
      <main>{children}</main>
    </div>
  );
}
