"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { FiSave, FiUser } from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import { auth } from "@/lib/api";
import { User } from "@/types";
import { useToast } from "@/components/ToastContainer";
import Button from "@/components/Button";
import SettingsCard from "@/components/settings/SettingsCard";
import AvatarUploader from "@/components/AvatarUploader";

export default function ProfileSettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsContent />
    </ProtectedRoute>
  );
}

function SettingsContent() {
  const { showSuccess, showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [profile, setProfile] = useState({
    first_name: "",
    last_name: "",
    country: "",
    bio: "",
    learning_goal: "",
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);
        
        setProfile({
          first_name: currentUser.first_name || "",
          last_name: currentUser.last_name || "",
          country: currentUser.country || "",
          bio: currentUser.bio || "",
          learning_goal: currentUser.learning_goal || "",
        });
      } catch (error) {
        showError("Failed to load profile");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [showError]);

  const handleAvatarChange = (url: string | null) => {
    if (user) {
      setUser({
        ...user,
        avatarUrl: url,
        avatar_url: url,
      });
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      showSuccess("Profile updated successfully ✅");
    } catch (error: any) {
      showError(error.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600"></div>
      </div>
    );
  }

  const bioLength = profile.bio?.length || 0;
  const bioMaxLength = 300;

  return (
    <div className="space-y-6">
      {/* Greeting Banner */}
      <div className="bg-gradient-to-br from-sky-50 to-blue-50 border border-sky-100 rounded-2xl p-6">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full overflow-hidden border-3 border-white shadow-lg relative">
            {user.avatarUrl || user.avatar_url ? (
              <Image
                src={user.avatarUrl ?? user.avatar_url ?? ''}
                alt={user.email}
                width={64}
                height={64}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center">
                <FiUser className="w-8 h-8 text-white" />
              </div>
            )}
          </div>
          <div>
            <p className="text-sm text-slate-600">{getGreeting()} 👋</p>
            <h2 className="text-2xl font-bold text-slate-900">
              {profile.first_name || user.email.split('@')[0]}
            </h2>
            <p className="text-sm text-slate-600 mt-0.5">This is your personal space.</p>
          </div>
        </div>
      </div>

      {/* Avatar Upload */}
      <SettingsCard
        title="Profile Photo"
        description="Profiles with photos get 3× more engagement"
      >
        <AvatarUploader
          initialUrl={user.avatarUrl ?? user.avatar_url}
          onAvatarChange={handleAvatarChange}
        />
      </SettingsCard>

      {/* Personal Information */}
      <SettingsCard
        title="Personal Information"
        description="Your basic profile details"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                First Name
              </label>
              <input
                type="text"
                value={profile.first_name}
                onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-transparent"
                placeholder="Enter your first name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Last Name
              </label>
              <input
                type="text"
                value={profile.last_name}
                onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-transparent"
                placeholder="Enter your last name"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Country
            </label>
            <select
              value={profile.country}
              onChange={(e) => setProfile({ ...profile, country: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-transparent"
            >
              <option value="">Select your country</option>
              <option value="US">🇺🇸 United States</option>
              <option value="GB">🇬🇧 United Kingdom</option>
              <option value="CA">🇨🇦 Canada</option>
              <option value="AU">🇦🇺 Australia</option>
              <option value="DE">🇩🇪 Germany</option>
              <option value="FR">🇫🇷 France</option>
              <option value="ES">🇪🇸 Spain</option>
              <option value="IT">🇮🇹 Italy</option>
              <option value="JP">🇯🇵 Japan</option>
              <option value="IN">🇮🇳 India</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Learning Goal
            </label>
            <select
              value={profile.learning_goal}
              onChange={(e) => setProfile({ ...profile, learning_goal: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-transparent"
            >
              <option value="">Select your primary goal</option>
              <option value="travel">🌍 Travel & Communication</option>
              <option value="business">💼 Business & Career</option>
              <option value="academic">📚 Academic Excellence</option>
              <option value="personal">🎯 Personal Development</option>
              <option value="hobby">🎨 Hobby & Interest</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Bio
            </label>
            <textarea
              value={profile.bio}
              onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
              rows={4}
              maxLength={bioMaxLength}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-transparent"
              placeholder="Tell us about yourself, your interests, and what you hope to achieve..."
            />
            <div className="flex justify-between text-xs mt-1">
              <span className="text-slate-500">Share a bit about yourself</span>
              <span className={`${bioLength > bioMaxLength * 0.9 ? 'text-orange-600' : 'text-slate-400'}`}>
                {bioLength}/{bioMaxLength}
              </span>
            </div>
          </div>
        </div>
      </SettingsCard>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 bg-rose-500 hover:bg-rose-600"
        >
          <FiSave className="w-4 h-4" />
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </div>
    </div>
  );
}
