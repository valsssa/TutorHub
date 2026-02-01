"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  FiVideo,
  FiCheck,
  FiAlertCircle,
  FiExternalLink,
  FiInfo,
} from "react-icons/fi";
import { SiZoom, SiGooglemeet, SiMicrosoftteams } from "react-icons/si";
import SettingsCard from "@/components/settings/SettingsCard";
import Button from "@/components/Button";
import LoadingSpinner from "@/components/LoadingSpinner";
import { useToast } from "@/components/ToastContainer";
import { api } from "@/lib/api";

interface VideoProvider {
  value: string;
  label: string;
  description: string;
  requires_setup: boolean;
  is_available: boolean;
}

interface VideoSettings {
  preferred_video_provider: string;
  custom_meeting_url_template: string | null;
  video_provider_configured: boolean;
  zoom_available: boolean;
  google_calendar_connected: boolean;
}

export default function VideoSettingsPage() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<VideoSettings | null>(null);
  const [providers, setProviders] = useState<VideoProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("zoom");
  const [customUrl, setCustomUrl] = useState<string>("");
  const [userRole, setUserRole] = useState<string>("");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Get user role first
      const user = await api.get("/auth/me");
      setUserRole(user.role);

      if (user.role !== "tutor") {
        router.push("/settings");
        return;
      }

      // Load video settings and providers
      const [settingsData, providersData] = await Promise.all([
        api.get("/tutor/settings/video"),
        api.get("/tutor/settings/video/providers"),
      ]);

      setSettings(settingsData);
      setProviders(providersData.providers);
      setSelectedProvider(settingsData.preferred_video_provider);
      setCustomUrl(settingsData.custom_meeting_url_template || "");
    } catch (error) {
      showError("Failed to load video settings");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await api.put("/tutor/settings/video", {
        preferred_video_provider: selectedProvider,
        custom_meeting_url_template:
          selectedProvider === "teams" || selectedProvider === "custom"
            ? customUrl
            : null,
      });

      setSettings(response);
      showSuccess("Video settings saved successfully");
    } catch (error: any) {
      const message =
        error.response?.data?.detail || "Failed to save video settings";
      showError(message);
    } finally {
      setSaving(false);
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case "zoom":
        return <SiZoom className="w-6 h-6" />;
      case "google_meet":
        return <SiGooglemeet className="w-6 h-6" />;
      case "teams":
        return <SiMicrosoftteams className="w-6 h-6" />;
      case "custom":
        return <FiVideo className="w-6 h-6" />;
      case "manual":
        return <FiExternalLink className="w-6 h-6" />;
      default:
        return <FiVideo className="w-6 h-6" />;
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider) {
      case "zoom":
        return "text-blue-600 bg-blue-100";
      case "google_meet":
        return "text-green-600 bg-green-100";
      case "teams":
        return "text-purple-600 bg-purple-100";
      case "custom":
        return "text-orange-600 bg-orange-100";
      case "manual":
        return "text-gray-600 bg-gray-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  if (userRole !== "tutor") {
    return null;
  }

  const needsCustomUrl =
    selectedProvider === "teams" || selectedProvider === "custom";
  const canSave =
    !needsCustomUrl || (customUrl.trim() && customUrl.startsWith("http"));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          Video Meeting Settings
        </h2>
        <p className="text-slate-600">
          Choose how you want to conduct video sessions with your students
        </p>
      </div>

      {/* Current Status */}
      {settings && (
        <SettingsCard title="Current Configuration">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center ${getProviderColor(
                settings.preferred_video_provider
              )}`}
            >
              {getProviderIcon(settings.preferred_video_provider)}
            </div>
            <div className="flex-1">
              <p className="font-medium text-slate-900">
                {providers.find(
                  (p) => p.value === settings.preferred_video_provider
                )?.label || "Unknown"}
              </p>
              <p className="text-sm text-slate-500">
                {settings.video_provider_configured ? (
                  <span className="text-green-600 flex items-center gap-1">
                    <FiCheck className="w-4 h-4" /> Configured and ready
                  </span>
                ) : (
                  <span className="text-amber-600 flex items-center gap-1">
                    <FiAlertCircle className="w-4 h-4" /> Setup required
                  </span>
                )}
              </p>
            </div>
          </div>
        </SettingsCard>
      )}

      {/* Provider Selection */}
      <SettingsCard title="Select Video Provider">
        <div className="space-y-3">
          {providers.map((provider) => {
            const isSelected = selectedProvider === provider.value;
            const isDisabled = !provider.is_available;

            return (
              <button
                key={provider.value}
                onClick={() => !isDisabled && setSelectedProvider(provider.value)}
                disabled={isDisabled}
                className={`w-full p-4 rounded-xl border-2 transition-all text-left ${
                  isSelected
                    ? "border-indigo-500 bg-indigo-50"
                    : isDisabled
                    ? "border-gray-200 bg-gray-50 opacity-60 cursor-not-allowed"
                    : "border-gray-200 hover:border-indigo-300"
                }`}
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${getProviderColor(
                      provider.value
                    )}`}
                  >
                    {getProviderIcon(provider.value)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold text-slate-900">
                        {provider.label}
                      </p>
                      {provider.value === "zoom" && (
                        <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                          Recommended
                        </span>
                      )}
                      {!provider.is_available && provider.requires_setup && (
                        <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full">
                          Setup Required
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-600">
                      {provider.description}
                    </p>
                    {!provider.is_available && provider.value === "google_meet" && (
                      <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                        <FiInfo className="w-3 h-3" />
                        Connect Google Calendar in Integrations to enable
                      </p>
                    )}
                  </div>
                  {isSelected && (
                    <div className="w-6 h-6 rounded-full bg-indigo-500 flex items-center justify-center flex-shrink-0">
                      <FiCheck className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </SettingsCard>

      {/* Custom URL Input (for Teams and Custom) */}
      {needsCustomUrl && (
        <SettingsCard
          title={
            selectedProvider === "teams"
              ? "Microsoft Teams Meeting Link"
              : "Custom Meeting URL"
          }
        >
          <div className="space-y-3">
            <p className="text-sm text-slate-600">
              {selectedProvider === "teams"
                ? "Enter your personal Teams meeting room link. This will be used for all your sessions."
                : "Enter your video meeting URL. You can use placeholders like {booking_id} for dynamic URLs."}
            </p>
            <input
              type="url"
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              placeholder={
                selectedProvider === "teams"
                  ? "https://teams.microsoft.com/l/meetup-join/..."
                  : "https://meet.jit.si/my-room or https://whereby.com/my-room"
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            {selectedProvider === "custom" && (
              <p className="text-xs text-slate-500">
                Supported placeholders: {"{booking_id}"}, {"{date}"}, {"{time}"}
              </p>
            )}
          </div>
        </SettingsCard>
      )}

      {/* Google Calendar Connection Notice */}
      {selectedProvider === "google_meet" &&
        settings &&
        !settings.google_calendar_connected && (
          <SettingsCard title="Google Calendar Required">
            <div className="flex items-start gap-3 p-4 bg-amber-50 rounded-xl border border-amber-200">
              <FiAlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-amber-800 font-medium mb-1">
                  Google Calendar connection required
                </p>
                <p className="text-sm text-amber-700 mb-3">
                  To use Google Meet, you need to connect your Google Calendar
                  first.
                </p>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => router.push("/settings/integrations")}
                >
                  Go to Integrations
                </Button>
              </div>
            </div>
          </SettingsCard>
        )}

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={saving || !canSave}
          className="min-w-[120px]"
        >
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </div>

      {/* Info Box */}
      <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
        <div className="flex items-start gap-3">
          <FiInfo className="w-5 h-5 text-slate-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-slate-600">
            <p className="font-medium text-slate-700 mb-1">
              How video meetings work
            </p>
            <ul className="space-y-1 text-slate-600">
              <li>
                When you confirm a booking, a meeting link is automatically
                generated
              </li>
              <li>
                Students will see the meeting link on their booking details page
              </li>
              <li>
                You can regenerate the meeting link if there are any issues
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
