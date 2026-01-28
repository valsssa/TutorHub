'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'
import {
  FiBook,
  FiSun,
  FiMoon,
  FiMenu,
  FiX,
} from 'react-icons/fi'
import { useTheme } from '@/contexts/ThemeContext'
import Button from './Button'

export default function PublicHeader() {
  const router = useRouter()
  const { theme, toggleTheme } = useTheme()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <nav className="relative z-50 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 cursor-pointer">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center shadow-sm">
            <FiBook className="text-white w-5 h-5" />
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-700 dark:from-emerald-400 dark:to-emerald-600 bg-clip-text text-transparent">
            EduConnect
          </span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-6">
          {/* Navigation Links */}
          <div className="flex gap-6">
          </div>

          <div className="h-6 w-px bg-slate-200 dark:bg-slate-800" />

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="tap-target p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors rounded-full hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Toggle theme"
            aria-pressed={theme === 'dark'}
          >
            {theme === 'dark' ? <FiSun className="w-5 h-5" /> : <FiMoon className="w-5 h-5" />}
          </button>

          {/* Auth Buttons */}
          <div className="flex items-center gap-3 pl-4 border-l border-slate-200 dark:border-slate-800">
            <button
              onClick={() => router.push('/login')}
              className="text-sm font-bold text-slate-600 dark:text-slate-300 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
            >
              Log in
            </button>
            <Button
              onClick={() => router.push('/register')}
              className="px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm font-bold rounded-lg hover:opacity-90 transition-opacity"
            >
              Sign up
            </Button>
          </div>
        </div>

        {/* Mobile Menu Button */}
        <div className="flex md:hidden items-center gap-4">
          <button
            onClick={toggleTheme}
            className="tap-target p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors rounded-full"
            aria-label="Toggle theme"
            aria-pressed={theme === 'dark'}
          >
            {theme === 'dark' ? <FiSun className="w-5 h-5" /> : <FiMoon className="w-5 h-5" />}
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-600 dark:text-slate-300"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
            aria-controls="public-mobile-menu"
          >
            {mobileMenuOpen ? <FiX className="w-6 h-6" /> : <FiMenu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu Dropdown */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-16 left-0 w-full bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-xl md:hidden z-[9999]"
              id="public-mobile-menu"
              role="menu"
            >
              <div className="p-4 space-y-4">
                <div className="flex flex-col gap-3">
                  <div className="h-px bg-slate-100 dark:bg-slate-800 my-2"></div>
                  <button
                    onClick={() => {
                      router.push('/login')
                      setMobileMenuOpen(false)
                    }}
                    className="w-full py-3 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-bold rounded-xl"
                  >
                    Log in
                  </button>
                  <button
                    onClick={() => {
                      router.push('/register')
                      setMobileMenuOpen(false)
                    }}
                    className="w-full py-3 bg-emerald-600 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20"
                  >
                    Sign up
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </nav>
  )
}
