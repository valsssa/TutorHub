'use client';

import Link from 'next/link';
import { Users, Search, FileText, Calendar, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, Skeleton, Avatar } from '@/components/ui';
import { useTutorStudents } from '@/lib/hooks/use-student-notes';
import { formatDate } from '@/lib/utils';

function StudentCardSkeleton() {
  return (
    <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-800">
      <div className="flex items-center gap-4">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div>
          <Skeleton className="h-5 w-32 mb-2" />
          <Skeleton className="h-4 w-24" />
        </div>
      </div>
      <Skeleton className="h-9 w-24" />
    </div>
  );
}

export default function TutorStudentsPage() {
  const { data: students, isLoading, error } = useTutorStudents();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            My Students
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Students you have worked with
          </p>
        </div>

        <Card>
          <CardContent className="p-4 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <StudentCardSkeleton key={i} />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            My Students
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Students you have worked with
          </p>
        </div>

        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-red-500">Failed to load students. Please try again.</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!students || students.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            My Students
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Students you have worked with
          </p>
        </div>

        <Card>
          <CardContent className="py-12 text-center">
            <div className="mx-auto w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
              <Users className="h-8 w-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              No students yet
            </h3>
            <p className="text-slate-500 dark:text-slate-400 max-w-sm mx-auto mb-6">
              Once you complete sessions with students, they will appear here and you can keep notes about them.
            </p>
            <Button asChild>
              <Link href="/tutor">
                Back to Dashboard
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            My Students
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            {students.length} {students.length === 1 ? 'student' : 'students'} you have worked with
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Student List
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {students.map((student) => (
              <Link
                key={student.id}
                href={`/tutor/students/${student.id}/notes`}
                className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors group"
              >
                <div className="flex items-center gap-4">
                  <Avatar
                    src={student.avatar_url}
                    name={student.name}
                    size="lg"
                  />
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {student.name}
                    </p>
                    <div className="flex items-center gap-3 text-sm text-slate-500">
                      {student.last_session_date && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          Last session: {formatDate(student.last_session_date, { month: 'short', day: 'numeric' })}
                        </span>
                      )}
                      {student.total_sessions && (
                        <span>
                          {student.total_sessions} {student.total_sessions === 1 ? 'session' : 'sessions'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-500 group-hover:text-primary-600 transition-colors flex items-center gap-1">
                    <FileText className="h-4 w-4" />
                    View Notes
                  </span>
                  <ChevronRight className="h-5 w-5 text-slate-400 group-hover:text-primary-600 transition-colors" />
                </div>
              </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
