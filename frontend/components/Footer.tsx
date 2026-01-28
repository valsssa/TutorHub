'use client'

import Link from 'next/link'
import { FiBook, FiHeart } from 'react-icons/fi'

export default function Footer() {
  return (
    <footer className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 pt-6 pb-4 sm:pt-8 sm:pb-6 transition-colors duration-200 mt-auto">
      <div className="container mx-auto px-4 sm:px-6 max-w-7xl">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8 mb-6 sm:mb-8">
          {/* Brand Column */}
          <div className="space-y-3 text-center sm:text-left">
            <Link href="/" className="flex items-center gap-2 cursor-pointer justify-center sm:justify-start">
              <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
                <FiBook className="text-white w-5 h-5" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-700 dark:from-emerald-400 dark:to-emerald-600 bg-clip-text text-transparent">
                EduConnect
              </span>
            </Link>
            <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed mx-auto sm:mx-0 max-w-xs">
              Connecting students with elite educators for personalized 1-on-1 learning. Master any subject, anytime, anywhere.
            </p>
          </div>

          {/* Product */}
          <div className="text-center sm:text-left">
            <h4 className="font-bold text-slate-900 dark:text-white mb-3 sm:mb-4 text-base">Product</h4>
            <ul className="space-y-2.5 sm:space-y-2 text-sm sm:text-base">
              <li>
                <Link href="/tutors" className="inline-block py-1 text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Find a Tutor
                </Link>
              </li>
              <li>
                <Link href="/referral" className="inline-block py-1 text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Refer a friend
                </Link>
              </li>
              <li>
                <Link href="/affiliate-program" className="inline-block py-1 text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Affiliate Program
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div className="text-center sm:text-left">
            <h4 className="font-bold text-slate-900 dark:text-white mb-3 sm:mb-4 text-base">Support</h4>
            <ul className="space-y-2.5 sm:space-y-2 text-sm sm:text-base">
              <li>
                <Link href="/support" className="inline-block py-1 text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Help & Support
                </Link>
              </li>
            </ul>
          </div>

          {/* For Tutors */}
          <div className="text-center sm:text-left">
            <h4 className="font-bold text-slate-900 dark:text-white mb-3 sm:mb-4 text-base">For Tutors</h4>
            <ul className="space-y-2.5 sm:space-y-2 text-sm sm:text-base">
              <li>
                <Link href="/become-a-tutor" className="inline-block py-1 text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
                  Become a Tutor
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-col md:flex-row justify-between items-center gap-3 sm:gap-4">
          <p className="text-slate-500 dark:text-slate-500 text-xs sm:text-sm flex flex-wrap items-center justify-center gap-1 text-center">
            © {new Date().getFullYear()} EduConnect Inc. Made with{' '}
            <FiHeart className="w-3 h-3 text-red-500 fill-current inline" /> globally.
          </p>
          <div className="flex flex-wrap gap-3 sm:gap-4 text-xs sm:text-sm font-medium justify-center">
            <Link href="/privacy" className="py-1 px-2 text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">
              Privacy
            </Link>
            <Link href="/terms" className="py-1 px-2 text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">
              Terms
            </Link>
            <Link href="/cookie-policy" className="py-1 px-2 text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">
              Cookies
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
