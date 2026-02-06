import { api } from './client';
import type { TutorProfile, Subject } from '@/types';
import type { SearchResults, SubjectSearchResult } from '@/types/search';

export const searchApi = {
  search: async (query: string): Promise<SearchResults> => {
    if (!query.trim()) {
      return { tutors: [], subjects: [] };
    }

    const [tutorsResponse, subjectsResponse] = await Promise.all([
      api.get<{ items: TutorProfile[] }>(`/tutors?search=${encodeURIComponent(query)}&page_size=5`),
      api.get<Subject[]>('/subjects'),
    ]);

    const queryLower = query.toLowerCase();
    const matchingSubjects: SubjectSearchResult[] = subjectsResponse
      .filter((s) => s.name.toLowerCase().includes(queryLower))
      .slice(0, 5)
      .map((s) => ({
        ...s,
        tutor_count: 0,
      }));

    return {
      tutors: tutorsResponse.items || [],
      subjects: matchingSubjects,
    };
  },
};
