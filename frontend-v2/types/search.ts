import type { TutorProfile, Subject } from './tutor';

export interface SearchResults {
  tutors: TutorProfile[];
  subjects: SubjectSearchResult[];
}

export interface SubjectSearchResult extends Subject {
  tutor_count: number;
}

export interface RecentSearch {
  id: string;
  query: string;
  timestamp: number;
}
