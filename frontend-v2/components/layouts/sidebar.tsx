'use client';

import { useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/hooks';
import { useUIStore } from '@/lib/stores';
import { cn } from '@/lib/utils';
import {
  Home,
  Search,
  Calendar,
  MessageSquare,
  Package,
  Wallet,
  Settings,
  Users,
  BarChart3,
  Shield,
  Heart,
  Bell,
  User,
  CheckCircle,
  FileText,
  Cog,
  ChevronLeft,
  X,
  type LucideIcon,
} from 'lucide-react';

interface NavItem {
  href: string;
  icon: LucideIcon;
  label: string;
  placeholder?: boolean;
}

const navItems: Record<string, NavItem[]> = {
  student: [
    { href: '/student', icon: Home, label: 'Dashboard' },
    { href: '/tutors', icon: Search, label: 'Find Tutors' },
    { href: '/bookings', icon: Calendar, label: 'My Bookings' },
    { href: '/messages', icon: MessageSquare, label: 'Messages' },
    { href: '/packages', icon: Package, label: 'Packages' },
    { href: '/favorites', icon: Heart, label: 'Favorites' },
    { href: '/wallet', icon: Wallet, label: 'Wallet' },
    { href: '/notifications', icon: Bell, label: 'Notifications' },
  ],
  tutor: [
    { href: '/tutor', icon: Home, label: 'Dashboard' },
    { href: '/bookings', icon: Calendar, label: 'My Bookings' },
    { href: '/tutor/students', icon: Users, label: 'My Students' },
    { href: '/messages', icon: MessageSquare, label: 'Messages' },
    { href: '/profile', icon: User, label: 'My Profile' },
    { href: '/wallet', icon: Wallet, label: 'Wallet' },
    { href: '/notifications', icon: Bell, label: 'Notifications' },
  ],
  admin: [
    { href: '/admin', icon: Home, label: 'Dashboard' },
    { href: '/admin/users', icon: Users, label: 'Users Management', placeholder: true },
    { href: '/admin/approvals', icon: CheckCircle, label: 'Tutor Approvals', placeholder: true },
    { href: '/bookings', icon: Calendar, label: 'Bookings' },
    { href: '/admin/reports', icon: FileText, label: 'Reports', placeholder: true },
  ],
  owner: [
    { href: '/owner', icon: Home, label: 'Dashboard' },
    { href: '/owner/analytics', icon: BarChart3, label: 'Analytics', placeholder: true },
    { href: '/owner/admins', icon: Shield, label: 'Admin Management', placeholder: true },
    { href: '/owner/financial', icon: Wallet, label: 'Financial Reports', placeholder: true },
    { href: '/owner/config', icon: Cog, label: 'System Config', placeholder: true },
  ],
};

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const { sidebarCollapsed, setSidebarCollapsed, mobileNavOpen, setMobileNavOpen } =
    useUIStore();
  const prevPathnameRef = useRef(pathname);

  // M20: Close mobile sidebar on route change
  useEffect(() => {
    if (prevPathnameRef.current !== pathname) {
      setMobileNavOpen(false);
      prevPathnameRef.current = pathname;
    }
  }, [pathname, setMobileNavOpen]);

  const role = user?.role || 'student';
  const items = navItems[role] || navItems.student;

  return (
    <>
      {mobileNavOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileNavOpen(false)}
        />
      )}

      <aside
        className={cn(
          'fixed left-0 top-0 z-50 h-full bg-white dark:bg-slate-900',
          'border-r border-slate-200 dark:border-slate-800',
          'transition-all duration-300 flex flex-col',
          'pb-[env(safe-area-inset-bottom)] pl-[env(safe-area-inset-left)]',
          mobileNavOpen
            ? 'w-64 max-w-[80vw] translate-x-0 pointer-events-auto'
            : cn(
                sidebarCollapsed ? 'w-20' : 'w-64',
                '-translate-x-full lg:translate-x-0',
                'max-lg:pointer-events-none lg:pointer-events-auto'
              )
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-200 dark:border-slate-800 flex-shrink-0">
          {(mobileNavOpen || !sidebarCollapsed) && (
            <Link href="/" className="text-xl font-bold text-primary-600">
              EduStream
            </Link>
          )}
          {!mobileNavOpen && sidebarCollapsed && (
            <Link href="/" className="text-xl font-bold text-primary-600 mx-auto">
              E
            </Link>
          )}
          {/* M19: Close button for mobile sidebar */}
          {mobileNavOpen && (
            <button
              onClick={() => setMobileNavOpen(false)}
              className="lg:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5 text-slate-500" />
            </button>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden lg:flex p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <ChevronLeft
              className={cn(
                'h-5 w-5 transition-transform text-slate-500',
                sidebarCollapsed && 'rotate-180'
              )}
            />
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {items.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== '/' && item.href !== '/student' && item.href !== '/tutor' && item.href !== '/admin' && item.href !== '/owner' && pathname.startsWith(item.href + '/'));
            return (
              <Link
                key={item.href}
                href={item.placeholder ? '#' : item.href}
                onClick={(e) => {
                  if (item.placeholder) e.preventDefault();
                  setMobileNavOpen(false);
                }}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors',
                  item.placeholder
                    ? 'opacity-50 cursor-default text-slate-400 dark:text-slate-500'
                    : isActive
                      ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/20'
                      : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
                )}
                aria-disabled={item.placeholder}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {(mobileNavOpen || !sidebarCollapsed) && (
                  <span className={cn('font-medium', item.placeholder && 'italic')}>
                    {item.label}
                  </span>
                )}
                {item.placeholder && (mobileNavOpen || !sidebarCollapsed) && (
                  <span className="ml-auto text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                    Soon
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* M17: Settings pinned to bottom via mt-auto flex layout */}
        <div className="mt-auto px-3 pb-4 flex-shrink-0">
          <Link
            href="/settings"
            onClick={() => setMobileNavOpen(false)}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors',
              pathname.startsWith('/settings')
                ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/20'
                : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
            )}
          >
            <Settings className="h-5 w-5" />
            {(mobileNavOpen || !sidebarCollapsed) && <span className="font-medium">Settings</span>}
          </Link>
        </div>
      </aside>
    </>
  );
}
