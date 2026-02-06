import type { TutorProfile } from './tutor';

export interface Favorite {
  id: number;
  student_id: number;
  tutor_profile_id: number;
  created_at: string;
  tutor?: TutorProfile;
}

export interface FavoriteStatus {
  is_favorite: boolean;
}
