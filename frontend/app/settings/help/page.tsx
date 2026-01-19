"use client";

import { FiMessageSquare, FiBook, FiClock, FiMail, FiExternalLink } from "react-icons/fi";
import SettingsCard from "@/components/settings/SettingsCard";
import Button from "@/components/Button";

export default function HelpPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          💬 Help & Support
        </h2>
        <p className="text-slate-600">
          We&apos;re here to help 24/7 🧡
        </p>
      </div>

      {/* Contact Support */}
      <SettingsCard title="Contact Support">
        <div className="space-y-4">
          <div className="flex items-start gap-4 p-4 bg-gradient-to-br from-sky-50 to-blue-50 rounded-xl border border-sky-100">
            <FiMessageSquare className="w-6 h-6 text-sky-600 mt-1" />
            <div className="flex-1">
              <h4 className="font-semibold text-slate-900 mb-1">Live Chat</h4>
              <p className="text-sm text-slate-600 mb-3">
                Get instant help from our support team
              </p>
              <Button variant="primary" className="bg-sky-600 hover:bg-sky-700">
                Start Chat
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
              <FiMail className="w-5 h-5 text-slate-600 mb-2" />
              <h4 className="font-semibold text-slate-900 mb-1">Email Us</h4>
              <p className="text-sm text-slate-600 mb-2">support@tutorconnect.com</p>
              <p className="text-xs text-slate-500">Response within 24 hours</p>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
              <FiClock className="w-5 h-5 text-slate-600 mb-2" />
              <h4 className="font-semibold text-slate-900 mb-1">Response Time</h4>
              <p className="text-sm text-green-600 font-medium mb-2">~5 minutes</p>
              <p className="text-xs text-slate-500">Average response time</p>
            </div>
          </div>
        </div>
      </SettingsCard>

      {/* Resources */}
      <SettingsCard title="Help Resources">
        <div className="space-y-3">
          <a
            href="/help/getting-started"
            className="flex items-center justify-between p-3 hover:bg-slate-50 rounded-lg transition-colors group"
          >
            <div className="flex items-center gap-3">
              <FiBook className="w-5 h-5 text-slate-400 group-hover:text-sky-600" />
              <div>
                <p className="font-medium text-slate-900">Getting Started Guide</p>
                <p className="text-xs text-slate-500">Learn the basics</p>
              </div>
            </div>
            <FiExternalLink className="w-4 h-4 text-slate-400" />
          </a>

          <a
            href="/help/faq"
            className="flex items-center justify-between p-3 hover:bg-slate-50 rounded-lg transition-colors group"
          >
            <div className="flex items-center gap-3">
              <FiBook className="w-5 h-5 text-slate-400 group-hover:text-sky-600" />
              <div>
                <p className="font-medium text-slate-900">FAQs</p>
                <p className="text-xs text-slate-500">Frequently asked questions</p>
              </div>
            </div>
            <FiExternalLink className="w-4 h-4 text-slate-400" />
          </a>

          <a
            href="/help/community"
            className="flex items-center justify-between p-3 hover:bg-slate-50 rounded-lg transition-colors group"
          >
            <div className="flex items-center gap-3">
              <FiBook className="w-5 h-5 text-slate-400 group-hover:text-sky-600" />
              <div>
                <p className="font-medium text-slate-900">Community Forum</p>
                <p className="text-xs text-slate-500">Connect with other users</p>
              </div>
            </div>
            <FiExternalLink className="w-4 h-4 text-slate-400" />
          </a>
        </div>
      </SettingsCard>

      {/* Feedback */}
      <SettingsCard title="Share Your Feedback">
        <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl border border-purple-100">
          <p className="text-sm text-purple-900 mb-3">
            Help us improve! Share your thoughts and suggestions.
          </p>
          <Button variant="secondary" className="border-purple-300 text-purple-700 hover:bg-purple-50">
            Send Feedback
          </Button>
        </div>
      </SettingsCard>
    </div>
  );
}
