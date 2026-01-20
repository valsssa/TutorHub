'use client'

import Link from 'next/link'
import { FiBook, FiHeart } from 'react-icons/fi'

export default function Footer() {
  return (
    <footer className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 pt-16 pb-8 transition-colors duration-200 mt-auto">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 mb-16">
          {/* Brand Column */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-2 cursor-pointer">
              <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
                <FiBook className="text-white w-5 h-5" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-700 dark:from-emerald-400 dark:to-emerald-600 bg-clip-text text-transparent">
                EduConnect
              </span>
            </Link>
            <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed max-w-xs">
              Connecting students with elite educators for personalized 1-on-1 learning. Master any subject, anytime, anywhere.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="font-bold text-slate-900 dark:text-white mb-6">Product</h4>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/tutors" className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Find a Tutor
                </Link>
              </li>
              <li>
                <Link href="/referral" className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Refer a friend
                </Link>
              </li>
              <li>
                <Link href="/affiliate-program" className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Affiliate Program
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="font-bold text-slate-900 dark:text-white mb-6">Support</h4>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/support" className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Help Center
                </Link>
              </li>
            </ul>
          </div>

          {/* For Tutors */}
          <div>
            <h4 className="font-bold text-slate-900 dark:text-white mb-6">For Tutors</h4>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/tutor/onboarding" className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Become a Tutor
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-bold text-slate-900 dark:text-white mb-6">Legal</h4>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/settings/privacy" className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/cookie-policy" className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Cookie Policy
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-100 dark:border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-slate-500 dark:text-slate-500 text-sm flex items-center gap-1">
            © {new Date().getFullYear()} EduConnect Inc. Made with{' '}
            <FiHeart className="w-3 h-3 text-red-500 fill-current" /> globally.
          </p>
          <div className="flex gap-6 text-sm font-medium">
            <Link href="/settings/privacy" className="text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">
              Privacy
            </Link>
            <Link href="/terms" className="text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">
              Terms
            </Link>
            <Link href="/cookie-policy" className="text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">
              Cookies
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
