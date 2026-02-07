'use client';

import { useState, useMemo } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Save,
  Trash2,
  FileText,
  AlertCircle,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Skeleton,
  Avatar,
} from '@/components/ui';
import {
  useStudentNote,
  useUpdateStudentNote,
  useDeleteStudentNote,
  useTutorStudents,
} from '@/lib/hooks/use-student-notes';
import { formatDate } from '@/lib/utils';

// Inner component that receives initial notes as prop to avoid useEffect
function NotesEditor({
  initialNotes,
  existingNote,
  studentId,
  onSaveSuccess,
}: {
  initialNotes: string;
  existingNote: { notes?: string | null; updated_at?: string } | null | undefined;
  studentId: number;
  onSaveSuccess: () => void;
}) {
  const [notes, setNotes] = useState(initialNotes);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const updateNoteMutation = useUpdateStudentNote();
  const deleteNoteMutation = useDeleteStudentNote();

  // Derive hasChanges from current notes vs original
  const hasChanges = useMemo(() => {
    const originalNotes = existingNote?.notes || '';
    return notes !== originalNotes;
  }, [notes, existingNote?.notes]);

  const isSaving = updateNoteMutation.isPending;
  const isDeleting = deleteNoteMutation.isPending;

  const handleSave = async () => {
    try {
      await updateNoteMutation.mutateAsync({
        studentId,
        data: { notes: notes || null },
      });
      onSaveSuccess();
    } catch {
      // Error displayed via mutation state
    }
  };

  const handleDelete = async () => {
    try {
      await deleteNoteMutation.mutateAsync(studentId);
      setNotes('');
      setShowDeleteConfirm(false);
    } catch {
      // Error displayed via mutation state
    }
  };

  return (
    <>
      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <Card className="border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
          <CardContent className="py-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
              <div className="flex items-start sm:items-center gap-3">
                <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5 sm:mt-0" />
                <p className="text-sm text-red-700 dark:text-red-400">
                  Are you sure you want to delete all notes for this student? This action cannot be undone.
                </p>
              </div>
              <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={isDeleting}
                >
                  Cancel
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={handleDelete}
                  disabled={isDeleting}
                >
                  {isDeleting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    'Delete'
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notes card */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Private Notes
            </CardTitle>
            {existingNote?.updated_at && (
              <p className="text-sm text-slate-500 mt-1">
                Last updated: {formatDate(existingNote.updated_at, {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                  hour: 'numeric',
                  minute: '2-digit'
                })}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {existingNote && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDeleteConfirm(true)}
                disabled={isSaving || isDeleting}
                className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                <Trash2 className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">Delete</span>
              </Button>
            )}
            <Button
              onClick={handleSave}
              disabled={!hasChanges || isSaving || isDeleting}
              size="sm"
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 sm:mr-2" />
                  <span className="hidden sm:inline">Save</span>
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Keep private notes about this student to track their progress, learning style, areas to focus on, and anything else that will help you provide better tutoring.
            </p>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              maxLength={2000}
              placeholder="Write your notes here... (e.g., learning goals, progress, topics covered, areas needing improvement)"
              className="w-full h-48 sm:h-64 p-3 sm:p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-y text-sm sm:text-base"
              disabled={isSaving || isDeleting}
            />
            <div className="flex justify-between items-center text-sm text-slate-500">
              <span className={notes.length >= 2000 ? 'text-red-500 font-medium' : ''}>
                {notes.length}/2000
              </span>
              {hasChanges && (
                <span className="text-amber-600 dark:text-amber-400">
                  Unsaved changes
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error display */}
      {(updateNoteMutation.error || deleteNoteMutation.error) && (
        <Card className="border-red-200 dark:border-red-800">
          <CardContent className="py-4">
            <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
              <AlertCircle className="h-5 w-5" />
              <p className="text-sm">
                {updateNoteMutation.error
                  ? 'Failed to save notes. Please try again.'
                  : 'Failed to delete notes. Please try again.'}
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}

export default function StudentNotesPage() {
  const params = useParams();
  const studentId = Number(params.studentId);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Fetch the student info from our students list
  const { data: students, isLoading: studentsLoading } = useTutorStudents();
  const student = students?.find((s) => s.id === studentId);

  // Fetch existing note for this student
  const { data: existingNote, isLoading: noteLoading, error: noteError } = useStudentNote(studentId);

  const isLoading = studentsLoading || noteLoading;

  const handleSaveSuccess = () => {
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded-lg" />
          <div>
            <Skeleton className="h-6 w-48 mb-2" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>

        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" asChild className="gap-2">
          <Link href="/tutor/students">
            <ArrowLeft className="h-4 w-4" />
            Back to Students
          </Link>
        </Button>

        <Card>
          <CardContent className="py-12 text-center">
            <div className="mx-auto w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
              <AlertCircle className="h-8 w-8 text-red-500" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Student Not Found
            </h3>
            <p className="text-slate-500 dark:text-slate-400 max-w-sm mx-auto mb-6">
              This student does not exist or you have not had any sessions with them.
            </p>
            <Button asChild>
              <Link href="/tutor/students">
                View All Students
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with back button */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3 sm:gap-4 min-w-0 flex-wrap sm:flex-nowrap">
          <Button variant="ghost" size="sm" asChild className="gap-2 shrink-0">
            <Link href="/tutor/students">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
          </Button>
          <div className="hidden sm:block h-8 w-px bg-slate-200 dark:bg-slate-700" />
          <Avatar
            src={student.avatar_url}
            name={student.name}
            size="md"
            className="shrink-0"
          />
          <div className="min-w-0">
            <h1 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white truncate">
              {student.name}
            </h1>
            {student.total_sessions && (
              <p className="text-sm text-slate-500">
                {student.total_sessions} {student.total_sessions === 1 ? 'session' : 'sessions'}
              </p>
            )}
          </div>
        </div>

        {saveSuccess && (
          <span className="text-sm text-green-600 flex items-center gap-1 shrink-0">
            <CheckCircle className="h-4 w-4" />
            Saved
          </span>
        )}
      </div>

      {/* Note error display */}
      {noteError && (
        <Card className="border-red-200 dark:border-red-800">
          <CardContent className="py-4">
            <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
              <AlertCircle className="h-5 w-5" />
              <p className="text-sm">
                Failed to load notes. Please try refreshing the page.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notes editor - uses key to reset state when existingNote changes */}
      <NotesEditor
        key={existingNote?.updated_at || 'new'}
        initialNotes={existingNote?.notes || ''}
        existingNote={existingNote}
        studentId={studentId}
        onSaveSuccess={handleSaveSuccess}
      />
    </div>
  );
}
