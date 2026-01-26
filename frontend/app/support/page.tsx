"use client";

import { FiBook, FiClock, FiMail, FiExternalLink } from "react-icons/fi";
import Button from "@/components/Button";
import PageLayout from "@/components/PageLayout";

export default function SupportPage() {
  return (
    <PageLayout showHeader={true} showFooter={true}>
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        <div className="space-y-6">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white mb-2">
              💬 Help & Support
            </h1>
            <p className="text-slate-600 dark:text-slate-400 text-lg">
              We&apos;re here to help 24/7 🧡
            </p>
          </div>

          {/* Contact Support */}
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Contact Support</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700">
                    <FiMail className="w-5 h-5 text-slate-600 dark:text-slate-400 mb-2" />
                    <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Email Us</h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">suppot@valsa.solutions</p>
                    <p className="text-xs text-slate-500 dark:text-slate-500">Response within 24 hours</p>
                  </div>

                  <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700">
                    <FiClock className="w-5 h-5 text-slate-600 dark:text-slate-400 mb-2" />
                    <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Response Time</h4>
                    <p className="text-sm text-green-600 dark:text-green-400 font-medium mb-2">~5 minutes</p>
                    <p className="text-xs text-slate-500 dark:text-slate-500">Average response time</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Resources */}
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Help Resources</h3>
              <div className="space-y-3">
                <a
                  href="/help/getting-started"
                  className="flex items-center justify-between p-3 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <FiBook className="w-5 h-5 text-slate-400 group-hover:text-sky-600 dark:group-hover:text-sky-400" />
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">Getting Started Guide</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">Learn the basics</p>
                    </div>
                  </div>
                  <FiExternalLink className="w-4 h-4 text-slate-400" />
                </a>

                <a
                  href="/help/faq"
                  className="flex items-center justify-between p-3 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <FiBook className="w-5 h-5 text-slate-400 group-hover:text-sky-600 dark:group-hover:text-sky-400" />
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">FAQs</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">Frequently asked questions</p>
                    </div>
                  </div>
                  <FiExternalLink className="w-4 h-4 text-slate-400" />
                </a>

                <a
                  href="/help/community"
                  className="flex items-center justify-between p-3 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <FiBook className="w-5 h-5 text-slate-400 group-hover:text-sky-600 dark:group-hover:text-sky-400" />
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">Community Forum</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">Connect with other users</p>
                    </div>
                  </div>
                  <FiExternalLink className="w-4 h-4 text-slate-400" />
                </a>
              </div>
            </div>
          </div>

          {/* Feedback */}
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Share Your Feedback</h3>
              <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl border border-purple-100 dark:border-purple-800">
                <p className="text-sm text-purple-900 dark:text-purple-200 mb-3">
                  Help us improve! Share your thoughts and suggestions.
                </p>
                <Button variant="secondary" className="border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/30">
                  Send Feedback
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
