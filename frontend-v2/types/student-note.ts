export interface StudentNote {
  id: number;
  tutor_id: number;
  student_id: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentNoteUpdate {
  notes: string | null;
}

export interface TutorStudent {
  id: number;
  name: string;
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
  email?: string;
  last_session_date?: string;
  total_sessions?: number;
}
