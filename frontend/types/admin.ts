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
  status: 'confirmed' | 'pending'
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
