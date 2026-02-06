import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studentNotesApi } from '@/lib/api';
import type { StudentNote, StudentNoteUpdate, TutorStudent } from '@/types/student-note';
import { bookingsApi } from '@/lib/api';
import type { Booking } from '@/types';

export const studentNotesKeys = {
  all: ['student-notes'] as const,
  get: (studentId: number) => [...studentNotesKeys.all, 'get', studentId] as const,
  students: () => [...studentNotesKeys.all, 'students'] as const,
};

export function useStudentNote(studentId: number) {
  return useQuery({
    queryKey: studentNotesKeys.get(studentId),
    queryFn: () => studentNotesApi.get(studentId),
    enabled: !!studentId,
  });
}

export function useUpdateStudentNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ studentId, data }: { studentId: number; data: StudentNoteUpdate }) =>
      studentNotesApi.update(studentId, data),
    onSuccess: (updatedNote) => {
      queryClient.setQueryData<StudentNote | null>(
        studentNotesKeys.get(updatedNote.student_id),
        updatedNote
      );
    },
  });
}

export function useDeleteStudentNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (studentId: number) => studentNotesApi.delete(studentId),
    onMutate: async (studentId) => {
      await queryClient.cancelQueries({ queryKey: studentNotesKeys.get(studentId) });

      const previousNote = queryClient.getQueryData<StudentNote | null>(
        studentNotesKeys.get(studentId)
      );

      queryClient.setQueryData<StudentNote | null>(studentNotesKeys.get(studentId), null);

      return { previousNote, studentId };
    },
    onError: (_err, _studentId, context) => {
      if (context?.previousNote) {
        queryClient.setQueryData(
          studentNotesKeys.get(context.studentId),
          context.previousNote
        );
      }
    },
    onSettled: (_data, _error, studentId) => {
      queryClient.invalidateQueries({ queryKey: studentNotesKeys.get(studentId) });
    },
  });
}

// Hook to get unique students the tutor has worked with based on bookings
export function useTutorStudents() {
  return useQuery({
    queryKey: studentNotesKeys.students(),
    queryFn: async () => {
      // Fetch all bookings as a tutor (completed ones to get students worked with)
      const response = await bookingsApi.list({
        role: 'tutor',
        page_size: 100,
      });

      const bookings = response.bookings ?? [];

      // Extract unique students from bookings
      const studentsMap = new Map<number, TutorStudent>();

      bookings.forEach((booking: Booking) => {
        if (booking.student && !studentsMap.has(booking.student.id)) {
          const existingStudent = studentsMap.get(booking.student.id);
          const bookingDate = new Date(booking.start_at || '');

          if (!existingStudent) {
            studentsMap.set(booking.student.id, {
              id: booking.student.id,
              name: booking.student.name,
              avatar_url: booking.student.avatar_url,
              last_session_date: booking.start_at,
              total_sessions: 1,
            });
          } else {
            // Update if this booking is more recent
            const existingDate = existingStudent.last_session_date
              ? new Date(existingStudent.last_session_date)
              : new Date(0);

            if (bookingDate > existingDate) {
              existingStudent.last_session_date = booking.start_at;
            }
            existingStudent.total_sessions = (existingStudent.total_sessions || 0) + 1;
          }
        } else if (booking.student && studentsMap.has(booking.student.id)) {
          const student = studentsMap.get(booking.student.id)!;
          const bookingDate = new Date(booking.start_at || '');
          const existingDate = student.last_session_date
            ? new Date(student.last_session_date)
            : new Date(0);

          if (bookingDate > existingDate) {
            student.last_session_date = booking.start_at;
          }
          student.total_sessions = (student.total_sessions || 0) + 1;
        }
      });

      // Convert to array and sort by last session date (most recent first)
      return Array.from(studentsMap.values()).sort((a, b) => {
        const dateA = a.last_session_date ? new Date(a.last_session_date).getTime() : 0;
        const dateB = b.last_session_date ? new Date(b.last_session_date).getTime() : 0;
        return dateB - dateA;
      });
    },
  });
}
