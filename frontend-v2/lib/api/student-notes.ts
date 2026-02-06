import { api } from './client';
import type { StudentNote, StudentNoteUpdate } from '@/types/student-note';

export const studentNotesApi = {
  // Get notes for a specific student
  get: (studentId: number) =>
    api.get<StudentNote | null>(`/tutor/student-notes/${studentId}`),

  // Create or update notes for a student
  update: (studentId: number, data: StudentNoteUpdate) =>
    api.put<StudentNote>(`/tutor/student-notes/${studentId}`, data),

  // Delete notes for a student
  delete: (studentId: number) =>
    api.delete<{ message: string }>(`/tutor/student-notes/${studentId}`),
};
