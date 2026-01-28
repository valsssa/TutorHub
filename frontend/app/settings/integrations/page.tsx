"use client";

import SettingsCard from "@/components/settings/SettingsCard";
import Button from "@/components/Button";

export default function IntegrationsPage() {
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

      {/* Calendar */}
      <SettingsCard title="📅 Google Calendar">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-600 mb-1">
              Sync your lessons with Google Calendar
            </p>
            <p className="text-xs text-slate-500">Coming soon</p>
          </div>
          <Button variant="secondary" disabled>
            Connect
          </Button>
        </div>
      </SettingsCard>
    </div>
  );
}
