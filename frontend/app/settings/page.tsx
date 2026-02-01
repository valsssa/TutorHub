"use client";

import { useEffect, useState, useRef } from "react";
import Image from "next/image";
import { Upload, Camera, User as UserIcon } from "lucide-react";
import { motion } from "framer-motion";
import { auth } from "@/lib/api";
import { User } from "@/types";
import { useToast } from "@/components/ToastContainer";
import { avatars } from "@/lib/api";
import Input from "@/components/Input";
import Button from "@/components/Button";
import SettingsCard from "@/components/settings/SettingsCard";
import LoadingSpinner from "@/components/LoadingSpinner";

export default function ProfileSettingsPage() {
  const { showSuccess, showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Account Form State
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);
        
        if (currentUser.first_name) {
          const nameParts = currentUser.first_name.split(" ");
          setFirstName(nameParts[0] || "");
          setLastName(nameParts.slice(1).join(" ") || "");
        } else {
          setFirstName("");
          setLastName("");
        }
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

    // Validate file size (2MB)
    if (file.size > 2 * 1024 * 1024) {
      showError("File size must be less than 2MB");
      return;
    }

    // Validate file type
    if (!file.type.match(/^image\/(jpeg|jpg|png)$/)) {
      showError("Please upload a JPG or PNG image");
      return;
    }

    setUploading(true);
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
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleSave = async () => {
    if (!firstName.trim()) {
      showError("First name is required");
      return;
    }

    setSaving(true);
    try {
      const updatedUser = await auth.updateUser({
        first_name: firstName.trim(),
        last_name: lastName.trim() || undefined,
      });
      setUser(updatedUser);
      showSuccess("Profile updated successfully");
    } catch (error: any) {
      showError(error.response?.data?.detail || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const displayName = firstName || user.email.split('@')[0];
  const avatarUrl = user.avatarUrl ?? user.avatar_url;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
          Profile Settings
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          Manage your profile information and photo
        </p>
      </div>

      {/* Profile Photo Section */}
      <SettingsCard
        title="Profile Photo"
        description="Upload a photo to help others recognize you"
      >
        <div className="flex flex-col sm:flex-row items-start gap-6 sm:gap-8">
          <div className="flex flex-col items-center gap-3">
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="relative w-32 h-32 rounded-full overflow-hidden flex-shrink-0 shadow-lg ring-2 ring-slate-200 dark:ring-slate-700"
            >
              {avatarUrl ? (
                <Image
                  src={avatarUrl}
                  alt="Profile"
                  width={128}
                  height={128}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-emerald-500 via-teal-500 to-cyan-500 flex items-center justify-center text-white">
                  <UserIcon className="w-16 h-16" />
                </div>
              )}
              {uploading && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                  <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                </div>
              )}
            </motion.div>
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="text-sm text-emerald-600 dark:text-emerald-400 font-medium hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              <Camera className="w-4 h-4" />
              Change photo
            </button>
          </div>
          
          <div className="flex-1 space-y-4 w-full sm:w-auto">
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              accept="image/png, image/jpeg, image/jpg"
              disabled={uploading}
            />
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="w-full sm:w-auto"
            >
              <Upload className="w-4 h-4" />
              {uploading ? "Uploading..." : "Upload new photo"}
            </Button>
            <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1">
              <p className="flex items-center gap-1">
                <span className="font-medium">Maximum size:</span> 2MB
              </p>
              <p className="flex items-center gap-1">
                <span className="font-medium">Formats:</span> JPG, PNG
              </p>
            </div>
          </div>
        </div>
      </SettingsCard>

      {/* Personal Information Section */}
      <SettingsCard
        title="Personal Information"
        description="Update your name and basic information"
        footer={
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={() => {
                if (user.first_name) {
                  const nameParts = user.first_name.split(" ");
                  setFirstName(nameParts[0] || "");
                  setLastName(nameParts.slice(1).join(" ") || "");
                } else {
                  setFirstName("");
                  setLastName("");
                }
              }}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              isLoading={saving}
              disabled={saving || uploading}
            >
              Save changes
            </Button>
          </div>
        }
      >
        <div className="space-y-5">
          <Input
            label="First name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="Enter your first name"
            required
            disabled={saving}
          />
          <Input
            label="Last name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Enter your last name"
            disabled={saving}
          />
          <div className="pt-2">
            <label className="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-1.5">
              Email
            </label>
            <div className="px-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-600 dark:text-slate-400">
              {user.email}
            </div>
            <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
              Email cannot be changed. Contact support if you need to update it.
            </p>
          </div>
        </div>
      </SettingsCard>
    </div>
  );
}
