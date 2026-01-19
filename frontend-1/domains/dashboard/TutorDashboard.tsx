
import React, { useMemo } from 'react';
import { Calendar, ArrowRight, Video, Users, Star, Clock, BarChart2, Plus, CalendarX, Settings, FileText, MessageSquare, User as UserIcon } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { User, Session, Tutor } from '../../types';
import { MOCK_TUTORS } from '../../constants';
import { Badge } from '../../components/shared/UI';

interface TutorDashboardProps {
    currentUser: User;
    tutorProfile?: Tutor;
    verificationStatus?: 'verified' | 'pending' | 'rejected' | 'unverified';
    sessions: Session[];
    onStartSession: (session: Session) => void;
    theme: 'dark' | 'light';
    onEditProfile: () => void;
    onUpdateSchedule: (mode?: 'calendar' | 'setup') => void; // Update to accept mode
    onQuickAction: (action: 'schedule' | 'timeoff' | 'extraslots') => void;
    onViewCalendar: () => void;
    onManageCalendar: () => void;
    onAcceptRequest: (id: number) => void;
    onDeclineRequest: (id: number) => void;
    onManageVerification: () => void;
    onOpenChat: (userId: string, userName: string) => void;
}

export const TutorDashboard: React.FC<TutorDashboardProps> = ({ 
    currentUser, tutorProfile, verificationStatus = 'unverified', sessions, onStartSession, theme,
    onEditProfile, onUpdateSchedule, onQuickAction, onViewCalendar, onManageCalendar,
    onAcceptRequest, onDeclineRequest, onManageVerification, onOpenChat
}) => {
    
    const displaySessions = useMemo(() => {
        const real = sessions.filter(s => s.tutorId === currentUser.id);
        if (real.length > 0) return real;
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
            },
            {
                id: 'demo-3',
                tutorId: currentUser.id,
                tutorName: currentUser.name,
                studentId: 'Elodie C.',
                date: new Date(Date.now() + 259200000).toISOString(), // 3 days
                status: 'upcoming',
                price: 85,
                subject: 'Mechanics'
            }
        ] as Session[];
    }, [sessions, currentUser.id, currentUser.name]);
    
    const upcomingSessions = displaySessions.filter(s => s.status === 'upcoming');
    const pastSessions = displaySessions.filter(s => s.status === 'completed');

    const totalEarnings = currentUser.earnings || 3450;
    const hoursTaught = pastSessions.length || 42; 
    const totalStudents = new Set(displaySessions.map(s => s.studentId)).size + 12;
    const rating = 4.9; 

    const data = [
        { name: 'Jan', earnings: 400 },
        { name: 'Feb', earnings: 300 },
        { name: 'Mar', earnings: 600 },
        { name: 'Apr', earnings: 800 },
        { name: 'May', earnings: 500 },
        { name: 'Jun', earnings: 850 },
    ];

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

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Tutor Command Center</h1>
                    <div className="flex flex-wrap items-center gap-3 mt-2">
                        <p className="text-lg text-slate-700 dark:text-slate-300 font-medium">Welcome, {currentUser.name}</p>
                        
                        {verificationStatus === 'verified' && <Badge variant="verified">Verified Tutor</Badge>}
                        {verificationStatus === 'pending' && <Badge variant="pending">Verification Pending</Badge>}
                        {verificationStatus === 'rejected' && <Badge variant="rejected">Verification Rejected</Badge>}
                        {verificationStatus === 'unverified' && (
                             <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700 px-2 py-0.5 rounded font-medium">
                                Unverified
                             </span>
                        )}
                        
                        <button 
                            onClick={onManageVerification} 
                            className="text-xs text-emerald-600 dark:text-emerald-400 hover:underline hover:text-emerald-700 dark:hover:text-emerald-300 font-medium ml-1"
                        >
                            {verificationStatus === 'verified' ? 'View Documents' : 'Manage Documents'}
                        </button>
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">You have {upcomingSessions.length} upcoming sessions.</p>
                </div>
                <div className="flex gap-3">
                    <button 
                        onClick={onEditProfile}
                        className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                    >
                        Edit Profile
                    </button>
                    <button 
                        onClick={() => onUpdateSchedule('calendar')}
                        className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-500 shadow-lg shadow-emerald-500/20 transition-colors flex items-center gap-2"
                    >
                        <Calendar size={16} /> Update Schedule
                    </button>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {/* Earnings */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
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
                {/* Hours */}
                 <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
                    <div className="absolute right-0 top-0 w-24 h-24 bg-blue-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
                    <div className="relative z-10">
                        <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Hours Taught</div>
                        <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">{hoursTaught}h</div>
                         <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 font-medium">
                            <span className="flex items-center"><ArrowRight size={12} className="rotate-[-45deg]"/> +5.2h</span>
                            <span className="text-slate-400 dark:text-slate-500 font-normal">vs last month</span>
                        </div>
                    </div>
                </div>
                {/* Active Students */}
                 <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
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
                 {/* Rating */}
                 <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
                    <div className="absolute right-0 top-0 w-24 h-24 bg-amber-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
                    <div className="relative z-10">
                        <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Overall Rating</div>
                        <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                            {rating} <Star size={24} className="text-amber-500 fill-amber-500"/>
                        </div>
                         <div className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 font-medium">
                            <span>Top 5%</span>
                            <span className="text-slate-400 dark:text-slate-500 font-normal">of tutors</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* Left Column */}
                <div className="xl:col-span-2 space-y-8">
                    
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
                                See all
                            </button>
                        </div>
                        
                        <div className="space-y-4">
                            {upcomingSessions.length === 0 ? (
                                <div className="text-center py-8 text-slate-500">
                                    No upcoming sessions.
                                </div>
                            ) : (
                                upcomingSessions.map(session => {
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
                                            
                                            <div className="flex items-center gap-4 text-slate-400 justify-end">
                                                <button className="p-2 hover:bg-white dark:hover:bg-slate-700 rounded-lg hover:text-emerald-600 transition-colors shadow-sm" title="Lesson Plan">
                                                    <FileText size={20} />
                                                </button>
                                                <button 
                                                    onClick={() => onStartSession(session)} 
                                                    className="p-2 hover:bg-white dark:hover:bg-slate-700 rounded-lg hover:text-emerald-600 transition-colors shadow-sm" 
                                                    title="Start Video Call"
                                                >
                                                    <Video size={20} />
                                                </button>
                                                <button 
                                                    onClick={() => onOpenChat(session.studentId, studentName)}
                                                    className="p-2 hover:bg-white dark:hover:bg-slate-700 rounded-lg hover:text-emerald-600 transition-colors shadow-sm" 
                                                    title="Message"
                                                >
                                                    <MessageSquare size={20} />
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>

                    {/* Earnings Chart */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
                                <BarChart2 size={20} className="text-emerald-500"/> Revenue Analytics
                            </h3>
                            <select className="bg-slate-100 dark:bg-slate-800 border-none rounded-lg text-sm px-3 py-1 text-slate-600 dark:text-slate-300 focus:ring-0">
                                <option>Last 6 Months</option>
                                <option>Last Year</option>
                            </select>
                        </div>
                        <div className="h-80 w-full">
                            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                                <BarChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.1} vertical={false} />
                                    <XAxis dataKey="name" stroke="#64748b" axisLine={false} tickLine={false} dy={10} fontSize={12} />
                                    <YAxis stroke="#64748b" axisLine={false} tickLine={false} tickFormatter={(value) => `$${value}`} fontSize={12} />
                                    <RechartsTooltip 
                                        cursor={{fill: theme === 'dark' ? '#1e293b' : '#f1f5f9'}}
                                        contentStyle={{ backgroundColor: theme === 'dark' ? '#0f172a' : '#ffffff', borderColor: theme === 'dark' ? '#1e293b' : '#e2e8f0', borderRadius: '0.5rem', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Bar dataKey="earnings" fill="#10b981" radius={[4, 4, 0, 0]} barSize={40} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                {/* Right Column */}
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

                    {/* Pending Requests */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                        <div className="p-4 border-b border-slate-200 dark:border-slate-800">
                             <h3 className="font-bold text-slate-900 dark:text-white text-sm uppercase tracking-wide">Pending Requests</h3>
                        </div>
                        <div className="divide-y divide-slate-100 dark:divide-slate-800">
                            {[1, 2].map((_, i) => (
                                <div key={i} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-2">
                                             <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 text-white flex items-center justify-center text-xs font-bold">
                                                {i === 0 ? 'MK' : 'JD'}
                                             </div>
                                             <div>
                                                 <div className="text-sm font-semibold text-slate-900 dark:text-white">{i === 0 ? 'Mike K.' : 'John D.'}</div>
                                                 <div className="text-xs text-slate-500">Physics • 1h</div>
                                             </div>
                                        </div>
                                        <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded">Pending</span>
                                    </div>
                                    <div className="flex gap-2 mt-3">
                                        <button 
                                            onClick={() => onAcceptRequest(i)}
                                            className="flex-1 py-1.5 text-xs bg-emerald-600 text-white rounded hover:bg-emerald-500"
                                        >
                                            Accept
                                        </button>
                                        <button 
                                            onClick={() => onDeclineRequest(i)}
                                            className="flex-1 py-1.5 text-xs border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 rounded hover:bg-slate-50 dark:hover:bg-slate-800"
                                        >
                                            Decline
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                     {/* Recent Reviews */}
                     <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                        <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-4">Recent Reviews</h3>
                        <div className="space-y-4">
                            {MOCK_TUTORS[0].reviewsList.slice(0, 2).map(review => (
                                <div key={review.id} className="pb-4 border-b border-slate-100 dark:border-slate-800 last:border-0 last:pb-0">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm font-medium text-slate-900 dark:text-white">{review.studentName}</span>
                                        <span className="text-xs text-slate-500">{new Date(review.date).toLocaleDateString()}</span>
                                    </div>
                                    <div className="flex mb-1">
                                        {[...Array(5)].map((_, i) => (
                                            <Star key={i} size={10} fill={i < review.rating ? "currentColor" : "none"} className={i < review.rating ? "text-amber-500" : "text-slate-300"} />
                                        ))}
                                    </div>
                                    <p className="text-xs text-slate-600 dark:text-slate-400 italic">"{review.comment}"</p>
                                </div>
                            ))}
                        </div>
                     </div>
                </div>
            </div>
        </div>
    );
};
