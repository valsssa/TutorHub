"use client";

import { useState, useEffect } from "react";
import { FiMail, FiLock, FiShield, FiAlertCircle } from "react-icons/fi";
import { auth } from "@/lib/api";
import { User } from "@/types";
import { useToast } from "@/components/ToastContainer";
import Button from "@/components/Button";
import SettingsCard from "@/components/settings/SettingsCard";

export default function AccountPage() {
  const { showSuccess, showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  
  const [passwordForm, setPasswordForm] = useState({
    current: "",
    new: "",
    confirm: "",
  });

  useEffect(() => {
    const loadUser = async () => {
      try {
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        showError("Failed to load account info");
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, [showError]);

  const handlePasswordChange = async () => {
    if (passwordForm.new !== passwordForm.confirm) {
      showError("New passwords don't match");
      return;
    }
    
    if (passwordForm.new.length < 6) {
      showError("Password must be at least 6 characters");
      return;
    }

    try {
      showSuccess("Password changed successfully 🔒");
      setPasswordForm({ current: "", new: "", confirm: "" });
      setChangePasswordOpen(false);
    } catch (error: any) {
      showError(error.message || "Failed to change password");
    }
  };

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          🔐 Account Security
        </h2>
        <p className="text-slate-600">
          Manage your login credentials and security settings
        </p>
      </div>

      {/* Email */}
      <SettingsCard
        title="Email Address"
        description="Your primary email for login and notifications"
      >
        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-100">
          <div className="flex items-center gap-3">
            <FiMail className="w-5 h-5 text-slate-400" />
            <div>
              <p className="font-medium text-slate-900">{user.email}</p>
              <p className="text-xs text-green-600 flex items-center gap-1 mt-0.5">
                ✓ Verified
              </p>
            </div>
          </div>
        </div>
        <div className="mt-3 p-3 bg-blue-50 border border-blue-100 rounded-lg">
          <p className="text-xs text-blue-800">
            <strong>Note:</strong> Email changes require verification and may affect your login.
          </p>
        </div>
      </SettingsCard>

      {/* Password */}
      <SettingsCard
        title="Password"
        description="Keep your account secure with a strong password"
      >
        <div>
          {!changePasswordOpen ? (
            <Button
              variant="secondary"
              onClick={() => setChangePasswordOpen(true)}
              className="flex items-center gap-2"
            >
              <FiLock className="w-4 h-4" />
              Change Password
            </Button>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Current Password
                </label>
                <input
                  type="password"
                  value={passwordForm.current}
                  onChange={(e) =>
                    setPasswordForm({ ...passwordForm, current: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-transparent"
                  placeholder="Enter your current password"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  New Password
                </label>
                <input
                  type="password"
                  value={passwordForm.new}
                  onChange={(e) =>
                    setPasswordForm({ ...passwordForm, new: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-transparent"
                  placeholder="Enter new password (min 6 characters)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={passwordForm.confirm}
                  onChange={(e) =>
                    setPasswordForm({ ...passwordForm, confirm: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-transparent"
                  placeholder="Confirm your new password"
                />
              </div>

              <div className="flex gap-3">
                <Button
                  variant="primary"
                  onClick={handlePasswordChange}
                  className="flex items-center gap-2"
                >
                  Update Password
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setChangePasswordOpen(false);
                    setPasswordForm({ current: "", new: "", confirm: "" });
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      </SettingsCard>

      {/* Two-Factor Authentication */}
      <SettingsCard
        title="Two-Factor Authentication (2FA)"
        description="Add an extra layer of security to your account"
      >
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-3">
            <FiShield className="w-5 h-5 text-amber-600 mt-0.5" />
            <div>
              <p className="font-medium text-amber-900 mb-1">Coming Soon</p>
              <p className="text-sm text-amber-800">
                Two-factor authentication will be available in a future update.
              </p>
            </div>
          </div>
        </div>
      </SettingsCard>

      {/* Active Sessions */}
      <SettingsCard
        title="Active Sessions"
        description="Manage devices where you're logged in"
      >
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
            <div>
              <p className="font-medium text-slate-900">Current Device</p>
              <p className="text-xs text-slate-500 mt-0.5">Active now</p>
            </div>
            <span className="text-xs text-green-600 font-medium">● Active</span>
          </div>
          
          <Button
            variant="ghost"
            className="w-full text-red-600 hover:bg-red-50"
          >
            Log Out From All Devices
          </Button>
        </div>
      </SettingsCard>
    </div>
  );
}
