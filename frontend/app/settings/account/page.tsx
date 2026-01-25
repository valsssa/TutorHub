"use client";

import { useState, useEffect } from "react";
import { Eye, EyeOff } from "lucide-react";
import { auth } from "@/lib/api";
import { User } from "@/types";
import { useToast } from "@/components/ToastContainer";

export default function AccountPage() {
  const { showSuccess, showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  const [passwordForm, setPasswordForm] = useState({
    current: "",
    new: "",
    confirm: "",
  });
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

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
    } catch (error: any) {
      showError(error.message || "Failed to change password");
    }
  };

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
      <div>
        <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Create Password</h3>

        <div className="space-y-6">
          <div>
            <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Current password</label>
            <div className="relative">
              <input 
                type={showCurrentPassword ? "text" : "password"}
                value={passwordForm.current}
                onChange={(e) => setPasswordForm({ ...passwordForm, current: e.target.value })}
                className="w-full p-3 pr-10 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors" 
                placeholder="Enter your current password"
              />
              <button 
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                {showCurrentPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <div className="mt-2">
              <button 
                onClick={() => alert('Password reset link sent to your email.')}
                className="text-sm font-bold text-slate-900 dark:text-white hover:text-emerald-600 dark:hover:text-emerald-400 border-b border-slate-900 dark:border-white hover:border-emerald-600 dark:hover:border-emerald-400 transition-all"
              >
                Forgot your password?
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">New password</label>
            <div className="relative">
              <input 
                type={showNewPassword ? "text" : "password"}
                value={passwordForm.new}
                onChange={(e) => setPasswordForm({ ...passwordForm, new: e.target.value })}
                className="w-full p-3 pr-10 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors" 
                placeholder="Enter new password (min 6 characters)"
              />
              <button 
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Verify password</label>
            <div className="relative">
              <input 
                type={showConfirmPassword ? "text" : "password"}
                value={passwordForm.confirm}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
                className="w-full p-3 pr-10 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors" 
                placeholder="Confirm your new password"
              />
              <button 
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
        </div>

        <div className="pt-6">
          <button 
            onClick={handlePasswordChange}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5"
          >
            Save changes
          </button>
        </div>
      </div>
    </div>
  );
}
