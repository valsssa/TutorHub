
export enum UserRole {
  STUDENT = 'STUDENT',
  TUTOR = 'TUTOR',
  ADMIN = 'ADMIN',
  OWNER = 'OWNER'
}

export interface Review {
  id: string;
  studentName: string;
  rating: number;
  comment: string;
  date: string;
}

export interface Tutor {
  id: string;
  name: string;
  title: string;
  subject: string;
  rating: number;
  reviews: number;
  hourlyRate: number;
  isVerified: boolean;
  imageUrl: string;
  bio: string;
  topics: string[];
  availability: string[]; // ISO Date strings
  education: string[];
  philosophy: string;
  reviewsList: Review[];
  videoUrl?: string;
  nativeLanguage?: string;
  languages?: string[];
  isCalendarConnected?: boolean;
}

export interface Session {
  id: string;
  tutorId: string;
  tutorName: string;
  studentId: string;
  date: string;
  status: 'upcoming' | 'completed' | 'cancelled';
  price: number;
  subject: string;
  isReviewed?: boolean;
}

export interface User {
  id: string;
  name: string;
  role: UserRole;
  avatarUrl: string;
  balance?: number; // For student
  earnings?: number; // For tutor
  savedTutorIds?: string[];
}

export interface TutorStudent {
    id: string;
    name: string;
    avatar?: string;
    type: 'Subscription' | 'Trial' | 'Cancelled';
    lessonsCompleted?: number;
    lessonsTotal?: number;
    nextLessonAt?: string; // ISO Date string
    suggestedAction?: 'Message student' | null;
}

export interface AdminProfile {
    id: string;
    name: string;
    email: string;
    role: string;
    status: string;
    joinedDate: string;
}

export type ViewState = 'home' | 'student-lessons' | 'student-saved-tutors' | 'tutor-dashboard' | 'tutor-students' | 'tutor-earnings' | 'classroom' | 'login' | 'admin-dashboard' | 'admin-revenue' | 'admin-verifications' | 'admin-sessions' | 'admin-tutors' | 'admin-manage' | 'tutor-profile' | 'referral' | 'settings' | 'payment' | 'tutor-profile-editor' | 'legal-compliance' | 'support' | 'pricing' | 'mobile-app' | 'terms' | 'privacy' | 'cancellation-policy' | 'become-tutor' | 'tutor-rules' | 'success-stories' | 'affiliate-program' | 'cookie-policy';

export interface FilterState {
  searchQuery: string;
  maxPrice: number;
  subject: string;
  minRating: number;
  country: string;
  availability: string;
  sort: string;
  nativeSpeaker: boolean;
}

export interface VerificationRequest {
  id: string;
  tutorId: string;
  tutorName: string;
  email: string;
  subject: string;
  submittedDate: string;
  status: 'pending' | 'approved' | 'rejected';
  documents: { name: string; type: string; url: string }[];
}

export interface ChatMessage {
  id: string;
  senderId: string;
  text: string;
  timestamp: string;
}

export interface ChatThread {
  id: string;
  participantId: string; // The ID of the OTHER person
  participantName: string;
  participantAvatar: string;
  lastMessage: string;
  lastUpdated: string;
  unreadCount: number;
  messages: ChatMessage[];
}
