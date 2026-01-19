
import React from 'react';
import { Wallet, Calendar, Clock, Video, XCircle } from 'lucide-react';
import { User, Session } from '../domain/types';

interface StudentLessonsPageProps {
    currentUser: User;
    sessions: Session[];
    onStartSession: (session: Session) => void;
    onCancelSession: (sessionId: string) => void;
    onReviewSession: (sessionId: string) => void;
    onTopUp: () => void;
}

export const StudentLessonsPage: React.FC<StudentLessonsPageProps> = ({ 
    currentUser, sessions, onStartSession, onCancelSession, onReviewSession, onTopUp
}) => {
    const mySessions = sessions.filter(s => s.studentId === currentUser.id);

    return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
        <h1 className="text-3xl font-bold mb-2 text-slate-900 dark:text-white">My Lessons</h1>
        <p className="text-slate-600 dark:text-slate-400 mb-8">Manage your upcoming schedule and past lessons.</p>

        {/* Wallet Section - Useful context for lessons */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 flex flex-col sm:flex-row justify-between items-center mb-10 gap-4">
            <div>
                <h3 className="text-slate-500 dark:text-slate-400 font-medium mb-1">Available Balance</h3>
                <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-slate-900 dark:text-white">${currentUser.balance?.toFixed(2)}</span>
                    <span className="text-sm text-slate-400">USD</span>
                </div>
            </div>
            <button 
                onClick={onTopUp}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-lg font-bold flex items-center gap-2 transition-all shadow-lg shadow-emerald-500/20"
            >
                <Wallet size={18} /> Top up wallet
            </button>
        </div>

        <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-slate-900 dark:text-white"><Calendar size={20}/> Your Schedule</h2>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            {mySessions.length === 0 ? (
                <div className="p-12 text-center">
                    <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
                        <Calendar size={32} />
                    </div>
                    <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">No sessions booked</h3>
                    <p className="text-slate-500 dark:text-slate-400">Book your first lesson from the marketplace to get started.</p>
                </div>
            ) : mySessions.map((session, idx) => (
                <div key={session.id} className={`p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 ${idx !== mySessions.length - 1 ? 'border-b border-slate-200 dark:border-slate-800' : ''}`}>
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 text-xl">
                            {session.subject === 'Mathematics' ? '∫' : session.subject === 'Physics' ? '⚛' : session.subject.charAt(0)}
                        </div>
                        <div>
                            <h4 className="font-semibold text-lg text-slate-900 dark:text-white">{session.subject} with {session.tutorName}</h4>
                            <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400 mt-1">
                                <span className="flex items-center gap-1.5"><Calendar size={14} className="text-emerald-500"/> {new Date(session.date).toLocaleDateString()}</span>
                                <span className="flex items-center gap-1.5"><Clock size={14} className="text-emerald-500"/> {new Date(session.date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        {session.status === 'upcoming' ? (
                            <>
                                <button 
                                    onClick={() => onStartSession(session)}
                                    className="w-full md:w-auto bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-lg font-bold transition-colors flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20"
                                >
                                    <Video size={18} /> Join Classroom
                                </button>
                                <button 
                                    onClick={() => onCancelSession(session.id)}
                                    className="p-2.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                    title="Cancel Session"
                                >
                                    <XCircle size={20} />
                                </button>
                            </>
                        ) : session.status === 'completed' && !session.isReviewed ? (
                            <button 
                                onClick={() => onReviewSession(session.id)}
                                className="w-full md:w-auto border-2 border-emerald-500/50 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 px-6 py-2 rounded-lg font-bold transition-colors"
                            >
                                Rate & Review
                            </button>
                        ) : (
                             <span className="inline-block px-4 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-sm font-medium">
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