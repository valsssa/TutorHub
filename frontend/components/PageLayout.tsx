"use client";

import { ReactNode, useEffect, useState } from "react";
import Cookies from "js-cookie";
import { auth } from "@/lib/api";
import { User } from "@/types";
import Navbar from "./Navbar";
import PublicHeader from "./PublicHeader";
import Footer from "./Footer";
import LoadingSpinner from "./LoadingSpinner";

interface PageLayoutProps {
  children: ReactNode;
  showHeader?: boolean;
  showFooter?: boolean;
  requireAuth?: boolean;
}

export default function PageLayout({
  children,
  showHeader = true,
  showFooter = true,
  requireAuth = false,
}: PageLayoutProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(requireAuth);

  useEffect(() => {
    if (requireAuth) {
      const checkAuth = async () => {
        const token = Cookies.get("token");
        if (token) {
          try {
            const currentUser = await auth.getCurrentUser();
            setUser(currentUser);
          } catch (error) {
            // User not authenticated, will show public header
          }
        }
        setLoading(false);
      };
      checkAuth();
    } else {
      // For non-required auth pages, just check if user exists
      const token = Cookies.get("token");
      if (token) {
        auth.getCurrentUser().then(setUser).catch(() => setUser(null));
      }
    }
  }, [requireAuth]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col transition-colors duration-200">
      {showHeader && (
        user ? (
          <Navbar user={user} />
        ) : (
          <PublicHeader />
        )
      )}

      <main id="main-content" role="main" className="flex-1">
        {children}
      </main>

      {showFooter && <Footer />}
    </div>
  );
}
