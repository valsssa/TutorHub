
import React, { createContext, useContext, useState, useEffect } from 'react';
import { Tutor, Session, VerificationRequest, ChatThread, AdminProfile, TutorStudent, User } from '../domain/types';
import { api } from '../services/api';

interface DataContextType {
    tutors: Tutor[];
    sessions: Session[];
    verificationRequests: VerificationRequest[];
    chats: ChatThread[];
    admins: AdminProfile[];
    students: TutorStudent[];
    refreshTutors: () => void;
    updateTutor: (tutor: Tutor) => void;
    addSession: (session: Session) => void;
    updateVerificationStatus: (id: string, status: 'approved' | 'rejected') => void;
    sendMessage: (threadId: string, text: string, userId: string) => void;
    createThread: (participantId: string, participantName: string, participantAvatar: string) => string;
    addAdmin: (admin: AdminProfile) => void;
    removeAdmin: (id: string) => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [tutors, setTutors] = useState<Tutor[]>([]);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [verificationRequests, setVerificationRequests] = useState<VerificationRequest[]>([]);
    const [chats, setChats] = useState<ChatThread[]>([]);
    const [students, setStudents] = useState<TutorStudent[]>([]);
    
    // Mock local-only state for admins as it's not in the main API mock yet
    const [admins, setAdmins] = useState<AdminProfile[]>([
        { id: 'a1', name: 'System Admin', email: 'admin@edu.com', role: 'ADMIN', status: 'Active', joinedDate: '2023-01-15' },
        { id: 'a2', name: 'Sarah Moderator', email: 'sarah@edu.com', role: 'MODERATOR', status: 'Active', joinedDate: '2023-03-10' }
    ]);

    useEffect(() => {
        const loadInitialData = async () => {
            try {
                const [tutorsData, sessionsData, verificationsData, chatsData] = await Promise.all([
                    api.tutors.getAll(),
                    api.sessions.getAll(),
                    api.verification.getRequests(),
                    api.chats.getThreads()
                ]);
                setTutors(tutorsData);
                setSessions(sessionsData);
                setVerificationRequests(verificationsData);
                setChats(chatsData);
                
                // For demo purposes, just load static mock students. In real app, this depends on the logged-in tutor
                const studentsData = await api.tutors.getStudents('t1');
                setStudents(studentsData);
            } catch (error) {
                console.error("Failed to load initial data", error);
            }
        };
        loadInitialData();
    }, []);

    const refreshTutors = async () => {
        const data = await api.tutors.getAll();
        setTutors(data);
    };

    const updateTutor = (updatedTutor: Tutor) => {
        setTutors(prev => prev.map(t => t.id === updatedTutor.id ? updatedTutor : t));
    };

    const addSession = (newSession: Session) => {
        setSessions(prev => [...prev, newSession]);
    };

    const updateVerificationStatus = (id: string, status: 'approved' | 'rejected') => {
        setVerificationRequests(prev => prev.map(r => r.id === id ? { ...r, status } : r));
        
        // If approved, verify the tutor
        if (status === 'approved') {
            const req = verificationRequests.find(r => r.id === id);
            if (req) {
                setTutors(prev => prev.map(t => t.id === req.tutorId ? { ...t, isVerified: true } : t));
            }
        }
    };

    const sendMessage = (threadId: string, text: string, userId: string) => {
        setChats(prev => prev.map(chat => {
            if (chat.id === threadId) {
                return {
                    ...chat,
                    lastMessage: text,
                    lastUpdated: new Date().toISOString(),
                    messages: [...chat.messages, {
                        id: `m-${Date.now()}`,
                        senderId: userId,
                        text,
                        timestamp: new Date().toISOString()
                    }]
                };
            }
            return chat;
        }));
    };

    const createThread = (participantId: string, participantName: string, participantAvatar: string) => {
        // Check if thread already exists
        const existingThread = chats.find(c => c.participantId === participantId);
        if (existingThread) return existingThread.id;

        const newId = `chat-${Date.now()}`;
        const newThread: ChatThread = {
            id: newId,
            participantId,
            participantName,
            participantAvatar,
            lastMessage: '',
            lastUpdated: new Date().toISOString(),
            unreadCount: 0,
            messages: []
        };
        setChats(prev => [newThread, ...prev]);
        return newId;
    };

    const addAdmin = (admin: AdminProfile) => setAdmins(prev => [...prev, admin]);
    const removeAdmin = (id: string) => setAdmins(prev => prev.filter(a => a.id !== id));

    return (
        <DataContext.Provider value={{ 
            tutors, sessions, verificationRequests, chats, admins, students,
            refreshTutors, updateTutor, addSession, updateVerificationStatus, sendMessage, createThread, addAdmin, removeAdmin
        }}>
            {children}
        </DataContext.Provider>
    );
};

export const useData = () => {
    const context = useContext(DataContext);
    if (!context) throw new Error("useData must be used within a DataProvider");
    return context;
};
