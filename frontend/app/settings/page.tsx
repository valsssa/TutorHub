"use client";

import { useEffect, useState, useRef } from "react";
import Image from "next/image";
import { Upload } from "lucide-react";
import { auth } from "@/lib/api";
import { User } from "@/types";
import { useToast } from "@/components/ToastContainer";
import { avatars } from "@/lib/api";

export default function ProfileSettingsPage() {
  const { showSuccess, showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Account Form State
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);
        
        const nameParts = (currentUser.first_name || "").split(" ");
        setFirstName(nameParts[0] || "");
        setLastName(nameParts.slice(1).join(" ") || "");
      } catch (error) {
        showError("Failed to load profile");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [showError]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const result = await avatars.upload(file);
      if (user) {
        setUser({
          ...user,
          avatarUrl: result.avatarUrl,
          avatar_url: result.avatarUrl,
        });
        showSuccess("Profile photo updated successfully");
      }
    } catch (error: any) {
      showError(error.message || "Failed to upload photo");
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // TODO: Implement API call to update user profile
      showSuccess("Profile updated successfully ✅");
    } catch (error: any) {
      showError(error.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  const displayName = firstName || user.email.split('@')[0];
  const avatarUrl = user.avatarUrl ?? user.avatar_url;

  return (
    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
      {/* Profile Image */}
      <div className="space-y-4">
        <label className="block text-sm font-medium text-slate-900 dark:text-white">Profile image</label>
        <div className="flex flex-col sm:flex-row items-start gap-6 sm:gap-8">
          <div className="flex flex-col items-center gap-2">
            <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-full overflow-hidden flex-shrink-0 shadow-sm">
              {avatarUrl ? (
                <Image
                  src={avatarUrl}
                  alt="Profile"
                  width={128}
                  height={128}
                  className="w-full h-full object-cover"
                  unoptimized
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-bold text-3xl sm:text-4xl">
                  {displayName.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="text-sm text-slate-900 dark:text-white underline decoration-slate-900 dark:decoration-white font-medium hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
            >
              Edit
            </button>
          </div>
          <div className="pt-2 space-y-3 w-full sm:w-auto">
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              accept="image/png, image/jpeg"
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center justify-center sm:justify-start gap-2 px-4 py-2 w-full sm:w-auto bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-sm font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors shadow-sm"
            >
              <Upload size={16} /> Upload photo
            </button>
            <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1 text-center sm:text-left">
              <p>Maximum size – 2MB</p>
              <p>JPG or PNG format</p>
            </div>
          </div>
        </div>
      </div>

      {/* Name Fields */}
      <div className="space-y-6">
        <div>
          <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">
            First name <span className="text-slate-400 font-normal text-xs ml-1">• Required</span>
          </label>
          <input 
            type="text" 
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
            placeholder="Enter your first name"
          />
        </div>
        <div>
          <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">Last name</label>
          <input 
            type="text" 
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
            placeholder="Enter your last name"
          />
        </div>
      </div>

      {/* Save Button */}
      <div className="pt-4 pb-8">
        <button 
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
        >
          {saving ? 'Saving...' : 'Save changes'}
        </button>
      </div>
    </div>
  );
}
