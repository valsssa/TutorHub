import Link from 'next/link';
import {
  GraduationCap,
  Users,
  Calendar,
  Video,
  Star,
  Shield,
  Clock,
  CheckCircle,
  ArrowRight,
  BookOpen,
  MessageCircle,
  CreditCard,
} from 'lucide-react';
import { Button, ThemeToggle } from '@/components/ui';

const features = [
  {
    icon: Users,
    title: 'Expert Tutors',
    description: 'Learn from verified professionals with proven teaching experience and excellent reviews.',
  },
  {
    icon: Video,
    title: 'Live Video Sessions',
    description: 'Connect face-to-face with tutors through high-quality video calls from anywhere.',
  },
  {
    icon: Calendar,
    title: 'Flexible Scheduling',
    description: 'Book sessions that fit your schedule with easy calendar management.',
  },
  {
    icon: Shield,
    title: 'Secure Payments',
    description: 'Protected transactions with money-back guarantee if not satisfied.',
  },
  {
    icon: MessageCircle,
    title: 'Direct Messaging',
    description: 'Communicate directly with tutors before and after sessions.',
  },
  {
    icon: BookOpen,
    title: 'All Subjects',
    description: 'From math and science to languages and music - find tutors for any subject.',
  },
];

const howItWorks = [
  {
    step: 1,
    title: 'Find Your Tutor',
    description: 'Browse our curated list of expert tutors, filter by subject, price, and availability.',
  },
  {
    step: 2,
    title: 'Book a Session',
    description: 'Choose a time that works for you and book your session in just a few clicks.',
  },
  {
    step: 3,
    title: 'Learn & Grow',
    description: 'Join the video session, learn from your tutor, and track your progress.',
  },
];

/* TODO: fetch real stats from API */
const stats = [
  { value: '500+', label: 'Expert Tutors' },
  { value: '10,000+', label: 'Sessions Completed' },
  { value: '4.9', label: 'Average Rating' },
  { value: '50+', label: 'Subjects' },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-slate-950/80 backdrop-blur-lg border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <GraduationCap className="h-8 w-8 text-primary-600" />
              <span className="text-xl font-bold text-slate-900 dark:text-white">
                EduStream
              </span>
            </Link>
            <div className="flex items-center gap-2 sm:gap-4">
              <ThemeToggle />
              <Link
                href="/login"
                className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors"
              >
                Sign in
              </Link>
              <Button asChild size="sm">
                <Link href="/register">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-24 pb-12 sm:pt-32 sm:pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold text-slate-900 dark:text-white leading-tight">
              Learn from the{' '}
              <span className="text-primary-600">Best Tutors</span>
              <br />
              Anywhere, Anytime
            </h1>
            <p className="mt-4 sm:mt-6 text-base sm:text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              Connect with expert tutors for personalized 1-on-1 video sessions.
              Master any subject with guidance tailored to your learning style.
            </p>
            <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
              <Button asChild size="lg" className="w-full sm:w-auto px-8">
                <Link href="/register">
                  Start Learning Today
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="w-full sm:w-auto px-8">
                <Link href="/register?role=tutor">
                  Become a Tutor
                </Link>
              </Button>
            </div>
            <div className="mt-6 sm:mt-8 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 sm:gap-6 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1 whitespace-nowrap">
                <CheckCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-500 shrink-0" />
                Free to join
              </span>
              <span className="flex items-center gap-1 whitespace-nowrap">
                <CheckCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-500 shrink-0" />
                No subscription
              </span>
              <span className="flex items-center gap-1 whitespace-nowrap">
                <CheckCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-500 shrink-0" />
                Pay per session
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-slate-50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-primary-600">
                  {stat.value}
                </div>
                <div className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-12 sm:py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 dark:text-white">
              Everything You Need to Succeed
            </h2>
            <p className="mt-4 text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              Our platform provides all the tools for effective online tutoring
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-900/50"
              >
                <div className="w-12 h-12 rounded-xl bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-12 sm:py-20 px-4 sm:px-6 lg:px-8 bg-slate-50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 dark:text-white">
              How It Works
            </h2>
            <p className="mt-4 text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              Get started with online tutoring in three simple steps
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 sm:gap-6 lg:gap-8">
            {howItWorks.map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-primary-600 text-white text-xl sm:text-2xl font-bold flex items-center justify-center mx-auto mb-4 sm:mb-6">
                  {item.step}
                </div>
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3">
                  {item.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-400">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* For Tutors Section */}
      <section className="py-12 sm:py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl sm:rounded-3xl p-6 sm:p-8 md:p-12 lg:p-16">
            <div className="max-w-3xl">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3 sm:mb-4">
                Share Your Knowledge, Earn Money
              </h2>
              <p className="text-base sm:text-lg text-primary-100 mb-6 sm:mb-8">
                Join our community of tutors and help students achieve their goals.
                Set your own rates, create your schedule, and teach from anywhere.
              </p>
              <div className="flex flex-wrap gap-4 sm:gap-6 mb-6 sm:mb-8 text-sm sm:text-base text-white">
                <span className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Flexible hours
                </span>
                <span className="flex items-center gap-2">
                  <CreditCard className="h-5 w-5" />
                  Weekly payouts
                </span>
                <span className="flex items-center gap-2">
                  <Star className="h-5 w-5" />
                  Build your reputation
                </span>
              </div>
              <Button
                asChild
                variant="secondary"
                size="lg"
                className="bg-white text-primary-600 hover:bg-primary-50"
              >
                <Link href="/register?role=tutor">
                  Apply as a Tutor
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 sm:py-20 px-4 sm:px-6 lg:px-8 bg-slate-50 dark:bg-slate-900/50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-3 sm:mb-4">
            Ready to Start Learning?
          </h2>
          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 mb-6 sm:mb-8">
            Join thousands of students who are already achieving their goals with EduStream.
          </p>
          <Button asChild size="lg" className="px-8">
            <Link href="/register">
              Create Free Account
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8 border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 sm:gap-6">
            <div className="flex items-center gap-2">
              <GraduationCap className="h-6 w-6 text-primary-600" />
              <span className="text-lg font-bold text-slate-900 dark:text-white">
                EduStream
              </span>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-slate-600 dark:text-slate-400">
              <Link href="/login" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                Sign In
              </Link>
              <Link href="/register" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                Sign Up
              </Link>
              <Link href="/register?role=tutor" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                Become a Tutor
              </Link>
              <Link href="/privacy" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                Privacy Policy
              </Link>
              <Link href="/terms" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                Terms of Service
              </Link>
              <Link href="/contact" className="hover:text-slate-900 dark:hover:text-white transition-colors">
                Contact
              </Link>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-500">
              &copy; {new Date().getFullYear()} EduStream. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
