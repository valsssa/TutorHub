"use client";

import { useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Search,
  BookOpen,
  CreditCard,
  Calendar,
  MessageSquare,
  User,
  Settings,
  Shield,
  HelpCircle,
  ChevronRight,
  ArrowLeft,
} from "lucide-react";
import Breadcrumb from "@/components/Breadcrumb";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";

interface Article {
  id: string;
  title: string;
  description: string;
  updated: string;
}

interface CategoryData {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
  articles: Article[];
}

const CATEGORIES_DATA: Record<string, CategoryData> = {
  "getting-started": {
    id: "getting-started",
    title: "Getting Started",
    description: "Learn the basics of using EduConnect",
    icon: BookOpen,
    articles: [
      {
        id: "create-account",
        title: "How to create an account",
        description: "Step-by-step guide to creating your EduConnect account",
        updated: "2026-01-15",
      },
      {
        id: "book-first-session",
        title: "How to book your first session",
        description: "Learn how to find a tutor and book your first lesson",
        updated: "2026-01-20",
      },
      {
        id: "profile-setup",
        title: "Setting up your profile",
        description: "Complete your profile to get the most out of EduConnect",
        updated: "2026-01-10",
      },
      {
        id: "find-tutor",
        title: "How to find the right tutor",
        description: "Tips for finding a tutor that matches your learning needs",
        updated: "2026-01-18",
      },
    ],
  },
  bookings: {
    id: "bookings",
    title: "Bookings & Sessions",
    description: "How to book, reschedule, and manage sessions",
    icon: Calendar,
    articles: [
      {
        id: "book-session",
        title: "How to book a session",
        description: "Complete guide to booking a tutoring session",
        updated: "2026-01-22",
      },
      {
        id: "cancel-booking",
        title: "How to cancel or reschedule a booking",
        description: "Learn about our cancellation policy and how to reschedule",
        updated: "2026-01-25",
      },
      {
        id: "join-session",
        title: "How to join a video session",
        description: "Technical guide for joining your online tutoring session",
        updated: "2026-01-20",
      },
      {
        id: "session-types",
        title: "Types of sessions available",
        description: "Understand the different session formats we offer",
        updated: "2026-01-15",
      },
    ],
  },
  payments: {
    id: "payments",
    title: "Payments & Billing",
    description: "Payment methods, refunds, and invoices",
    icon: CreditCard,
    articles: [
      {
        id: "payment-methods",
        title: "Accepted payment methods",
        description: "Learn about all the ways you can pay for sessions",
        updated: "2026-01-20",
      },
      {
        id: "refund-policy",
        title: "Understanding our refund policy",
        description: "When and how you can request a refund",
        updated: "2026-01-18",
      },
      {
        id: "view-receipts",
        title: "How to view and download receipts",
        description: "Access your payment history and download invoices",
        updated: "2026-01-12",
      },
      {
        id: "payment-failed",
        title: "What to do if payment fails",
        description: "Troubleshooting payment issues",
        updated: "2026-01-10",
      },
    ],
  },
  messaging: {
    id: "messaging",
    title: "Messaging",
    description: "Communicate with tutors and students",
    icon: MessageSquare,
    articles: [
      {
        id: "send-message",
        title: "How to send a message",
        description: "Learn how to communicate with tutors before booking",
        updated: "2026-01-15",
      },
      {
        id: "message-guidelines",
        title: "Messaging guidelines",
        description: "Best practices for communicating on the platform",
        updated: "2026-01-10",
      },
    ],
  },
  account: {
    id: "account",
    title: "Account & Profile",
    description: "Manage your account settings and profile",
    icon: User,
    articles: [
      {
        id: "update-profile",
        title: "How to update your profile",
        description: "Change your profile picture, bio, and other details",
        updated: "2026-01-20",
      },
      {
        id: "change-password",
        title: "How to change your password",
        description: "Keep your account secure with a strong password",
        updated: "2026-01-18",
      },
      {
        id: "delete-account",
        title: "How to delete your account",
        description: "Understand what happens when you delete your account",
        updated: "2026-01-15",
      },
    ],
  },
  tutors: {
    id: "tutors",
    title: "For Tutors",
    description: "Tutor-specific guides and resources",
    icon: Settings,
    articles: [
      {
        id: "become-tutor",
        title: "How to become a tutor",
        description: "Complete guide to joining as a tutor on EduConnect",
        updated: "2026-01-25",
      },
      {
        id: "set-availability",
        title: "Setting your availability",
        description: "Learn how to manage your teaching schedule",
        updated: "2026-01-22",
      },
      {
        id: "set-pricing",
        title: "How to set your pricing",
        description: "Guide to pricing your tutoring services",
        updated: "2026-01-20",
      },
      {
        id: "tutor-payouts",
        title: "Understanding payouts",
        description: "How and when you get paid for your sessions",
        updated: "2026-01-18",
      },
    ],
  },
  safety: {
    id: "safety",
    title: "Safety & Privacy",
    description: "Stay safe and protect your information",
    icon: Shield,
    articles: [
      {
        id: "privacy-policy",
        title: "Privacy policy overview",
        description: "How we protect and use your data",
        updated: "2026-01-15",
      },
      {
        id: "safety-tips",
        title: "Safety tips for online learning",
        description: "Best practices for staying safe on the platform",
        updated: "2026-01-10",
      },
    ],
  },
  disputes: {
    id: "disputes",
    title: "Disputes & Issues",
    description: "Resolve problems and file disputes",
    icon: HelpCircle,
    articles: [
      {
        id: "file-dispute",
        title: "How to file a dispute",
        description: "Step-by-step guide to filing a dispute",
        updated: "2026-01-22",
      },
      {
        id: "dispute-resolution",
        title: "Understanding the dispute process",
        description: "What happens after you file a dispute",
        updated: "2026-01-20",
      },
      {
        id: "report-issue",
        title: "How to report an issue",
        description: "Report problems with sessions or users",
        updated: "2026-01-15",
      },
    ],
  },
};

