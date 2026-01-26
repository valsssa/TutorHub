'use client'

import { useState, useEffect, useRef, lazy, Suspense, useCallback } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'
import {
  FiBook,
  FiLogOut,
  FiUser,
  FiSettings,
  FiMessageSquare,
  FiHeart,
  FiChevronDown,
  FiCalendar,
  FiSun,
  FiMoon,
  FiMenu,
  FiX,
  FiShare2,
  FiUsers
} from 'react-icons/fi'
import { User } from '@/types'
import { auth, messages } from '@/lib/api'
import { authUtils } from '@/lib/auth'
import { useTheme } from '@/contexts/ThemeContext'
import { useWebSocket } from '@/hooks/useWebSocket'
import Button from './Button'
import NotificationBell from './NotificationBell'
import Avatar from './Avatar'

interface NavbarProps {
  user: User
}

export default function Navbar({ user }: NavbarProps) {
  const router = useRouter()
  const { theme, toggleTheme } = useTheme()
  const [userDropdownOpen, setUserDropdownOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [unreadMessageCount, setUnreadMessageCount] = useState(0)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { lastMessage } = useWebSocket()

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setUserDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Load unread message count
  const loadUnreadCount = useCallback(async () => {
    try {
      const data = await messages.getUnreadCount()
      setUnreadMessageCount(data.total || 0)
    } catch (error) {
      console.error('Failed to load unread message count:', error)
      setUnreadMessageCount(0)
    }
  }, [])

  // Load unread count on mount and when page becomes visible
  useEffect(() => {
    loadUnreadCount()

    // Refresh count when page becomes visible (user returns to tab)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadUnreadCount()
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)

    // Poll for updates every 30 seconds
    const interval = setInterval(loadUnreadCount, 30000)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      clearInterval(interval)
    }
  }, [loadUnreadCount])

  // Listen to WebSocket for new messages
  useEffect(() => {
    if (!lastMessage) return

    if (lastMessage.type === 'new_message') {
      // Increment count if message is for current user
      const currentUserId = user?.id
      if (lastMessage.recipient_id === currentUserId) {
        setUnreadMessageCount((prev) => prev + 1)
      }
    } else if (lastMessage.type === 'thread_read' || lastMessage.type === 'message_read') {
      // Decrement count when messages are read
      loadUnreadCount()
    }
  }, [lastMessage, user?.id, loadUnreadCount])

  const handleLogout = () => {
    auth.logout()
    router.push('/')
  }

  const handleMenuClick = (action: () => void) => {
    action()
    setUserDropdownOpen(false)
    setMobileMenuOpen(false)
  }

  const renderAvatar = (sizeVariant: 'xs' | 'sm' | 'md' = 'sm') => {
    const avatarUrl = user.avatarUrl ?? user.avatar_url
    return (
      <Avatar 
        name={user.email} 
        avatarUrl={avatarUrl}
        variant="emerald"
        size={sizeVariant}
      />
    )
  }

  return (
    <nav className="w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md transition-colors duration-200 relative z-[10000]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 cursor-pointer"
        >
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center shadow-sm">
            <FiBook className="text-white w-5 h-5" />
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-700 dark:from-emerald-400 dark:to-emerald-600 bg-clip-text text-transparent hidden sm:inline">
            EduConnect
          </span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-4 sm:gap-6">
          {/* Navigation Links based on role */}
          <div className="flex gap-6">
            {authUtils.isTutor(user) && (
              <Link
                href="/dashboard"
                className="text-sm font-medium text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors"
              >
                Dashboard
              </Link>
            )}
            {authUtils.isStudent(user) && (
              <Link
                href="https://edustream.valsa.solutions/dashboard"
                className="text-sm font-medium text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors"
              >
                Dashboard
              </Link>
            )}
            {authUtils.isAdmin(user) && (
              <Link
                href="/admin"
                className="text-sm font-medium text-emerald-500 hover:text-emerald-600 dark:text-emerald-400 transition-colors"
              >
                Admin Panel
              </Link>
            )}
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

          <div className="h-6 w-px bg-slate-200 dark:bg-slate-800" />

          {/* Messages */}
          <Link
            href="/messages"
            className="relative tap-target p-2 text-slate-500 hover:text-emerald-600 dark:text-slate-400 dark:hover:text-emerald-400 transition-colors rounded-full hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label={`Messages${unreadMessageCount > 0 ? ` (${unreadMessageCount} unread)` : ''}`}
          >
            <FiMessageSquare className="w-5 h-5" />
            {unreadMessageCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold leading-none text-white bg-gradient-to-br from-red-500 to-red-600 rounded-full min-w-[20px] h-5 shadow-lg shadow-red-500/50 ring-2 ring-white dark:ring-slate-950">
                {unreadMessageCount > 99 ? '99+' : unreadMessageCount}
              </span>
            )}
          </Link>

          {/* Saved Tutors */}
          {authUtils.isStudent(user) && (
            <button
              onClick={() => router.push('/saved-tutors')}
              className="tap-target p-2 text-slate-500 hover:text-emerald-600 dark:text-slate-400 dark:hover:text-emerald-400 transition-colors rounded-full hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Saved tutors"
            >
              <FiHeart className="w-5 h-5" />
            </button>
          )}

          {/* Notifications */}
          <NotificationBell />

          {/* User Avatar Dropdown */}
          <div className="relative pl-2 border-l border-slate-200 dark:border-slate-800" ref={dropdownRef}>
            <button
              onClick={() => setUserDropdownOpen(!userDropdownOpen)}
              className="flex items-center gap-3 p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors focus:outline-none"
              aria-haspopup="menu"
              aria-expanded={userDropdownOpen}
              aria-controls="user-menu"
            >
              {renderAvatar()}
              <span className="hidden sm:block text-sm font-bold text-slate-900 dark:text-white max-w-[120px] truncate">
                {user.email?.split('@')[0]}
              </span>
              <FiChevronDown className={`w-4 h-4 text-slate-400 hidden sm:block transition-transform ${userDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            <AnimatePresence>
              {userDropdownOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                  className="absolute right-0 top-full mt-2 w-72 bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-slate-200 dark:border-slate-800 py-2 z-[10001]"
                  id="user-menu"
                  role="menu"
                >
                  {/* User Info */}
                  <div className="px-5 py-4 flex items-center gap-3 border-b border-slate-100 dark:border-slate-800">
                    {renderAvatar('sm')}
                    <div className="overflow-hidden">
                      <p className="font-bold text-slate-900 dark:text-white truncate">{user.email}</p>
                      <p className="text-xs text-slate-500 capitalize">{user.role?.toLowerCase()}</p>
                    </div>
                  </div>

                  {/* Share Profile (Tutor only) */}
                  {authUtils.isTutor(user) && (
                    <div className="px-5 py-3">
                      <button className="w-full flex items-center justify-center gap-2 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                        <FiShare2 className="w-4 h-4" /> Share profile
                      </button>
                    </div>
                  )}

                  {/* Menu Items */}
                  <div className="py-1">
                    <Link
                      href="/messages"
                      onClick={() => setUserDropdownOpen(false)}
                      className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <FiMessageSquare className="w-4 h-4" /> Messages
                      </div>
                      {unreadMessageCount > 0 && (
                        <span className="inline-flex items-center justify-center px-2 py-0.5 text-[10px] font-bold leading-none text-white bg-gradient-to-br from-red-500 to-red-600 rounded-full min-w-[20px] h-5 shadow-md shadow-red-500/30">
                          {unreadMessageCount > 99 ? '99+' : unreadMessageCount}
                        </span>
                      )}
                    </Link>

                    {authUtils.isTutor(user) && (
                      <>
                        <Link
                          href="/tutor/profile"
                          onClick={() => setUserDropdownOpen(false)}
                          className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                        >
                          <FiUser className="w-4 h-4" /> My Profile
                        </Link>
                        <Link
                          href="/dashboard"
                          onClick={() => setUserDropdownOpen(false)}
                          className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                        >
                          <FiCalendar className="w-4 h-4" /> Dashboard
                        </Link>
                      </>
                    )}

                    {authUtils.isStudent(user) && (
                      <>
                        <Link
                          href="https://edustream.valsa.solutions/dashboard"
                          onClick={() => setUserDropdownOpen(false)}
                          className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                        >
                          <FiCalendar className="w-4 h-4" /> Dashboard
                        </Link>
                        <Link
                          href="/bookings"
                          onClick={() => setUserDropdownOpen(false)}
                          className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                        >
                          <FiBook className="w-4 h-4" /> My Lessons
                        </Link>
                        <Link
                          href="/saved-tutors"
                          onClick={() => setUserDropdownOpen(false)}
                          className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                        >
                          <FiHeart className="w-4 h-4" /> Saved Tutors
                        </Link>
                      </>
                    )}

                    <Link
                      href="/settings"
                      onClick={() => setUserDropdownOpen(false)}
                      className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                    >
                      <FiSettings className="w-4 h-4" /> Settings
                    </Link>
                  </div>

                  <div className="h-px bg-slate-100 dark:bg-slate-800 my-1 mx-2"></div>

                  {/* Logout */}
                  <button
                    onClick={() => handleMenuClick(handleLogout)}
                    className="w-full text-left px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center gap-3"
                  >
                    <FiLogOut className="w-4 h-4" /> Log out
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
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
            aria-controls="mobile-menu"
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
              className="absolute top-16 left-0 w-full bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-xl md:hidden"
              id="mobile-menu"
              role="menu"
            >
              <div className="p-4 space-y-4">
                {/* User Info */}
                <div className="flex items-center gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
                  {renderAvatar()}
                  <div>
                    <p className="font-bold text-slate-900 dark:text-white">{user.email}</p>
                    <p className="text-xs text-slate-500 capitalize">{user.role}</p>
                  </div>
                </div>

                {/* Menu Items */}
                <div className="grid gap-2">

                  {authUtils.isTutor(user) && (
                    <>
                      <Link 
                        href="/tutor/profile"
                        onClick={() => setMobileMenuOpen(false)}
                        className="text-left py-2 font-medium text-slate-700 dark:text-slate-300"
                      >
                        My Profile
                      </Link>
                      <Link 
                        href="/dashboard"
                        onClick={() => setMobileMenuOpen(false)}
                        className="text-left py-2 font-medium text-slate-700 dark:text-slate-300"
                      >
                        Dashboard
                      </Link>
                    </>
                  )}

                  {authUtils.isStudent(user) && (
                    <Link 
                      href="https://edustream.valsa.solutions/dashboard"
                      onClick={() => setMobileMenuOpen(false)}
                      className="text-left py-2 font-medium text-slate-700 dark:text-slate-300"
                    >
                      Dashboard
                    </Link>
                  )}

                  <Link 
                    href="/messages"
                    onClick={() => setMobileMenuOpen(false)}
                    className="relative text-left py-2 font-medium text-slate-700 dark:text-slate-300 flex items-center justify-between"
                  >
                    <span>Messages</span>
                    {unreadMessageCount > 0 && (
                      <span className="inline-flex items-center justify-center px-2 py-0.5 text-[10px] font-bold leading-none text-white bg-gradient-to-br from-red-500 to-red-600 rounded-full min-w-[20px] h-5 shadow-md shadow-red-500/30">
                        {unreadMessageCount > 99 ? '99+' : unreadMessageCount}
                      </span>
                    )}
                  </Link>
                  <Link 
                    href="/settings"
                    onClick={() => setMobileMenuOpen(false)}
                    className="text-left py-2 font-medium text-slate-700 dark:text-slate-300"
                  >
                    Settings
                  </Link>
                  
                  <button
                    onClick={() => handleMenuClick(handleLogout)}
                    className="text-left py-2 font-medium text-red-600"
                  >
                    Log Out
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
