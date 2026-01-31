"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  FiCheck,
  FiX,
  FiExternalLink,
  FiLoader,
} from "react-icons/fi";
import { SiZoom, SiGooglemeet } from "react-icons/si";
import SettingsCard from "@/components/settings/SettingsCard";
import Button from "@/components/Button";
import { useToast } from "@/components/ToastContainer";
import { api } from "@/lib/api";

interface ZoomStatus {
  is_connected: boolean;
  zoom_email: string | null;
  connected_at: string | null;
}

interface CalendarStatus {
  is_connected: boolean;
  calendar_email: string | null;
  connected_at: string | null;
  can_create_events: boolean;
}

export default function IntegrationsPage() {
  const searchParams = useSearchParams();
  const { showSuccess, showError, showInfo } = useToast();
  const [loading, setLoading] = useState(true);
  const [zoomStatus, setZoomStatus] = useState<ZoomStatus | null>(null);
  const [calendarStatus, setCalendarStatus] = useState<CalendarStatus | null>(null);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [disconnecting, setDisconnecting] = useState<string | null>(null);

  useEffect(() => {
    loadStatuses();
  }, []);

  // Handle callback parameters
  useEffect(() => {
    const calendar = searchParams.get("calendar");
    const error = searchParams.get("error");

    if (calendar === "connected") {
      showSuccess("Google Calendar connected successfully");
      loadStatuses();
    } else if (error === "invalid_state") {
      showError("Connection failed: Invalid state. Please try again.");
    } else if (error === "no_refresh_token") {
      showError("Connection failed: Could not get refresh token. Please try again.");
    } else if (error === "oauth_error") {
      showError("Connection failed: OAuth error. Please try again.");
    } else if (error) {
      showError(`Connection failed: ${error}`);
    }
  }, [searchParams, showSuccess, showError]);

  const loadStatuses = async () => {
    try {
      const [zoomRes, calendarRes] = await Promise.all([
        api.get("/integrations/zoom/status").catch(() => null),
        api.get("/integrations/calendar/status").catch(() => null),
      ]);

      setZoomStatus(zoomRes);
      setCalendarStatus(calendarRes);
    } catch (error) {
      console.error("Failed to load integration statuses:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectCalendar = async () => {
    setConnecting("calendar");
    try {
      const response = await api.get("/integrations/calendar/connect");
      if (response.authorization_url) {
        window.location.href = response.authorization_url;
      }
    } catch (error: any) {
      showError(error.response?.data?.detail || "Failed to start calendar connection");
      setConnecting(null);
    }
  };

  const handleDisconnectCalendar = async () => {
    setDisconnecting("calendar");
    try {
      await api.delete("/integrations/calendar/disconnect");
      showSuccess("Google Calendar disconnected");
      setCalendarStatus({
        is_connected: false,
        calendar_email: null,
        connected_at: null,
        can_create_events: false,
      });
    } catch (error: any) {
      showError(error.response?.data?.detail || "Failed to disconnect calendar");
    } finally {
      setDisconnecting(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          Integrations
        </h2>
        <p className="text-slate-600">
          Connect your favorite tools and services
        </p>
      </div>

      {/* Zoom Integration */}
      <SettingsCard title="Zoom">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
            <SiZoom className="w-7 h-7 text-blue-600" />
          </div>
          <div className="flex-1">
            <p className="font-medium text-slate-900 mb-1">Zoom Meetings</p>
            {loading ? (
              <p className="text-sm text-slate-500">Checking status...</p>
            ) : zoomStatus?.is_connected ? (
              <p className="text-sm text-green-600 flex items-center gap-1">
                <FiCheck className="w-4 h-4" />
                Platform-level integration active
              </p>
            ) : (
              <p className="text-sm text-slate-500">
                Zoom meetings are automatically created for bookings
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {zoomStatus?.is_connected && (
              <span className="px-3 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">
                Active
              </span>
            )}
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-3">
          Zoom integration is handled at the platform level. Meeting links are automatically generated when bookings are confirmed.
        </p>
      </SettingsCard>

      {/* Google Calendar Integration */}
      <SettingsCard title="Google Calendar">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
            <SiGooglemeet className="w-7 h-7 text-green-600" />
          </div>
          <div className="flex-1">
            <p className="font-medium text-slate-900 mb-1">Google Calendar</p>
            {loading ? (
              <p className="text-sm text-slate-500">Checking status...</p>
            ) : calendarStatus?.is_connected ? (
              <div>
                <p className="text-sm text-green-600 flex items-center gap-1">
                  <FiCheck className="w-4 h-4" />
                  Connected as {calendarStatus.calendar_email}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Enables Google Meet links and calendar sync
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                Sync bookings to your calendar and enable Google Meet
              </p>
            )}
          </div>
          <div>
            {calendarStatus?.is_connected ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={handleDisconnectCalendar}
                disabled={disconnecting === "calendar"}
              >
                {disconnecting === "calendar" ? (
                  <span className="flex items-center gap-2">
                    <FiLoader className="w-4 h-4 animate-spin" />
                    Disconnecting...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <FiX className="w-4 h-4" />
                    Disconnect
                  </span>
                )}
              </Button>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={handleConnectCalendar}
                disabled={connecting === "calendar"}
              >
                {connecting === "calendar" ? (
                  <span className="flex items-center gap-2">
                    <FiLoader className="w-4 h-4 animate-spin" />
                    Connecting...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <FiExternalLink className="w-4 h-4" />
                    Connect
                  </span>
                )}
              </Button>
            )}
          </div>
        </div>
        {calendarStatus?.is_connected && (
          <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
            <p className="text-sm text-green-800">
              <strong>Features enabled:</strong>
            </p>
            <ul className="text-sm text-green-700 mt-1 space-y-1">
              <li>Automatic booking sync to your calendar</li>
              <li>External calendar conflict detection</li>
              <li>Google Meet link generation (if selected as video provider)</li>
            </ul>
          </div>
        )}
      </SettingsCard>

      {/* Future Integrations */}
      <SettingsCard title="More Integrations">
        <div className="text-center py-6">
          <p className="text-slate-500 mb-2">More integrations coming soon</p>
          <p className="text-xs text-slate-400">
            Microsoft Outlook, Stripe Express, and more
          </p>
        </div>
      </SettingsCard>
    </div>
  );
}
