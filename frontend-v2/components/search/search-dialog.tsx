'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Search, X, Clock, Loader2 } from 'lucide-react';
import { useSearch, useRecentSearches } from '@/lib/hooks/use-search';
import { SearchResults } from './search-results';

interface SearchDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SearchDialog({ isOpen, onClose }: SearchDialogProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  const { results, isLoading } = useSearch(query);
  const { recentSearches, addRecentSearch, removeRecentSearch, clearRecentSearches } =
    useRecentSearches();

  const totalResults =
    (results?.tutors.length || 0) + (results?.subjects.length || 0);

  // Track previous isOpen state to detect when dialog opens
  const prevIsOpenRef = useRef(isOpen);

  // Reset state and focus when dialog opens
  useEffect(() => {
    const wasOpen = prevIsOpenRef.current;
    prevIsOpenRef.current = isOpen;

    if (isOpen && !wasOpen) {
      // Dialog just opened - schedule state reset for next tick
      const resetTimer = setTimeout(() => {
        setQuery('');
        setSelectedIndex(0);
      }, 0);

      // Focus input after a brief delay to ensure it's rendered
      const focusTimer = setTimeout(() => {
        inputRef.current?.focus();
      }, 10);

      return () => {
        clearTimeout(resetTimer);
        clearTimeout(focusTimer);
      };
    }
  }, [isOpen]);

  // Custom setter that also resets selectedIndex
  const handleQueryChange = useCallback((newQuery: string) => {
    setQuery(newQuery);
    setSelectedIndex(0);
  }, []);

  const handleSelect = useCallback(
    (type: 'tutor' | 'subject', id: number) => {
      if (query.trim()) {
        addRecentSearch(query);
      }
      onClose();
      if (type === 'tutor') {
        router.push(`/tutors/${id}`);
      } else {
        router.push(`/tutors?subject=${id}`);
      }
    },
    [query, addRecentSearch, onClose, router]
  );

  const handleRecentSearchClick = useCallback(
    (searchQuery: string) => {
      handleQueryChange(searchQuery);
    },
    [handleQueryChange]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowDown':
          e.preventDefault();
          if (results && totalResults > 0) {
            setSelectedIndex((prev) => (prev + 1) % totalResults);
          }
          break;
        case 'ArrowUp':
          e.preventDefault();
          if (results && totalResults > 0) {
            setSelectedIndex((prev) => (prev - 1 + totalResults) % totalResults);
          }
          break;
        case 'Enter':
          e.preventDefault();
          if (results && totalResults > 0) {
            const tutorCount = results.tutors.length;
            if (selectedIndex < tutorCount) {
              handleSelect('tutor', results.tutors[selectedIndex].id);
            } else {
              const subjectIndex = selectedIndex - tutorCount;
              handleSelect('subject', results.subjects[subjectIndex].id);
            }
          }
          break;
      }
    },
    [onClose, results, totalResults, selectedIndex, handleSelect]
  );

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dialogRef.current && !dialogRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const showRecentSearches = !query.trim() && recentSearches.length > 0;
  const showResults = query.trim() && results && !isLoading;
  const showLoading = query.trim() && isLoading;
  const showEmptyState = !query.trim() && recentSearches.length === 0;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-start justify-center pt-0 sm:pt-[15vh]">
      <div
        ref={dialogRef}
        className="w-full h-full sm:h-auto sm:max-w-xl bg-white dark:bg-slate-900 sm:rounded-2xl shadow-2xl sm:border border-slate-200 dark:border-slate-700 overflow-hidden flex flex-col sm:block"
        role="dialog"
        aria-modal="true"
        aria-label="Search"
      >
        <div className="flex items-center gap-3 px-3 sm:px-4 border-b border-slate-200 dark:border-slate-700">
          <Search className="h-5 w-5 text-slate-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search tutors, subjects..."
            className="flex-1 h-12 sm:h-14 bg-transparent text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none text-base"
          />
          {isLoading && (
            <Loader2 className="h-5 w-5 text-slate-400 animate-spin shrink-0" />
          )}
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Close search"
          >
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>

        <div className="flex-1 sm:flex-none max-h-none sm:max-h-[60vh] overflow-y-auto overscroll-contain">
          {showEmptyState && (
            <div className="px-4 py-8 text-center">
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Start typing to search for tutors or subjects
              </p>
            </div>
          )}

          {showRecentSearches && (
            <div className="py-2">
              <div className="px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-slate-400" />
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Recent Searches
                  </span>
                </div>
                <button
                  onClick={clearRecentSearches}
                  className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                >
                  Clear all
                </button>
              </div>
              <ul>
                {recentSearches.map((search) => (
                  <li key={search.id} className="group">
                    <div className="flex items-center">
                      <button
                        onClick={() => handleRecentSearchClick(search.query)}
                        className="flex-1 px-4 py-2.5 text-left text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                      >
                        {search.query}
                      </button>
                      <button
                        onClick={() => removeRecentSearch(search.id)}
                        className="p-2 mr-2 opacity-0 group-hover:opacity-100 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-all"
                        aria-label={`Remove "${search.query}" from recent searches`}
                      >
                        <X className="h-4 w-4 text-slate-400" />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {showLoading && (
            <div className="px-4 py-8 text-center">
              <Loader2 className="h-6 w-6 text-primary-500 animate-spin mx-auto" />
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                Searching...
              </p>
            </div>
          )}

          {showResults && (
            <SearchResults
              tutors={results.tutors}
              subjects={results.subjects}
              selectedIndex={selectedIndex}
              onSelect={handleSelect}
            />
          )}
        </div>

        <div className="hidden sm:block px-4 py-3 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border border-slate-200 dark:border-slate-600 font-mono">
                  ↑↓
                </kbd>
                <span>Navigate</span>
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border border-slate-200 dark:border-slate-600 font-mono">
                  ↵
                </kbd>
                <span>Select</span>
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border border-slate-200 dark:border-slate-600 font-mono">
                  Esc
                </kbd>
                <span>Close</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