export default function HelpCategoryPage() {
  const params = useParams();
  const categoryId = params?.category as string;

  const category = useMemo(() => {
    return CATEGORIES_DATA[categoryId];
  }, [categoryId]);

  if (!category) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
        <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
          <div className="container mx-auto px-4 py-4">
            <Breadcrumb
              items={[
                { label: "Help Center", href: "/help" },
                { label: "Not Found" },
              ]}
            />
          </div>
        </div>
        <div className="container mx-auto px-4 py-16 max-w-2xl">
          <EmptyState
            variant="error"
            title="Category not found"
            description="The help category you're looking for doesn't exist."
            action={{
              label: "Back to Help Center",
              href: "/help",
            }}
          />
        </div>
      </div>
    );
  }

  const Icon = category.icon;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <Breadcrumb
            items={[
              { label: "Help Center", href: "/help" },
              { label: category.title },
            ]}
          />
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Back Link */}
        <Link
          href="/help"
          className="inline-flex items-center gap-2 text-slate-600 hover:text-emerald-600 dark:text-slate-400 dark:hover:text-emerald-400 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Help Center
        </Link>

        {/* Category Header */}
        <div className="flex items-start gap-4 mb-8">
          <div className="w-14 h-14 rounded-2xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
            <Icon className="w-7 h-7 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
              {category.title}
            </h1>
            <p className="text-slate-500 dark:text-slate-400">
              {category.description}
            </p>
          </div>
        </div>

        {/* Articles List */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 divide-y divide-slate-100 dark:divide-slate-800">
          {category.articles.map((article) => (
            <Link
              key={article.id}
              href={`/help/${categoryId}/${article.id}`}
              className="flex items-center justify-between p-5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group"
            >
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center shrink-0 group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/30 transition-colors">
                  <BookOpen className="w-5 h-5 text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors" />
                </div>
                <div>
                  <h3 className="font-medium text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                    {article.title}
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                    {article.description}
                  </p>
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-2">
                    Updated {new Date(article.updated).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-emerald-500 transition-colors shrink-0" />
            </Link>
          ))}
        </div>

        {/* Still need help */}
        <div className="mt-8 bg-slate-100 dark:bg-slate-800/50 rounded-2xl p-6 text-center">
          <p className="text-slate-600 dark:text-slate-400 mb-4">
            Can't find what you're looking for?
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/help">
              <Button variant="secondary">Search Help Center</Button>
            </Link>
            <a href="mailto:support@educonnect.com">
              <Button>Contact Support</Button>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
