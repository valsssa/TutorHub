'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { Menu, Sun, Moon, LogOut, User, Settings, ChevronDown, Search } from 'lucide-react';
import { useAuth, useSearchShortcut } from '@/lib/hooks';
import { useUIStore } from '@/lib/stores';
import { Avatar } from '@/components/ui';
import { SearchDialog } from '@/components/search';
import { NotificationBell } from '@/components/notifications';
import { cn } from '@/lib/utils';

export function Topbar() {
  const { user, logout } = useAuth();
  const { setMobileNavOpen, theme, setTheme } = useUIStore();
  const { isSearchOpen, openSearch, closeSearch } = useSearchShortcut();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getProfileLink = () => {
    switch (user?.role) {
      case 'admin': return '/admin';
      case 'owner': return '/owner';
      default: return '/profile';
    }
  };

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
      <div className="flex h-full items-center justify-between px-3 sm:px-4 md:px-6">
        <button
          onClick={() => setMobileNavOpen(true)}
          className="lg:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          <Menu className="h-5 w-5 text-slate-600 dark:text-slate-400" />
        </button>

        <div className="hidden lg:block flex-1 max-w-md ml-4">
          <button
            onClick={openSearch}
            className="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-500 bg-slate-100 dark:bg-slate-800 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            <Search className="h-4 w-4" />
            <span className="flex-1 text-left">Search tutors, subjects...</span>
            <kbd className="max-sm:hidden inline-flex items-center gap-1 px-2 py-0.5 text-xs text-slate-400 bg-white dark:bg-slate-700 rounded border border-slate-200 dark:border-slate-600 font-mono">
              <span className="text-xs">Cmd</span>K
            </kbd>
          </button>
        </div>

        <div className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={openSearch}
            className="lg:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Open search"
          >
            <Search className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          </button>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? (
              <Sun className="h-5 w-5 text-slate-600 dark:text-slate-400" />
            ) : (
              <Moon className="h-5 w-5 text-slate-600 dark:text-slate-400" />
            )}
          </button>

          <NotificationBell />

          <div className="relative ml-2 pl-4 border-l border-slate-200 dark:border-slate-700" ref={menuRef}>
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-3 p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <Avatar
                src={user?.avatar_url}
                name={user?.first_name ?? undefined}
                size="sm"
              />
              <div className="hidden md:block text-left max-w-[120px] lg:max-w-[160px]">
                <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-slate-500 capitalize truncate">{user?.role}</p>
              </div>
              <ChevronDown className={cn(
                'h-4 w-4 text-slate-400 transition-transform hidden md:block',
                userMenuOpen && 'rotate-180'
              )} />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 py-1 z-50">
                <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700 md:hidden">
                  <p className="text-sm font-medium text-slate-900 dark:text-white">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
                </div>

                <Link
                  href={getProfileLink()}
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  <User className="h-4 w-4" />
                  Profile
                </Link>

                <Link
                  href="/settings"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </Link>

                <div className="border-t border-slate-200 dark:border-slate-700 my-1" />

                <button
                  onClick={() => {
                    setUserMenuOpen(false);
                    logout();
                  }}
                  className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <SearchDialog isOpen={isSearchOpen} onClose={closeSearch} />
    </header>
  );
}
