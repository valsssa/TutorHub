export interface UserData {
  id: number
  email: string
  role: string
  is_active: boolean
  is_verified?: boolean
  created_at: string
  updated_at?: string
  currency: string
  timezone: string
  // User identity fields
  first_name?: string | null
  last_name?: string | null
  /** Computed by backend: "{first_name} {last_name}" */
  full_name?: string | null
  /** True if user needs to complete profile (missing first_name or last_name) */
  profile_incomplete?: boolean
}

export interface Stats {
  totalUsers: number
  activeTutors: number
  totalSessions: number
  revenue: number
  satisfaction: number
  completionRate: number
}

export interface Activity {
  id: number
  user: string
  action: string
  time: string
  type: 'success' | 'info'
}

export interface Session {
  id: number
  student: string
  tutor: string
  subject: string
  time: string
  duration: string
  // Session state from four-field system (with legacy values for backward compatibility)
  status: 'REQUESTED' | 'SCHEDULED' | 'ACTIVE' | 'ENDED' | 'CANCELLED' | 'EXPIRED' | 'confirmed' | 'pending'
}

export interface Tutor {
  id: number
  name: string
  subject: string
  rating: number
  students: number
  hourlyRate: number
  status: 'active' | 'inactive'
}

export interface Student {
  id: number
  name: string
  sessions: number
  totalSpent: number
  status: 'active' | 'inactive'
}

export interface Conversation {
  id: number
  participant: string
  role: string
  avatar: string
  lastMessage: string
  time: string
  unread: number
  status: 'online' | 'offline' | 'away'
}

export interface Message {
  id: number
  sender: string
  message: string
  time: string
  type: 'sent' | 'received'
}

export interface SidebarItem {
  id: string
  label: string
  icon: any
}

export interface SettingsTab {
  id: string
  label: string
  icon: any
}
