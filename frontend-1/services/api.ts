
import * as mock from './mockData';
import { Tutor, Session, User, VerificationRequest, ChatThread, UserRole, TutorStudent } from '../domain/types';

// Simulate network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const api = {
  auth: {
    login: async (email: string, role: UserRole): Promise<User> => {
        await delay(500);
        // Simplified mock login logic based on role for demo purposes
        if (role === UserRole.TUTOR) return mock.MOCK_TUTOR_USER;
        if (role === UserRole.ADMIN) return mock.MOCK_ADMIN;
        if (role === UserRole.OWNER) return mock.MOCK_OWNER;
        return mock.MOCK_STUDENT;
    },
    getCurrentUser: async (): Promise<User> => {
        await delay(200);
        return mock.MOCK_STUDENT;
    }
  },
  tutors: {
    getAll: async (): Promise<Tutor[]> => {
        await delay(300);
        return [...mock.MOCK_TUTORS];
    },
    getStudents: async (tutorId: string): Promise<TutorStudent[]> => {
        await delay(200);
        return [...mock.MOCK_TUTOR_STUDENTS];
    }
  },
  sessions: {
    getAll: async (): Promise<Session[]> => {
         await delay(200);
         return [...mock.MOCK_SESSIONS];
    }
  },
  verification: {
    getRequests: async (): Promise<VerificationRequest[]> => {
        await delay(200);
        return [...mock.MOCK_VERIFICATION_REQUESTS];
    }
  },
  chats: {
    getThreads: async (): Promise<ChatThread[]> => {
        await delay(100);
        return [...mock.MOCK_CHATS];
    }
  }
};
