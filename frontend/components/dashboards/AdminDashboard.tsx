"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { FiUsers, FiTrendingUp } from "react-icons/fi";
import { User } from "@/types";
import AppShell from "@/components/AppShell";

interface AdminDashboardProps {
  user: User;
  onAvatarChange: (url: string | null) => void;
}

export default function AdminDashboard({
  user,
  onAvatarChange,
}: AdminDashboardProps) {
  const router = useRouter();

  return (
    <AppShell user={user}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Hero Banner */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-red-500 via-pink-500 to-purple-500 rounded-2xl shadow-warm p-6 md:p-8 text-white"
        >
          <h1 className="text-2xl md:text-3xl font-bold mb-2">
            Admin Dashboard 🛡️
          </h1>
          <p className="text-white/90">
            Manage users and platform settings
          </p>
        </motion.div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-red-500 to-red-700 rounded-2xl shadow-floating p-6 text-white cursor-pointer hover:scale-105 transition-transform"
            onClick={() => router.push("/admin")}
          >
            <FiUsers className="w-12 h-12 mb-4 opacity-90" />
            <h3 className="text-2xl font-bold mb-2">User Management 👥</h3>
            <p className="mb-4 opacity-90 text-sm">View and manage all platform users</p>
            <div className="inline-flex items-center gap-2 text-sm font-semibold">
              Manage users →
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-purple-500 to-purple-700 rounded-2xl shadow-floating p-6 text-white"
          >
            <FiTrendingUp className="w-12 h-12 mb-4 opacity-90" />
            <h3 className="text-2xl font-bold mb-2">Analytics 📊</h3>
            <p className="mb-4 opacity-90 text-sm">
              View platform statistics and insights
            </p>
            <div className="inline-flex items-center gap-2 text-sm font-semibold text-white/70">
              Coming soon...
            </div>
          </motion.div>
        </div>
      </div>
    </AppShell>
  );
}
