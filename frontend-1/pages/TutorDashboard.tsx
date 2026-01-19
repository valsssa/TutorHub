
import React, { useMemo } from 'react';
import { Calendar, ArrowRight, Video, Users, Star, Clock, Plus, CalendarX, Settings, FileText, MessageSquare, User as UserIcon, XCircle, CheckCircle, AlertCircle, ChevronRight, Eye } from 'lucide-react';
import { User, Session, Tutor } from '../domain/types';
import { Badge } from '../components/shared/UI';

interface TutorDashboardProps {
    currentUser: User;
    tutorProfile?: Tutor;
    verificationStatus?: 'verified' | 'pending' | 'rejected' | 'unverified';
    sessions: Session[];
    onStartSession: (session: Session) => void;
    onCancelSession: (sessionId: string) => void;
    onRescheduleSession: (sessionId: string) => void;
    theme: 'dark' | 'light';
    onEditProfile: () => void;
    onViewProfile: () => void;
    onUpdateSchedule: (mode?: 'calendar' | 'setup') => void;
    onQuickAction: (action: 'schedule' | 'timeoff' | 'extraslots') => void;
    onViewCalendar: () => void;
    onManageCalendar: () => void;
    onAcceptRequest: (id: number) => void;
    onDeclineRequest: (id: number) => void;
    onManageVerification: () => void;
    onOpenChat: (userId: string, userName: string) => void;
    onViewEarnings: () => void;
    onViewStudents: () => void;
}

