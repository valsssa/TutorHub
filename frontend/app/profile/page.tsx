"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { FiUser, FiMail, FiSave, FiBookOpen, FiTrendingUp, FiTarget, FiAward } from "react-icons/fi";
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

      if (studentProfile) {
        setFirstName(studentProfile.first_name || "");
        setLastName(studentProfile.last_name || "");
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
      const updated = await students.updateProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone: phone.trim() || undefined,
        bio: bio.trim() || undefined,
        learning_goals: learningGoals.trim() || undefined,
        interests: interests.trim() || undefined
      });

      setProfile(updated);
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
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-primary-600 via-pink-500 to-purple-600 rounded-2xl shadow-warm p-6 md:p-8 text-white"
        >
          <h1 className="text-2xl md:text-3xl font-bold mb-2">
            My Profile 👤
          </h1>
          <p className="text-white/90">
            Manage your personal information and learning preferences
          </p>
        </motion.div>

        {/* Profile Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-soft p-6 md:p-8"
        >
          {/* Avatar Section */}
          <div className="flex flex-col md:flex-row items-start md:items-center gap-6 mb-8 pb-8 border-b border-gray-200">
            <div className="flex-shrink-0">
              <AvatarUploader
                initialUrl={user.avatar_url}
                onAvatarChange={handleAvatarChange}
                allowRemoval={true}
              />
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {firstName || lastName ? `${firstName} ${lastName}` : "Complete Your Profile"}
              </h2>
              <div className="flex items-center gap-2 text-gray-600 mb-3">
                <FiMail className="w-4 h-4" />
                <span>{user.email}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  user.role === 'student' ? 'bg-green-100 text-green-700' :
                  user.role === 'tutor' ? 'bg-blue-100 text-blue-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {user.role}
                </span>
                {user.is_verified && (
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold flex items-center gap-1">
                    <FiAward className="w-3 h-3" />
                    Verified
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Basic Information */}
          <div className="space-y-6 mb-8">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <FiUser className="text-primary-600" />
              Basic Information
            </h3>

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

          {/* Learning Information */}
          <div className="space-y-6 mb-8">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <FiBookOpen className="text-primary-600" />
              Learning Profile
            </h3>

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

          {/* Save Button */}
          <div className="flex items-center justify-end gap-4 pt-6 border-t border-gray-200">
            <Button
              variant="ghost"
              onClick={() => router.push("/dashboard")}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={saving}
              className="bg-gradient-to-r from-primary-600 to-pink-600 shadow-warm"
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
          </div>
        </motion.div>

        {/* Quick Stats */}
        {profile && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-slate-50 to-blue-50 rounded-2xl shadow-soft p-6"
          >
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <FiTrendingUp className="text-primary-600" />
              Your Learning Journey
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl p-4 text-center">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-sky-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <FiBookOpen className="w-5 h-5 text-blue-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900 mb-1">0</p>
                <p className="text-xs text-gray-600">Completed Sessions</p>
              </div>

              <div className="bg-white rounded-xl p-4 text-center">
                <div className="w-10 h-10 bg-gradient-to-br from-green-100 to-emerald-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <FiTarget className="w-5 h-5 text-green-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900 mb-1">0</p>
                <p className="text-xs text-gray-600">Active Courses</p>
              </div>

              <div className="bg-white rounded-xl p-4 text-center">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-100 to-pink-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <FiAward className="w-5 h-5 text-purple-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900 mb-1">0</p>
                <p className="text-xs text-gray-600">Achievements</p>
              </div>

              <div className="bg-white rounded-xl p-4 text-center">
                <div className="w-10 h-10 bg-gradient-to-br from-yellow-100 to-amber-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <FiTrendingUp className="w-5 h-5 text-yellow-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900 mb-1">0</p>
                <p className="text-xs text-gray-600">Learning Streak</p>
              </div>
            </div>

            <div className="mt-6 p-4 bg-white/50 backdrop-blur-sm rounded-xl">
              <p className="text-sm text-gray-700 text-center">
                💡 <strong>Tip:</strong> Complete your profile to help tutors personalize your learning experience!
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </AppShell>
  );
}
