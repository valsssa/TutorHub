"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { FiClock, FiDollarSign, FiCheck, FiStar, FiUser, FiPackage } from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import { packages, tutors } from "@/lib/api";
import { StudentPackage, TutorPublicSummary } from "@/types";
import { useToast } from "@/components/ToastContainer";
import LoadingSpinner from "@/components/LoadingSpinner";
import Button from "@/components/Button";
import AppShell from "@/components/AppShell";
import { auth } from "@/lib/api";
import { User } from "@/types";

export default function PackagesPage() {
  return (
    <ProtectedRoute showNavbar={false}>
      <PackagesContent />
    </ProtectedRoute>
  );
}

function PackagesContent() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [myPackages, setMyPackages] = useState<StudentPackage[]>([]);
  const [availableTutors, setAvailableTutors] = useState<TutorPublicSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<"my-packages" | "browse">("my-packages");

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    try {
      const [currentUser, packagesData, tutorsData] = await Promise.all([
        auth.getCurrentUser(),
        packages.list(),
        tutors.list({ page_size: 20, sort_by: "rating" })
      ]);

      setUser(currentUser);
      setMyPackages(Array.isArray(packagesData) ? packagesData : []);
      setAvailableTutors(Array.isArray(tutorsData) ? tutorsData : []);
    } catch (error) {
      showError("Failed to load packages data");
    } finally {
      setLoading(false);
    }
  };

  const activePackages = useMemo(
    () => myPackages.filter((p) => p.status === "active"),
    [myPackages]
  );

  const exhaustedPackages = useMemo(
    () => myPackages.filter((p) => p.status === "exhausted" || p.status === "expired"),
    [myPackages]
  );

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <AppShell user={user}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-purple-600 via-pink-500 to-primary-600 rounded-2xl shadow-warm p-6 md:p-8 text-white"
        >
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold mb-2">
                Session Packages 🎁
              </h1>
              <p className="text-white/90">
                Save money with multi-session packages from your favorite tutors
              </p>
            </div>
            <div className="flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-xl px-4 py-2">
              <FiPackage className="w-5 h-5" />
              <span className="font-bold">
                {activePackages.length} Active Package{activePackages.length !== 1 ? "s" : ""}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-2 bg-white rounded-xl p-1 shadow-soft">
          <button
            onClick={() => setSelectedTab("my-packages")}
            className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all ${
              selectedTab === "my-packages"
                ? "bg-gradient-to-r from-primary-600 to-pink-600 text-white shadow-md"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            My Packages ({myPackages.length})
          </button>
          <button
            onClick={() => setSelectedTab("browse")}
            className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all ${
              selectedTab === "browse"
                ? "bg-gradient-to-r from-primary-600 to-pink-600 text-white shadow-md"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Browse Packages
          </button>
        </div>

        {/* My Packages Tab */}
        {selectedTab === "my-packages" && (
          <div className="space-y-6">
            {/* Active Packages */}
            {activePackages.length > 0 && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <FiPackage className="text-green-600" />
                  Active Packages
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {activePackages.map((pkg) => (
                    <motion.div
                      key={pkg.id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="bg-white rounded-2xl shadow-soft hover:shadow-lg transition-all border-2 border-green-200 p-6"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl flex items-center justify-center">
                            <FiPackage className="w-6 h-6 text-green-600" />
                          </div>
                          <div>
                            <p className="font-bold text-gray-900">Package #{pkg.id}</p>
                            <p className="text-sm text-gray-600">Active</p>
                          </div>
                        </div>
                        <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
                          {pkg.sessions_remaining} left
                        </span>
                      </div>

                      <div className="space-y-3 mb-4">
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                          <span className="text-sm text-gray-600">Purchased</span>
                          <span className="font-semibold text-gray-900">
                            {pkg.sessions_purchased} sessions
                          </span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                          <span className="text-sm text-gray-600">Used</span>
                          <span className="font-semibold text-gray-900">
                            {pkg.sessions_used} sessions
                          </span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl">
                          <span className="text-sm text-gray-700 font-medium">Remaining</span>
                          <span className="font-bold text-green-700 text-lg">
                            {pkg.sessions_remaining} sessions
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Purchase Price</p>
                          <p className="text-xl font-bold text-gray-900">
                            ${Number(pkg.purchase_price).toFixed(2)}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => router.push("/bookings")}
                          className="text-primary-600 hover:text-primary-700"
                        >
                          Use Credit →
                        </Button>
                      </div>

                      {pkg.expires_at && (
                        <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
                          <FiClock className="w-3 h-3" />
                          Expires: {new Date(pkg.expires_at).toLocaleDateString()}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Exhausted/Expired Packages */}
            {exhaustedPackages.length > 0 && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <FiClock className="text-gray-400" />
                  Past Packages
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {exhaustedPackages.map((pkg) => (
                    <motion.div
                      key={pkg.id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="bg-white rounded-2xl shadow-soft p-6 opacity-75"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
                            <FiPackage className="w-6 h-6 text-gray-400" />
                          </div>
                          <div>
                            <p className="font-bold text-gray-700">Package #{pkg.id}</p>
                            <p className="text-sm text-gray-500 capitalize">{pkg.status}</p>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2 mb-4">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Purchased:</span>
                          <span className="font-semibold text-gray-900">
                            {pkg.sessions_purchased} sessions
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Used:</span>
                          <span className="font-semibold text-gray-900">
                            {pkg.sessions_used} sessions
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Price:</span>
                          <span className="font-semibold text-gray-900">
                            ${Number(pkg.purchase_price).toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {myPackages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl shadow-soft p-12 text-center border-2 border-purple-100"
              >
                <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <FiPackage className="w-10 h-10 text-purple-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  No Packages Yet 📦
                </h3>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  Browse available packages from tutors and save on multi-session bundles
                </p>
                <Button
                  variant="primary"
                  onClick={() => setSelectedTab("browse")}
                  className="bg-gradient-to-r from-primary-600 to-pink-600 shadow-warm"
                >
                  Browse Packages →
                </Button>
              </motion.div>
            )}
          </div>
        )}

        {/* Browse Packages Tab */}
        {selectedTab === "browse" && (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <FiCheck className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="font-semibold text-blue-900 mb-1">How Packages Work</p>
                <p className="text-sm text-blue-700">
                  Purchase multi-session packages from tutors at discounted rates. Use credits when booking sessions to save money.
                </p>
              </div>
            </div>

            {availableTutors.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {availableTutors.map((tutor) => (
                  <motion.div
                    key={tutor.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-white rounded-2xl shadow-soft hover:shadow-lg transition-all p-6 cursor-pointer"
                    onClick={() => router.push(`/tutors/${tutor.id}`)}
                  >
                    <div className="flex items-center gap-4 mb-4">
                      {tutor.profile_photo_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={tutor.profile_photo_url}
                          alt={tutor.title}
                          className="w-16 h-16 rounded-full object-cover border-2 border-primary-100"
                        />
                      ) : (
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-100 to-pink-100 flex items-center justify-center">
                          <FiUser className="w-8 h-8 text-primary-400" />
                        </div>
                      )}
                      <div className="flex-1">
                        <h3 className="font-bold text-gray-900">{tutor.title}</h3>
                        <p className="text-sm text-gray-600">{tutor.headline}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 mb-4">
                      <div className="flex items-center gap-1 text-yellow-600">
                        <FiStar className="w-4 h-4 fill-current" />
                        <span className="font-semibold">
                          {Number(tutor.average_rating).toFixed(1)}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">
                        ({tutor.total_reviews} reviews)
                      </span>
                    </div>

                    <div className="bg-gradient-to-r from-primary-50 to-pink-50 rounded-xl p-4 mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-600">Hourly Rate</span>
                        <span className="text-2xl font-bold text-primary-600">
                          ${Number(tutor.hourly_rate).toFixed(0)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500">
                        Check tutor profile for package deals
                      </p>
                    </div>

                    <Button
                      variant="primary"
                      size="sm"
                      className="w-full"
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/tutors/${tutor.id}`);
                      }}
                    >
                      View Profile & Packages →
                    </Button>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 bg-white rounded-2xl shadow-soft">
                <p className="text-gray-600">No tutors available at the moment</p>
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
