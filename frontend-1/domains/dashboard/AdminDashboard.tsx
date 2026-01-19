
import React, { useMemo, useState } from 'react';
import { 
    Users, DollarSign, FileText, CheckCircle, XCircle, 
    TrendingUp, Activity, Shield, Download, Eye, Upload, Calendar, Search, AlertTriangle, Trash2, Key
} from 'lucide-react';
import { 
    AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { VerificationRequest, Session, User, Tutor, UserRole } from '../../types';
import { Modal } from '../../components/shared/UI';
import { Badge } from '../../components/shared/UI';

interface AdminDashboardProps {
    currentUser: User;
    verificationRequests: VerificationRequest[];
    sessions: Session[];
    users: User[]; // implied total count based on mock logic
    tutors: Tutor[];
    onApproveVerification: (id: string) => void;
    onRejectVerification: (id: string) => void;
    onViewProfile?: (tutor: Tutor) => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ 
    currentUser, verificationRequests, sessions, tutors, onApproveVerification, onRejectVerification, onViewProfile
}) => {
    const [selectedRequest, setSelectedRequest] = useState<VerificationRequest | null>(null);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<'requests' | 'tutors'>('requests');
    const isOwner = currentUser.role === UserRole.OWNER;
    
    // --- Computed Stats ---
    const pendingRequests = verificationRequests.filter(r => r.status === 'pending');
    
    // Calculate Platform Revenue (Assuming 15% platform fee)
    const platformRevenue = useMemo(() => {
        const totalVolume = sessions.reduce((acc, session) => acc + session.price, 0);
        return totalVolume * 0.15;
    }, [sessions]);

    // Find the tutor object associated with the selected verification request
    const reviewTutor = useMemo(() => 
        selectedRequest ? tutors.find(t => t.id === selectedRequest.tutorId) : null, 
    [selectedRequest, tutors]);

    const stats = [
        { 
            label: 'Platform Revenue', 
            value: `$${platformRevenue.toLocaleString(undefined, {minimumFractionDigits: 2})}`, 
            icon: DollarSign, 
            color: 'text-emerald-600', 
            bg: 'bg-emerald-100 dark:bg-emerald-900/30',
            trend: '+12.5%'
        },
        { 
            label: 'Pending Verifications', 
            value: pendingRequests.length, 
            icon: Shield, 
            color: 'text-amber-600', 
            bg: 'bg-amber-100 dark:bg-amber-900/30',
            trend: 'Action Required'
        },
        { 
            label: 'Total Sessions', 
            value: sessions.length, 
            icon: Activity, 
            color: 'text-blue-600', 
            bg: 'bg-blue-100 dark:bg-blue-900/30',
            trend: '+8.2%'
        },
        { 
            label: 'Active Tutors', 
            value: tutors.length, 
            icon: Users, 
            color: 'text-purple-600', 
            bg: 'bg-purple-100 dark:bg-purple-900/30',
            trend: '+4 this week'
        },
    ];

    // Mock Data for Daily Revenue
    const dailyRevenueData = [
        { name: 'Mon', revenue: 120 },
        { name: 'Tue', revenue: 180 },
        { name: 'Wed', revenue: 150 },
        { name: 'Thu', revenue: 240 },
        { name: 'Fri', revenue: 300 },
        { name: 'Sat', revenue: 380 },
        { name: 'Sun', revenue: 210 },
    ];

    // Mock Data for Monthly Earnings
    const monthlyRevenueData = [
        { name: 'Jan', earnings: 4500, expenses: 1200 },
        { name: 'Feb', earnings: 5200, expenses: 1300 },
        { name: 'Mar', earnings: 4800, expenses: 1100 },
        { name: 'Apr', earnings: 6100, expenses: 1400 },
        { name: 'May', earnings: 5900, expenses: 1600 },
        { name: 'Jun', earnings: 7200, expenses: 1500 },
    ];

    const handleApprove = (id: string) => {
        onApproveVerification(id);
        setSelectedRequest(null);
    };

    const handleReject = (id: string) => {
        onRejectVerification(id);
        setSelectedRequest(null);
    };

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            <div className="mb-8 flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        Admin Overview
                        {isOwner && (
                            <span className="text-xs bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-2 py-1 rounded uppercase tracking-wider font-bold">Owner Access</span>
                        )}
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400">Platform performance and moderation queue.</p>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {stats.map((stat, idx) => (
                    <div key={idx} className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <div className="flex justify-between items-start mb-4">
                            <div className={`p-3 rounded-xl ${stat.bg} ${stat.color}`}>
                                <stat.icon size={24} />
                            </div>
                            <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded-full">
                                {stat.trend}
                            </span>
                        </div>
                        <h3 className="text-slate-500 dark:text-slate-400 text-sm font-medium">{stat.label}</h3>
                        <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{stat.value}</p>
                    </div>
                ))}
            </div>

            {/* OWNER ONLY SECTION */}
            {isOwner && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8 animate-in slide-in-from-top-4 duration-500">
                    {/* Platform Billing & Legal */}
                    <div className="bg-slate-900 dark:bg-slate-800 rounded-2xl p-6 border border-slate-800 dark:border-slate-700 shadow-lg text-white">
                        <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                            <Key size={20} className="text-yellow-400"/> Owner Controls
                        </h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-white/10 p-4 rounded-xl">
                                <p className="text-xs text-slate-400 uppercase tracking-wide font-bold mb-1">Platform Billing</p>
                                <p className="text-2xl font-bold">$12,450.00</p>
                                <p className="text-xs text-slate-400 mt-1">Next payout: Oct 31</p>
                            </div>
                            <div className="bg-white/10 p-4 rounded-xl">
                                <p className="text-xs text-slate-400 uppercase tracking-wide font-bold mb-1">Stripe Connect</p>
                                <div className="flex items-center gap-2 text-emerald-400 font-bold">
                                    <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
                                    Operational
                                </div>
                                <p className="text-xs text-slate-400 mt-1">v2023-10-16</p>
                            </div>
                        </div>
                        <div className="mt-4 flex gap-3">
                            <button className="flex-1 py-2 bg-white text-slate-900 rounded-lg text-sm font-bold hover:bg-slate-200 transition-colors">
                                Manage Admins
                            </button>
                            <button className="flex-1 py-2 border border-white/20 text-white rounded-lg text-sm font-bold hover:bg-white/10 transition-colors">
                                Legal & Compliance
                            </button>
                        </div>
                    </div>

                    {/* Danger Zone */}
                    <div className="bg-red-50 dark:bg-red-900/10 rounded-2xl p-6 border border-red-100 dark:border-red-900/30">
                        <h3 className="font-bold text-lg mb-4 flex items-center gap-2 text-red-700 dark:text-red-400">
                            <AlertTriangle size={20} /> Danger Zone
                        </h3>
                        <p className="text-sm text-red-600/80 dark:text-red-300 mb-6">
                            Actions here can have destructive effects on the organization. Proceed with extreme caution.
                        </p>
                        
                        <div className="space-y-3">
                            <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-900 rounded-lg border border-red-100 dark:border-red-900/30">
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Pause All Withdrawals</span>
                                <button className="px-3 py-1 bg-red-100 text-red-700 rounded text-xs font-bold hover:bg-red-200 transition-colors">Pause</button>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-900 rounded-lg border border-red-100 dark:border-red-900/30">
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Delete Organization</span>
                                <button className="px-3 py-1 bg-red-600 text-white rounded text-xs font-bold hover:bg-red-700 transition-colors">Delete</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                
                {/* --- Left Column: Tutor Management & Queue --- */}
                <div className="xl:col-span-2 space-y-8">
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden min-h-[500px]">
                        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                            <div className="flex items-center gap-2">
                                <FileText size={20} className="text-emerald-500"/> 
                                <h2 className="text-lg font-bold text-slate-900 dark:text-white">Tutor Management</h2>
                            </div>
                            
                            <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                                <button 
                                    onClick={() => setActiveTab('requests')}
                                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === 'requests' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'}`}
                                >
                                    Queue <span className="ml-1 px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 rounded-full text-[10px]">{pendingRequests.length}</span>
                                </button>
                                <button 
                                    onClick={() => setActiveTab('tutors')}
                                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === 'tutors' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'}`}
                                >
                                    All Profiles <span className="ml-1 px-1.5 py-0.5 bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-full text-[10px]">{tutors.length}</span>
                                </button>
                            </div>

                            {activeTab === 'requests' && (
                                <button 
                                    onClick={() => setIsUploadModalOpen(true)}
                                    className="hidden sm:flex text-sm items-center gap-1 text-slate-500 hover:text-emerald-600 transition-colors"
                                >
                                    <Upload size={14} /> Upload
                                </button>
                            )}
                        </div>
                        
                        {activeTab === 'requests' ? (
                            <>
                                {pendingRequests.length === 0 ? (
                                    <div className="p-12 text-center text-slate-500">
                                        <CheckCircle size={48} className="mx-auto text-emerald-500 mb-4 opacity-50"/>
                                        <p>All caught up! No pending verifications.</p>
                                    </div>
                                ) : (
                                    <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                        {pendingRequests.map(request => (
                                            <div key={request.id} className="p-6 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-3 mb-2">
                                                            <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-bold text-slate-600 dark:text-slate-300">
                                                                {request.tutorName.charAt(0)}
                                                            </div>
                                                            <div>
                                                                <h3 className="font-bold text-slate-900 dark:text-white">{request.tutorName}</h3>
                                                                <p className="text-xs text-slate-500">{request.email}</p>
                                                            </div>
                                                        </div>
                                                        
                                                        <div className="flex gap-4 text-sm mt-2">
                                                            <div>
                                                                <span className="text-slate-400 text-xs">Subject: </span>
                                                                <span className="font-medium text-slate-700 dark:text-slate-300">{request.subject}</span>
                                                            </div>
                                                            <div>
                                                                <span className="text-slate-400 text-xs">Date: </span>
                                                                <span className="font-medium text-slate-700 dark:text-slate-300">{request.submittedDate}</span>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <button 
                                                        onClick={() => setSelectedRequest(request)}
                                                        className="bg-slate-100 dark:bg-slate-800 hover:bg-emerald-600 hover:text-white text-slate-700 dark:text-slate-300 px-4 py-2 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-all"
                                                    >
                                                        <Eye size={16} /> Review
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                {tutors.map(tutor => (
                                    <div key={tutor.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <img src={tutor.imageUrl} alt={tutor.name} className="w-12 h-12 rounded-full object-cover border border-slate-200 dark:border-slate-700" />
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <h3 className="font-bold text-slate-900 dark:text-white">{tutor.name}</h3>
                                                        <Badge variant={tutor.isVerified ? 'verified' : 'default'}>
                                                            {tutor.isVerified ? 'Verified' : 'Unverified'}
                                                        </Badge>
                                                    </div>
                                                    <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                                                        <span>{tutor.subject}</span>
                                                        <span>•</span>
                                                        <span>${tutor.hourlyRate}/hr</span>
                                                        <span>•</span>
                                                        <span className="flex items-center gap-1"><Users size={12}/> {tutor.reviews} reviews</span>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <button 
                                                onClick={() => onViewProfile && onViewProfile(tutor)}
                                                className="text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                                                title="View Profile"
                                            >
                                                <Eye size={20} />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* --- Right Column: Financials --- */}
                <div className="space-y-8">
                    
                    {/* Revenue Trend (Daily) */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <TrendingUp size={20} className="text-emerald-500"/> Daily Trend
                            </h3>
                            <span className="text-xs text-slate-500">Last 7 Days</span>
                        </div>
                        <div className="h-48 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={dailyRevenueData}>
                                    <defs>
                                        <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                            <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.1} vertical={false} />
                                    <XAxis dataKey="name" stroke="#64748b" axisLine={false} tickLine={false} dy={10} fontSize={10} />
                                    <YAxis stroke="#64748b" axisLine={false} tickLine={false} tickFormatter={(value) => `$${value}`} fontSize={10} />
                                    <RechartsTooltip 
                                        contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', color: '#fff' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Area type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Monthly Earnings (New) */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <Calendar size={20} className="text-blue-500"/> Monthly Earnings
                            </h3>
                            <span className="text-xs text-slate-500">2024</span>
                        </div>
                        <div className="h-48 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={monthlyRevenueData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.1} vertical={false} />
                                    <XAxis dataKey="name" stroke="#64748b" axisLine={false} tickLine={false} dy={10} fontSize={10} />
                                    <YAxis stroke="#64748b" axisLine={false} tickLine={false} tickFormatter={(value) => `$${value/1000}k`} fontSize={10} />
                                    <RechartsTooltip 
                                        cursor={{fill: 'rgba(255,255,255,0.05)'}}
                                        contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', color: '#fff' }}
                                    />
                                    <Bar dataKey="earnings" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Recent Transactions */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
                            <h3 className="font-bold text-sm text-slate-900 dark:text-white">Recent Transactions</h3>
                            <button className="text-xs text-emerald-600 font-medium hover:underline">View All</button>
                        </div>
                        <div className="divide-y divide-slate-100 dark:divide-slate-800">
                            {sessions.slice(0, 3).map((session, i) => (
                                <div key={i} className="p-4 flex justify-between items-center hover:bg-slate-50 dark:hover:bg-slate-800/50">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600">
                                            <DollarSign size={14} />
                                        </div>
                                        <div>
                                            <p className="text-sm font-semibold text-slate-900 dark:text-white">{(session.price * 0.15).toFixed(2)} Fee</p>
                                            <p className="text-[10px] text-slate-500">Session #{session.id.substring(0, 6)}</p>
                                        </div>
                                    </div>
                                    <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                                        {new Date(session.date).toLocaleDateString(undefined, {month:'short', day:'numeric'})}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Verification Detail Modal */}
            <Modal 
                isOpen={!!selectedRequest} 
                onClose={() => setSelectedRequest(null)} 
                title="Review Verification Request"
            >
                {selectedRequest && (
                    <div className="space-y-6">
                        <div className="flex items-start gap-4 p-4 bg-slate-50 dark:bg-slate-800 rounded-xl">
                            <div className="w-12 h-12 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-xl font-bold text-slate-600 dark:text-slate-300">
                                {selectedRequest.tutorName.charAt(0)}
                            </div>
                            <div>
                                <h3 className="font-bold text-lg text-slate-900 dark:text-white">{selectedRequest.tutorName}</h3>
                                <p className="text-sm text-slate-500">{selectedRequest.email}</p>
                                <div className="flex gap-2 mt-2">
                                    <span className="px-2 py-0.5 bg-slate-200 dark:bg-slate-700 rounded text-xs font-medium text-slate-700 dark:text-slate-300">
                                        {selectedRequest.subject}
                                    </span>
                                    <span className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/40 rounded text-xs font-medium text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
                                        Pending Review
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h4 className="font-semibold text-slate-900 dark:text-white mb-3">Submitted Documents</h4>
                            <div className="grid gap-3">
                                {selectedRequest.documents.map((doc, i) => (
                                    <div key={i} className="flex items-center justify-between p-3 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded text-slate-500">
                                                <FileText size={20} />
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium text-slate-900 dark:text-white">{doc.name}</p>
                                                <p className="text-xs text-slate-500 uppercase">{doc.type.split('/')[1]}</p>
                                            </div>
                                        </div>
                                        <button className="text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300 p-2">
                                            <Download size={18} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {reviewTutor && onViewProfile && (
                             <button 
                                onClick={() => {
                                    onViewProfile(reviewTutor);
                                    setSelectedRequest(null);
                                }}
                                className="w-full mb-2 px-4 py-3 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl font-semibold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center justify-center gap-2"
                            >
                                <Eye size={18} /> View Full Profile
                            </button>
                        )}

                        <div className="flex gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                            <button 
                                onClick={() => handleReject(selectedRequest.id)}
                                className="flex-1 px-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-xl font-semibold hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 hover:border-red-200 dark:hover:border-red-800 transition-colors flex items-center justify-center gap-2"
                            >
                                <XCircle size={18} /> Reject
                            </button>
                            <button 
                                onClick={() => handleApprove(selectedRequest.id)}
                                className="flex-1 px-4 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-semibold shadow-lg shadow-emerald-500/20 transition-colors flex items-center justify-center gap-2"
                            >
                                <CheckCircle size={18} /> Approve Application
                            </button>
                        </div>
                    </div>
                )}
            </Modal>

            {/* Manual Upload Simulation Modal */}
            <Modal
                isOpen={isUploadModalOpen}
                onClose={() => setIsUploadModalOpen(false)}
                title="Manual Verification Upload"
            >
                <div className="space-y-4">
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                        Upload documents on behalf of a tutor. This will create a pending verification request in the queue.
                    </p>
                    
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Tutor Email</label>
                        <input type="email" placeholder="tutor@example.com" className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm" />
                    </div>

                    <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-8 text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer">
                        <Upload size={24} className="mx-auto text-slate-400 mb-2"/>
                        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Click to upload files</p>
                        <p className="text-xs text-slate-500">PDF, JPG up to 10MB</p>
                    </div>

                    <div className="flex justify-end pt-2">
                         <button 
                            onClick={() => setIsUploadModalOpen(false)}
                            className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium"
                        >
                            Upload & Create Request
                        </button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};
