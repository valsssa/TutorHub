
import React from 'react';
import { Wallet, Heart, Calendar, Clock, Video } from 'lucide-react';
import { User, Session, Tutor } from '../../types';
import { TutorCard } from '../marketplace/TutorCard';

interface StudentDashboardProps {
    currentUser: User;
    sessions: Session[];
    savedTutors: Tutor[];
    onStartSession: (session: Session) => void;
    onReviewSession: (sessionId: string) => void;
    onViewProfile: (tutor: Tutor) => void;
    onToggleSave: (e: React.MouseEvent, id: string) => void;
    onBook: (e: React.MouseEvent, tutor: Tutor) => void;
    onQuickBook: (e: React.MouseEvent, tutor: Tutor) => void;
    onSlotBook: (e: React.MouseEvent, tutor: Tutor, slot: string) => void;
    onMessage: (e: React.MouseEvent, tutor: Tutor) => void;
    onTopUp: () => void;
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({ 
    currentUser, sessions, savedTutors, onStartSession, onReviewSession,
    onViewProfile, onToggleSave, onBook, onQuickBook, onSlotBook, onMessage, onTopUp
}) => {
    const mySessions = sessions.filter(s => s.studentId === currentUser.id);

    return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
        <h1 className="text-3xl font-bold mb-2 text-slate-900 dark:text-white">Student Dashboard</h1>
        <p className="text-slate-600 dark:text-slate-400 mb-8">Welcome back, {currentUser.name}</p>

        <div className="grid grid-cols-1 gap-8 mb-12">
             <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
                <div>
                    <h3 className="text-slate-500 dark:text-slate-400 font-medium mb-1">Available Credits</h3>
                    <div className="text-3xl font-bold text-slate-900 dark:text-white">${currentUser.balance}</div>
                </div>
                <button 
                    onClick={onTopUp}
                    className="self-start text-sm text-emerald-600 dark:text-emerald-400 hover:text-emerald-500 dark:hover:text-emerald-300 font-medium flex items-center gap-1 mt-4 hover:underline transition-all"
                >
                    <Wallet size={16} /> Top up wallet
                </button>
            </div>
        </div>
        
        {savedTutors.length > 0 && (
          <div className="mb-12">
             <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-slate-900 dark:text-white"><Heart size={20} className="text-emerald-500"/> Saved Tutors</h2>
             <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {savedTutors.map(tutor => (
                    <TutorCard 
                        key={tutor.id} 
                        tutor={tutor} 
                        onViewProfile={onViewProfile}
                        onToggleSave={onToggleSave}
                        onBook={onBook}
                        onQuickBook={onQuickBook}
                        onSlotBook={onSlotBook}
                        onMessage={onMessage}
                        isSaved={true}
                    />
                ))}
             </div>
          </div>
        )}

        <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-slate-900 dark:text-white"><Calendar size={20}/> Your Sessions</h2>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden">
            {mySessions.length === 0 ? (
                <div className="p-8 text-center text-slate-500">No sessions booked yet.</div>
            ) : mySessions.map((session, idx) => (
                <div key={session.id} className={`p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 ${idx !== mySessions.length - 1 ? 'border-b border-slate-200 dark:border-slate-800' : ''}`}>
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400">
                            {session.subject === 'Mathematics' ? '∫' : session.subject === 'Physics' ? '⚛' : '💻'}
                        </div>
                        <div>
                            <h4 className="font-semibold text-slate-900 dark:text-white">{session.subject} with {session.tutorName}</h4>
                            <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400 mt-1">
                                <span className="flex items-center gap-1"><Calendar size={14}/> {new Date(session.date).toLocaleDateString()}</span>
                                <span className="flex items-center gap-1"><Clock size={14}/> {new Date(session.date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                            </div>
                        </div>
                    </div>
                    <div>
                        {session.status === 'upcoming' ? (
                            <button 
                                onClick={() => onStartSession(session)}
                                className="w-full md:w-auto bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(5,150,105,0.4)] hover:-translate-y-0.5"
                            >
                                <Video size={18} /> Join Classroom
                            </button>
                        ) : session.status === 'completed' && !session.isReviewed ? (
                            <button 
                                onClick={() => onReviewSession(session.id)}
                                className="w-full md:w-auto border border-emerald-500/50 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 px-6 py-2 rounded-lg font-medium transition-colors"
                            >
                                Rate & Review
                            </button>
                        ) : (
                             <span className="inline-block px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-sm">
                                {session.isReviewed ? 'Reviewed' : 'Completed'}
                             </span>
                        )}
                    </div>
                </div>
            ))}
        </div>
    </div>
    );
};
