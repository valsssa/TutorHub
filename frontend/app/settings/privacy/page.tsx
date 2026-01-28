"use client";

import { FiEye, FiDownload, FiShield } from "react-icons/fi";
import SettingsCard from "@/components/settings/SettingsCard";
import Button from "@/components/Button";
import Toggle from "@/components/settings/Toggle";
import { useState } from "react";

export default function PrivacyPage() {
  const [settings, setSettings] = useState({
    profilePublic: true,
    showLocation: false,
    shareActivity: true,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          🔒 Privacy & Security
        </h2>
        <p className="text-slate-600">
          Stay in control of your data
        </p>
      </div>

      {/* Profile Visibility */}
      <SettingsCard
        title="Profile Visibility"
        description="Control who can see your profile"
      >
        <div className="space-y-3">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="font-medium text-slate-900">Public Profile</span>
              <input
                type="radio"
                name="visibility"
                checked={settings.profilePublic}
                onChange={() => setSettings({ ...settings, profilePublic: true })}
                className="w-4 h-4 text-sky-600"
              />
            </label>
            <p className="text-xs text-slate-500 mt-1 ml-6">
              Anyone can view your profile
            </p>
          </div>
          
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="font-medium text-slate-900">Logged-in Users Only</span>
              <input
                type="radio"
                name="visibility"
                checked={!settings.profilePublic}
                onChange={() => setSettings({ ...settings, profilePublic: false })}
                className="w-4 h-4 text-sky-600"
              />
            </label>
            <p className="text-xs text-slate-500 mt-1 ml-6">
              Only registered users can see your profile
            </p>
          </div>

          <div className="border-t border-slate-100 pt-3 mt-3">
            <Toggle
              enabled={settings.showLocation}
              onChange={(val) => setSettings({ ...settings, showLocation: val })}
              label="Show Location"
              description="Display your country on your profile"
            />
          </div>
        </div>
      </SettingsCard>

      {/* Data & Privacy */}
      <SettingsCard
        title="Your Data"
        description="Manage your personal information"
      >
        <div className="space-y-3">
          <Button
            variant="secondary"
            className="w-full flex items-center justify-center gap-2"
          >
            <FiDownload className="w-4 h-4" />
            Download My Data
          </Button>
          <p className="text-xs text-slate-500 text-center">
            Get a copy of all your data in JSON format
          </p>
        </div>
      </SettingsCard>

      {/* Cookie Preferences */}
      <SettingsCard
        title="Cookie Preferences"
        description="Manage how we use cookies"
      >
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
            <span className="text-2xl">🍪</span>
            <div>
              <p className="font-medium text-slate-900 mb-1">Essential Cookies</p>
              <p className="text-xs text-slate-600">
                Required for the platform to function. Cannot be disabled.
              </p>
            </div>
          </div>

          <Toggle
            enabled={settings.shareActivity}
            onChange={(val) => setSettings({ ...settings, shareActivity: val })}
            label="Analytics Cookies"
            description="Help us improve by sharing anonymous usage data"
          />
        </div>
      </SettingsCard>

      {/* Security */}
      <SettingsCard
        title="Security"
        description="Your data is encrypted and secure"
      >
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start gap-3">
            <FiShield className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <p className="font-medium text-green-900 mb-1">Your data is protected</p>
              <ul className="text-sm text-green-800 space-y-1">
                <li>✓ End-to-end encryption</li>
                <li>✓ GDPR compliant</li>
                <li>✓ Regular security audits</li>
                <li>✓ No data sold to third parties</li>
              </ul>
            </div>
          </div>
        </div>
      </SettingsCard>

      {/* Privacy Policy */}
      <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl">
        <p className="text-sm text-slate-700">
          Learn more about how we protect your data in our{" "}
          <a href="/privacy-policy" className="text-sky-600 hover:underline font-medium">
            Privacy Policy
          </a>{" "}
          and{" "}
          <a href="/terms" className="text-sky-600 hover:underline font-medium">
            Terms of Service
          </a>
          .
        </p>
      </div>
    </div>
  );
}
