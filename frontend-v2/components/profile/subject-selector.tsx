'use client';

import { useState, useRef, useEffect } from 'react';
import { X, ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui';
import type { Subject } from '@/types';

interface SubjectSelectorProps {
  subjects: Subject[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
  error?: string;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
}

export function SubjectSelector({
  subjects,
  selectedIds,
  onChange,
  error,
  label,
  placeholder = 'Select subjects...',
  disabled = false,
}: SubjectSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const selectedSubjects = subjects.filter((s) => selectedIds.includes(s.id));
  const filteredSubjects = subjects.filter((s) =>
    s.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleSubject = (subjectId: number) => {
    if (selectedIds.includes(subjectId)) {
      onChange(selectedIds.filter((id) => id !== subjectId));
    } else {
      onChange([...selectedIds, subjectId]);
    }
  };

  const removeSubject = (subjectId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(selectedIds.filter((id) => id !== subjectId));
  };

  return (
    <div className="space-y-1.5" ref={containerRef}>
      {label && (
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
          {label}
        </label>
      )}

      <div
        className={cn(
          'relative min-h-[42px] w-full rounded-xl border bg-white px-3 py-2',
          'border-slate-200 dark:border-slate-700 dark:bg-slate-900',
          'focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-transparent',
          error && 'border-red-500 focus-within:ring-red-500',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        onClick={() => {
          if (!disabled) {
            setIsOpen(true);
            inputRef.current?.focus();
          }
        }}
      >
        <div className="flex flex-wrap gap-1.5 items-center">
          {selectedSubjects.map((subject) => (
            <Badge key={subject.id} variant="primary" className="gap-1 pr-1">
              {subject.name}
              <button
                type="button"
                onClick={(e) => removeSubject(subject.id, e)}
                className="ml-1 rounded-full hover:bg-primary-600 p-0.5"
                disabled={disabled}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          <input
            ref={inputRef}
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onFocus={() => setIsOpen(true)}
            placeholder={selectedSubjects.length === 0 ? placeholder : ''}
            className={cn(
              'flex-1 min-w-[120px] bg-transparent outline-none text-sm',
              'placeholder:text-slate-400 dark:placeholder:text-slate-500'
            )}
            disabled={disabled}
          />
          <ChevronDown className={cn(
            'h-4 w-4 text-slate-400 transition-transform',
            isOpen && 'transform rotate-180'
          )} />
        </div>

        {isOpen && !disabled && (
          <div className="absolute left-0 right-0 top-full mt-1 z-50 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg max-h-60 overflow-auto">
            {filteredSubjects.length === 0 ? (
              <div className="p-3 text-sm text-slate-500 text-center">
                {searchTerm ? 'No subjects found' : 'No subjects available'}
              </div>
            ) : (
              <div className="py-1">
                {filteredSubjects.map((subject) => {
                  const isSelected = selectedIds.includes(subject.id);
                  return (
                    <button
                      key={subject.id}
                      type="button"
                      onClick={() => toggleSubject(subject.id)}
                      className={cn(
                        'w-full px-3 py-2 text-left text-sm flex items-center justify-between',
                        'hover:bg-slate-50 dark:hover:bg-slate-800',
                        isSelected && 'bg-primary-50 dark:bg-primary-900/20'
                      )}
                    >
                      <span className={cn(
                        'text-slate-700 dark:text-slate-300',
                        isSelected && 'text-primary-600 dark:text-primary-400 font-medium'
                      )}>
                        {subject.name}
                      </span>
                      {isSelected && (
                        <Check className="h-4 w-4 text-primary-500" />
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}
    </div>
  );
}
