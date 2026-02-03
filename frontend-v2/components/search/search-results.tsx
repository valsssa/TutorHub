'use client';


import { Star, BookOpen, Users } from 'lucide-react';
import { Avatar, Badge } from '@/components/ui';
import type { TutorProfile } from '@/types';
import type { SubjectSearchResult } from '@/types/search';

interface SearchResultsProps {
  tutors: TutorProfile[];
  subjects: SubjectSearchResult[];
  selectedIndex: number;
  onSelect: (type: 'tutor' | 'subject', id: number) => void;
}

export function SearchResults({
  tutors,
  subjects,
  selectedIndex,
  onSelect,
}: SearchResultsProps) {
  const totalTutors = tutors.length;

  const getItemIndex = (type: 'tutor' | 'subject', index: number) => {
    if (type === 'tutor') return index;
    return totalTutors + index;
  };

  if (tutors.length === 0 && subjects.length === 0) {
    return (
      <div className="px-4 py-8 text-center">
        <p className="text-sm text-slate-500 dark:text-slate-400">
          No results found. Try a different search term.
        </p>
      </div>
    );
  }

  return (
    <div className="py-2">
      {tutors.length > 0 && (
        <div className="mb-2">
          <div className="px-4 py-2 flex items-center gap-2">
            <Users className="h-4 w-4 text-slate-400" />
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Tutors
            </span>
          </div>
          <ul>
            {tutors.map((tutor, index) => (
              <li key={tutor.id}>
                <button
                  onClick={() => onSelect('tutor', tutor.id)}
                  className={`w-full px-4 py-3 flex items-center gap-3 text-left transition-colors ${
                    getItemIndex('tutor', index) === selectedIndex
                      ? 'bg-primary-50 dark:bg-primary-900/20'
                      : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  }`}
                >
                  <Avatar
                    src={tutor.avatar_url}
                    name={tutor.display_name}
                    size="sm"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {tutor.display_name}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                        <span className="text-xs text-slate-500">
                          {tutor.average_rating.toFixed(1)}
                        </span>
                      </div>
                      {tutor.subjects.length > 0 && (
                        <>
                          <span className="text-slate-300 dark:text-slate-600">|</span>
                          <span className="text-xs text-slate-500 truncate">
                            {tutor.subjects.slice(0, 2).map((s) => s.name).join(', ')}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                  <Badge variant="default" className="text-xs">
                    ${tutor.hourly_rate}/hr
                  </Badge>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {subjects.length > 0 && (
        <div>
          <div className="px-4 py-2 flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-slate-400" />
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Subjects
            </span>
          </div>
          <ul>
            {subjects.map((subject, index) => (
              <li key={subject.id}>
                <button
                  onClick={() => onSelect('subject', subject.id)}
                  className={`w-full px-4 py-3 flex items-center gap-3 text-left transition-colors ${
                    getItemIndex('subject', index) === selectedIndex
                      ? 'bg-primary-50 dark:bg-primary-900/20'
                      : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  }`}
                >
                  <div className="h-8 w-8 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                    <BookOpen className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                      {subject.name}
                    </p>
                    {subject.tutor_count > 0 && (
                      <p className="text-xs text-slate-500 mt-0.5">
                        {subject.tutor_count} {subject.tutor_count === 1 ? 'tutor' : 'tutors'}
                      </p>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
