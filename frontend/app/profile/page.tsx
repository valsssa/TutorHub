"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { FiUser, FiMail, FiSave, FiBookOpen, FiAward } from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import { auth, students } from "@/lib/api";
import { User, StudentProfile } from "@/types";
import { useToast } from "@/components/ToastContainer";
import LoadingSpinner from "@/components/LoadingSpinner";
import Button from "@/components/Button";
import Input from "@/components/Input";
import TextArea from "@/components/TextArea";
import AppShell from "@/components/AppShell";
import AvatarUploader from "@/components/AvatarUploader";

export default function ProfilePage() {
  return (
    <ProtectedRoute showNavbar={false}>
      <ProfileContent />
    </ProtectedRoute>
  );
}

function ProfileContent() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form state
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [bio, setBio] = useState("");
  const [learningGoals, setLearningGoals] = useState("");
  const [interests, setInterests] = useState("");

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    try {
      const [currentUser, studentProfile] = await Promise.all([
        auth.getCurrentUser(),
        students.getProfile().catch(() => null)
      ]);

      setUser(currentUser);
      setProfile(studentProfile);

      if (currentUser) {
        setFirstName(currentUser.first_name || "");
        setLastName(currentUser.last_name || "");
      }

      if (studentProfile) {
        setPhone(studentProfile.phone || "");
        setBio(studentProfile.bio || "");
        setLearningGoals(studentProfile.learning_goals || "");
        setInterests(studentProfile.interests || "");
      }
    } catch (error) {
      showError("Failed to load profile data");
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarChange = (url: string | null) => {
    setUser((prev) =>
      prev ? { ...prev, avatarUrl: url, avatar_url: url ?? null } : prev
    );
  };

  const handleSave = async () => {
    if (!firstName.trim() || !lastName.trim()) {
      showError("First name and last name are required");
      return;
    }

    setSaving(true);
    try {
      // Update user information (names) via auth API
      if (user) {
        const updatedUser = await auth.updateUser({
          first_name: firstName.trim() || undefined,
          last_name: lastName.trim() || undefined,
        });
        setUser(updatedUser);
      }

      // Update student profile information (excluding names)
      const updatedProfile = await students.updateProfile({
        phone: phone.trim() || undefined,
        bio: bio.trim() || undefined,
        learning_goals: learningGoals.trim() || undefined,
        interests: interests.trim() || undefined
      });

      setProfile(updatedProfile);
      showSuccess("Profile updated successfully!");
    } catch (error) {
      showError("Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <AppShell user={user}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Profile Header Card */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 md:p-8"
        >
          <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
            <div className="flex-shrink-0">
              <AvatarUploader
                initialUrl={user.avatar_url}
                onAvatarChange={handleAvatarChange}
                allowRemoval={true}
              />
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                {firstName || lastName ? `${firstName} ${lastName}` : "Complete Your Profile"}
              </h2>
              <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400 mb-3">
                <FiMail className="w-4 h-4" />
                <span>{user.email}</span>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  user.role === 'student' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' :
                  user.role === 'tutor' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                  'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                }`}>
                  {user.role}
                </span>
                {user.is_verified && (
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 rounded-full text-xs font-semibold flex items-center gap-1">
                    <FiAward className="w-3 h-3" />
                    Verified
                  </span>
                )}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Basic Information Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm hover:shadow-md transition-all"
        >
          <div className="p-6 md:p-8">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1 flex items-center gap-2">
              <FiUser className="w-5 h-5 text-emerald-600" />
              Basic Information
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">Update your personal details</p>

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="First Name *"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Enter your first name"
                  required
                />
                <Input
                  label="Last Name *"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Enter your last name"
                  required
                />
              </div>

              <Input
                label="Phone Number"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 (555) 000-0000"
              />

              <TextArea
                label="Bio"
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Tell us a bit about yourself..."
                rows={4}
              />
            </div>
          </div>
        </motion.div>

        {/* Learning Profile Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm hover:shadow-md transition-all"
        >
          <div className="p-6 md:p-8">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1 flex items-center gap-2">
              <FiBookOpen className="w-5 h-5 text-emerald-600" />
              Learning Profile
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">Help tutors personalize your learning experience</p>

            <div className="space-y-6">
              <TextArea
                label="Learning Goals"
                value={learningGoals}
                onChange={(e) => setLearningGoals(e.target.value)}
                placeholder="What do you want to achieve? (e.g., Master Python programming, Improve conversational Spanish, etc.)"
                rows={4}
                helperText="Help tutors understand your objectives"
              />

              <TextArea
                label="Interests & Hobbies"
                value={interests}
                onChange={(e) => setInterests(e.target.value)}
                placeholder="What are your interests? (e.g., Technology, Languages, Music, Sports, etc.)"
                rows={3}
                helperText="Tutors can personalize lessons based on your interests"
              />
            </div>
          </div>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex items-center justify-end gap-4"
        >
          <Button
            variant="ghost"
            onClick={() => router.push("/dashboard")}
            disabled={saving}
            className="px-6 py-2.5"
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={saving}
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5"
          >
            {saving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Saving...
              </>
            ) : (
              <>
                <FiSave className="w-4 h-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </motion.div>
      </div>
    </AppShell>
  );
}
