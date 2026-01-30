"use client";

import { useState } from "react";
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
  Mail,
  MessageCircle,
  Phone,
  ExternalLink,
} from "lucide-react";
import Breadcrumb from "@/components/Breadcrumb";
import Button from "@/components/Button";

interface HelpCategory {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
  color: string;
  articles: number;
}

interface PopularArticle {
  id: string;
  title: string;
  category: string;
  views: number;
}

const CATEGORIES: HelpCategory[] = [
  {
    id: "getting-started",
    title: "Getting Started",
    description: "Learn the basics of using EduConnect",
    icon: BookOpen,
    color: "bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400",
    articles: 12,
  },
  {
    id: "bookings",
    title: "Bookings & Sessions",
    description: "How to book, reschedule, and manage sessions",
    icon: Calendar,
    color: "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400",
    articles: 18,
  },
  {
    id: "payments",
    title: "Payments & Billing",
    description: "Payment methods, refunds, and invoices",
    icon: CreditCard,
    color: "bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400",
    articles: 15,
  },
  {
    id: "messaging",
    title: "Messaging",
    description: "Communicate with tutors and students",
    icon: MessageSquare,
    color: "bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400",
    articles: 8,
  },
  {
    id: "account",
    title: "Account & Profile",
    description: "Manage your account settings and profile",
    icon: User,
    color: "bg-cyan-100 dark:bg-cyan-900/30 text-cyan-600 dark:text-cyan-400",
    articles: 10,
  },
  {
    id: "tutors",
    title: "For Tutors",
    description: "Tutor-specific guides and resources",
    icon: Settings,
    color: "bg-rose-100 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400",
    articles: 22,
  },
  {
    id: "safety",
    title: "Safety & Privacy",
    description: "Stay safe and protect your information",
    icon: Shield,
    color: "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400",
    articles: 7,
  },
  {
    id: "disputes",
    title: "Disputes & Issues",
    description: "Resolve problems and file disputes",
    icon: HelpCircle,
    color: "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400",
    articles: 9,
  },
];

const POPULAR_ARTICLES: PopularArticle[] = [
  { id: "book-first-session", title: "How to book your first session", category: "getting-started", views: 12500 },
  { id: "cancel-booking", title: "How to cancel or reschedule a booking", category: "bookings", views: 9800 },
  { id: "payment-methods", title: "Accepted payment methods", category: "payments", views: 8200 },
  { id: "refund-policy", title: "Understanding our refund policy", category: "payments", views: 7500 },
  { id: "become-tutor", title: "How to become a tutor", category: "tutors", views: 6800 },
  { id: "file-dispute", title: "How to file a dispute", category: "disputes", views: 5200 },
];

export default function HelpCenterPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // In a real app, this would navigate to search results
      window.location.href = `/help/search?q=${encodeURIComponent(searchQuery)}`;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <Breadcrumb items={[{ label: "Help Center" }]} />
        </div>
      </div>

      {/* Hero Section */}
      <div className="bg-gradient-to-br from-emerald-600 to-teal-700 dark:from-emerald-900 dark:to-teal-950">
        <div className="container mx-auto px-4 py-16 text-center">
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            How can we help you?
          </h1>
          <p className="text-emerald-100 text-lg mb-8 max-w-2xl mx-auto">
            Search our help center or browse categories below to find answers to your questions.
          </p>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="max-w-2xl mx-auto">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for articles..."
                className="w-full pl-12 pr-4 py-4 bg-white dark:bg-slate-800 border-none rounded-xl text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-4 focus:ring-emerald-500/30 focus:outline-none shadow-lg"
              />
              <Button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2">
                Search
              </Button>
            </div>
          </form>
        </div>
      </div>

      <div className="container mx-auto px-4 py-12 max-w-6xl">
        {/* Categories Grid */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
            Browse by Category
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {CATEGORIES.map((category) => (
              <Link
                key={category.id}
                href={`/help/${category.id}`}
                className="group bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 hover:border-emerald-500 dark:hover:border-emerald-500 hover:shadow-lg transition-all"
              >
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${category.color}`}
                >
                  <category.icon className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-slate-900 dark:text-white mb-1 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                  {category.title}
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">
                  {category.description}
                </p>
                <span className="text-xs text-slate-400 dark:text-slate-500">
                  {category.articles} articles
                </span>
              </Link>
            ))}
          </div>
        </section>

        {/* Popular Articles */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
            Popular Articles
          </h2>

          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 divide-y divide-slate-100 dark:divide-slate-800">
            {POPULAR_ARTICLES.map((article) => (
              <Link
                key={article.id}
                href={`/help/${article.category}/${article.id}`}
                className="flex items-center justify-between p-5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/30 transition-colors">
                    <BookOpen className="w-5 h-5 text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                      {article.title}
                    </p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {CATEGORIES.find((c) => c.id === article.category)?.title}
                    </p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-emerald-500 transition-colors" />
              </Link>
            ))}
          </div>
        </section>

        {/* Contact Support */}
        <section>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
            Still need help?
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Email Support */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 text-center">
              <div className="w-14 h-14 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mx-auto mb-4">
                <Mail className="w-7 h-7 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="font-bold text-slate-900 dark:text-white mb-2">
                Email Support
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                Get a response within 24 hours
              </p>
              <a
                href="mailto:support@educonnect.com"
                className="text-emerald-600 hover:text-emerald-500 dark:text-emerald-400 font-medium text-sm"
              >
                support@educonnect.com
              </a>
            </div>

            {/* Live Chat */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 text-center">
              <div className="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="w-7 h-7 text-emerald-600 dark:text-emerald-400" />
              </div>
              <h3 className="font-bold text-slate-900 dark:text-white mb-2">
                Live Chat
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                Available Mon-Fri, 9am-6pm EST
              </p>
              <Button size="sm">Start Chat</Button>
            </div>

            {/* Community */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 text-center">
              <div className="w-14 h-14 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mx-auto mb-4">
                <User className="w-7 h-7 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="font-bold text-slate-900 dark:text-white mb-2">
                Community Forum
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                Connect with other users
              </p>
              <a
                href="#"
                className="inline-flex items-center gap-1 text-emerald-600 hover:text-emerald-500 dark:text-emerald-400 font-medium text-sm"
              >
                Visit Forum
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