export const TutorDashboard: React.FC<TutorDashboardProps> = ({ 
    currentUser, tutorProfile, verificationStatus = 'unverified', sessions, onStartSession, onCancelSession, onRescheduleSession, theme,
    onEditProfile, onViewProfile, onUpdateSchedule, onQuickAction, onViewCalendar, onManageCalendar,
    onAcceptRequest, onDeclineRequest, onManageVerification, onOpenChat, onViewEarnings, onViewStudents
}) => {
    
    const displaySessions = useMemo(() => {
        const real = sessions.filter(s => s.tutorId === currentUser.id);
        if (real.length > 0) return real;
        // Fallback for demo if no real sessions
        return [
            {
                id: 'demo-1',
                tutorId: currentUser.id,
                tutorName: currentUser.name,
                studentId: 'Luis P.',
                date: new Date().toISOString(), // Today
                status: 'upcoming',
                price: 85,
                subject: 'Physics'
            },
            {
                id: 'demo-2',
                tutorId: currentUser.id,
                tutorName: currentUser.name,
                studentId: 'Elodie C.',
                date: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
                status: 'upcoming',
                price: 85,
                subject: 'Mechanics'
            }
        ] as Session[];
    }, [sessions, currentUser.id, currentUser.name]);
    
    const upcomingSessions = displaySessions.filter(s => s.status === 'upcoming');
    const nextSession = upcomingSessions.length > 0 ? upcomingSessions[0] : null;

    const totalEarnings = currentUser.earnings || 3450;
    const totalStudents = new Set(displaySessions.map(s => s.studentId)).size + 12; // Mock base + actual

    const getRelativeDateLabel = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        const sessionDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        
        if (sessionDate.getTime() === today.getTime()) return 'Today';
        if (sessionDate.getTime() === tomorrow.getTime()) return 'Tomorrow';
        
        const diffTime = sessionDate.getTime() - today.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        if (diffDays > 1 && diffDays < 7) return `In ${diffDays} Days`;
        
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const formatTimeRange = (dateStr: string) => {
        const date = new Date(dateStr);
        const start = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        const end = new Date(date.getTime() + 50 * 60000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        return `${start} – ${end}`;
    }

    // Detailed mock requests
    const pendingRequests = [
        {
            id: 1,
            studentName: 'Mike K.',
            subject: 'Physics',
            topic: 'Thermodynamics',
            date: new Date(Date.now() + 86400000 * 2).toISOString(), // 2 days later
            duration: '1h',
            avatar: 'MK',
            gradient: 'from-purple-500 to-indigo-500'
        },
        {
            id: 2,
            studentName: 'John D.',
            subject: 'Mechanics',
            topic: 'Kinematics & Forces',
            date: new Date(Date.now() + 86400000 * 3).toISOString(), // 3 days later
            duration: '1h',
            avatar: 'JD',
            gradient: 'from-blue-500 to-cyan-500'
        }
    ];

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
                <div>
                    <div className="flex flex-wrap items-center gap-3 mb-2">
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Welcome, {currentUser.name}</h1>
                        
                        {verificationStatus === 'verified' && <Badge variant="verified">Verified Tutor</Badge>}
                        {verificationStatus === 'pending' && <Badge variant="pending">Verification Pending</Badge>}
                        {verificationStatus === 'rejected' && <Badge variant="rejected">Verification Rejected</Badge>}
                        {verificationStatus === 'unverified' && (
                             <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700 px-2 py-0.5 rounded font-medium">
                                Unverified
                             </span>
                        )}
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                         <button 
                            onClick={onManageVerification} 
                            className="text-emerald-600 dark:text-emerald-400 hover:underline hover:text-emerald-700 dark:hover:text-emerald-300 font-medium"
                        >
                            {verificationStatus === 'verified' ? 'View Documents' : 'Manage Documents'}
                        </button>
                        <span className="text-slate-300 dark:text-slate-600">•</span>
                        <p className="text-slate-500 dark:text-slate-400">You have {upcomingSessions.length} upcoming sessions.</p>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button 
                        onClick={onViewProfile}
                        className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
                    >
                        <Eye size={16} /> View Profile
                    </button>
                    <button 
                        onClick={onEditProfile}
                        className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
                    >
                        <UserIcon size={16} /> Edit Profile
                    </button>
                    <button 
                        onClick={() => onUpdateSchedule('calendar')}
                        className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-50 shadow-lg shadow-emerald-500/20 transition-colors flex items-center gap-2"
                    >
                        <Calendar size={16} /> Update Schedule
                    </button>
                </div>
            </div>

            {/* HERO SECTION: Priority Action */}
            {nextSession ? (
                <div className="mb-8 rounded-3xl overflow-hidden relative shadow-xl shadow-emerald-900/10 dark:shadow-black/30">
                    <div className="absolute inset-0 bg-gradient-to-r from-emerald-600 to-teal-700 dark:from-emerald-900 dark:to-teal-950"></div>
                    <div className="absolute right-0 top-0 h-full w-1/2 bg-white/5 skew-x-12 translate-x-20"></div>
                    
                    <div className="relative p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="flex items-center gap-6">
                            <div className="w-20 h-20 bg-white/20 backdrop-blur-md rounded-2xl flex flex-col items-center justify-center text-white border border-white/20 shadow-inner">
                                <span className="text-xs font-bold uppercase tracking-wider opacity-80">{new Date(nextSession.date).toLocaleString('en-US', { month: 'short' })}</span>
                                <span className="text-3xl font-bold">{new Date(nextSession.date).getDate()}</span>
                            </div>
                            <div>
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="px-2 py-0.5 rounded-full bg-white/20 backdrop-blur-sm border border-white/20 text-white text-[10px] font-bold uppercase tracking-wide">Up Next</span>
                                    <span className="text-emerald-100 text-sm font-medium flex items-center gap-1">
                                        <Clock size={14} /> {formatTimeRange(nextSession.date)}
                                    </span>
                                </div>
                                <h2 className="text-2xl sm:text-3xl font-bold text-white mb-1">
                                    {nextSession.subject} with {nextSession.studentId === 's1' ? 'Luis P.' : nextSession.studentId}
                                </h2>
                                <p className="text-emerald-100 text-sm">
                                    Prepare your materials. Class starts in {Math.floor((new Date(nextSession.date).getTime() - Date.now()) / (1000 * 60))} minutes.
                                </p>
                            </div>
                        </div>
                        
                        <div className="flex gap-4 w-full md:w-auto">
                            <button 
                                onClick={() => onQuickAction('schedule')}
                                className="px-6 py-3 rounded-xl border border-white/20 text-white font-semibold hover:bg-white/10 transition-colors flex-1 md:flex-initial text-center"
                            >
                                Reschedule
                            </button>
                            <button 
                                onClick={() => onStartSession(nextSession)}
                                className="px-8 py-3 bg-white text-emerald-900 rounded-xl font-bold hover:bg-emerald-50 transition-colors shadow-lg flex items-center justify-center gap-2 flex-1 md:flex-initial"
                            >
                                <Video size={18} /> Join Classroom
                            </button>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="mb-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 text-center">
                    <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
                        <Calendar size={32} />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">No upcoming sessions</h3>
                    <p className="text-slate-500 dark:text-slate-400 mb-6">Your schedule is clear. Update your availability to get more bookings.</p>
                    <button 
                        onClick={() => onUpdateSchedule('setup')}
                        className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl transition-colors shadow-lg shadow-emerald-500/20"
                    >
                        Update Availability
                    </button>
                </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {/* Earnings */}
                <div 
                    onClick={onViewEarnings}
                    className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group cursor-pointer hover:border-emerald-500 hover:shadow-lg transition-all"
                >
                    <div className="absolute right-0 top-0 w-24 h-24 bg-emerald-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
                    <div className="relative z-10">
                        <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Total Earnings</div>
                        <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">${totalEarnings.toLocaleString()}</div>
                        <div className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                            <span className="flex items-center"><ArrowRight size={12} className="rotate-[-45deg]"/> +12%</span>
                            <span className="text-slate-400 dark:text-slate-500 font-normal">vs last month</span>
                        </div>
                    </div>
                </div>
                {/* Active Students */}
                 <div 
                    onClick={onViewStudents}
                    className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group cursor-pointer hover:border-purple-500 hover:shadow-lg transition-all"
                 >
                    <div className="absolute right-0 top-0 w-24 h-24 bg-purple-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
                    <div className="relative z-10">
                        <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Active Students</div>
                        <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">{totalStudents}</div>
                        <div className="flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400 font-medium">
                            <span>2 new</span>
                            <span className="text-slate-400 dark:text-slate-500 font-normal">this week</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* Left Column (Work Queue) */}
                <div className="xl:col-span-2 space-y-8">
                    
                    {/* Pending Requests */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
                             <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <AlertCircle size={20} className="text-amber-500" /> Pending Requests
                             </h3>
                             <span className="bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-2 py-0.5 rounded text-xs font-bold">{pendingRequests.length} Action Items</span>
                        </div>
                        <div className="divide-y divide-slate-100 dark:divide-slate-800">
                            {pendingRequests.map((req) => (
                                <div key={req.id} className="p-5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                    <div className="flex items-center gap-4">
                                         <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${req.gradient} text-white flex items-center justify-center text-sm font-bold shadow-sm`}>
                                            {req.avatar}
                                         </div>
                                         <div>
                                             <div className="text-base font-bold text-slate-900 dark:text-white mb-0.5">{req.studentName}</div>
                                             <div className="text-sm text-slate-500 flex flex-wrap items-center gap-x-3 gap-y-1">
                                                <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-xs font-medium text-slate-700 dark:text-slate-300">{req.subject}</span>
                                                <span className="text-slate-400 text-xs">{req.topic}</span>
                                             </div>
                                             <div className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 flex items-center gap-2">
                                                <Calendar size={12} /> 
                                                <span>{new Date(req.date).toLocaleDateString(undefined, {weekday: 'short', month: 'short', day: 'numeric'})}</span>
                                                <span className="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-600"></span>
                                                <Clock size={12} />
                                                <span>{new Date(req.date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} ({req.duration})</span>
                                             </div>
                                         </div>
                                    </div>
                                    <div className="flex gap-3 w-full sm:w-auto">
                                        <button 
                                            onClick={() => onDeclineRequest(req.id)}
                                            className="flex-1 sm:flex-none px-4 py-2 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 font-medium transition-colors text-sm"
                                        >
                                            Decline
                                        </button>
                                        <button 
                                            onClick={() => onAcceptRequest(req.id)}
                                            className="flex-1 sm:flex-none px-6 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl hover:opacity-90 font-bold transition-colors shadow-sm text-sm"
                                        >
                                            Accept Request
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Upcoming Sessions List */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
                                <Video size={20} className="text-emerald-500" /> Upcoming Sessions
                            </h3>
                            <button 
                                onClick={onViewCalendar}
                                className="text-sm font-bold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300 transition-colors"
                            >
                                View Calendar
                            </button>
                        </div>
                        
                        <div className="space-y-4">
                            {upcomingSessions.length === 0 ? (
                                <div className="text-center py-12 text-slate-500 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700">
                                    <p>No more sessions scheduled for today.</p>
                                </div>
                            ) : (
                                upcomingSessions.map((session, idx) => {
                                    if (idx === 0) return null; // Skip first as it's in Hero
                                    const studentName = session.studentId === 's1' ? 'Luis P.' : session.studentId;
                                    return (
                                        <div key={session.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl hover:shadow-md transition-all border border-transparent hover:border-emerald-100 dark:hover:border-emerald-900/30 group gap-4">
                                            <div className="flex items-center gap-4">
                                                {/* Avatar */}
                                                <div className="w-12 h-12 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center text-slate-600 dark:text-slate-200 font-bold text-xl shadow-sm border border-slate-300 dark:border-slate-600">
                                                     {studentName.charAt(0).toUpperCase()}
                                                </div>
                                                <div>
                                                    <h4 className="font-bold text-slate-900 dark:text-white text-base">
                                                        {studentName}
                                                    </h4>
                                                    <p className="text-slate-500 dark:text-slate-400 text-sm">
                                                        {getRelativeDateLabel(session.date)}, {formatTimeRange(session.date)}
                                                    </p>
                                                </div>
                                            </div>
                                            
                                            <div className="flex items-center gap-2 text-slate-400 justify-end">
                                                <button className="p-2 hover:bg-white dark:hover:bg-slate-700 rounded-lg hover:text-emerald-600 transition-colors" title="Lesson Plan">
                                                    <FileText size={18} />
                                                </button>
                                                <button 
                                                    onClick={() => onOpenChat(session.studentId, studentName)}
                                                    className="p-2 hover:bg-white dark:hover:bg-slate-700 rounded-lg hover:text-emerald-600 transition-colors" 
                                                    title="Message"
                                                >
                                                    <MessageSquare size={18} />
                                                </button>
                                                
                                                <div className="h-4 w-px bg-slate-300 dark:bg-slate-700 mx-2"></div>
                                                
                                                {/* Text Actions */}
                                                <button 
                                                    onClick={() => onQuickAction('schedule')}
                                                    className="text-xs font-medium text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors px-1" 
                                                >
                                                    Reschedule
                                                </button>
                                                <span className="text-slate-300 dark:text-slate-700">•</span>
                                                <button 
                                                    onClick={() => onCancelSession(session.id)}
                                                    className="text-xs font-medium text-slate-500 hover:text-red-500 transition-colors px-1" 
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Column (Tools & Feedback) */}
                <div className="space-y-8">
                     {/* Quick Schedule / Actions Widget */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                        <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                            <Clock size={20} className="text-emerald-500"/> Quick Schedule
                        </h3>
                        
                        <div className="space-y-3">
                            <button 
                                onClick={() => onQuickAction('schedule')}
                                className="w-full py-3.5 px-4 bg-emerald-600 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 hover:bg-emerald-500 transition-all flex items-center justify-center gap-2"
                            >
                                <Calendar size={18} /> Schedule lesson
                            </button>
                            
                            <button 
                                onClick={() => onQuickAction('timeoff')}
                                className="w-full py-3 px-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center justify-center gap-2"
                            >
                                <CalendarX size={18} /> Add time off
                            </button>
                            
                            <button 
                                onClick={() => onQuickAction('extraslots')}
                                className="w-full py-3 px-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center justify-center gap-2"
                            >
                                <Plus size={18} /> Add extra slots
                            </button>
                            
                            <button 
                                onClick={() => onUpdateSchedule('setup')}
                                className="w-full py-3 px-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center justify-center gap-2"
                            >
                                <Settings size={18} /> Set up availability
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
