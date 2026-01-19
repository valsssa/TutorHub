
import React, { useMemo, useState } from 'react';
import { 
    Users, DollarSign, FileText, CheckCircle, XCircle, 
    TrendingUp, Activity, Shield, Download, Eye, Upload, Calendar, AlertTriangle, Key, UserPlus, PlayCircle, Trash2, ChevronRight, MessageSquare, Flag, Clock, FileClock, Server, MoreHorizontal, Filter, ExternalLink, Link as LinkIcon
} from 'lucide-react';
import { 
    AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer 
} from 'recharts';
import { VerificationRequest, Session, User, Tutor, UserRole, ViewState, AdminProfile } from '../domain/types';
import { Modal, Badge } from '../components/shared/UI';

interface AdminDashboardProps {
    currentUser: User;
    verificationRequests: VerificationRequest[];
    sessions: Session[];
    users: User[]; // implied total count based on mock logic
    tutors: Tutor[];
    admins: AdminProfile[];
    onAddAdmin: (admin: AdminProfile) => void;
    onRemoveAdmin: (id: string) => void;
    onApproveVerification: (id: string) => void;
    onRejectVerification: (id: string) => void;
    onForceCancelSession: (sessionId: string) => void;
    onViewProfile?: (tutor: Tutor) => void;
    onNavigate?: (view: ViewState) => void;
}

const YOUTRACK_BASE_URL = "https://valsa.youtrack.cloud";

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ 
    currentUser, verificationRequests, sessions, tutors, admins, onAddAdmin, onRemoveAdmin,
    onApproveVerification, onRejectVerification, onForceCancelSession, onViewProfile, onNavigate
}) => {
    const [selectedRequest, setSelectedRequest] = useState<VerificationRequest | null>(null);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [isAdminModalOpen, setIsAdminModalOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<'requests' | 'reports' | 'tutors' | 'admins' | 'logs'>('requests');
    const isOwner = currentUser.role === UserRole.OWNER;
    
    // Owner specific states
    const [withdrawalsPaused, setWithdrawalsPaused] = useState(false);
    const [isPauseModalOpen, setIsPauseModalOpen] = useState(false);
    const [isDeleteOrgModalOpen, setIsDeleteOrgModalOpen] = useState(false);
    const [deleteConfirmText, setDeleteConfirmText] = useState('');
    const [adminToDelete, setAdminToDelete] = useState<string | null>(null);
    
    // Admin Creation State
    const [newAdminName, setNewAdminName] = useState('');
    const [newAdminEmail, setNewAdminEmail] = useState('');

    // --- Mock Support Data with YouTrack Integration ---
    const mockReports = [
        { id: 'r1', youtrackId: 'SUP-2401', type: 'Harassment', user: 'Alex Johnson', target: 'Dr. Elena Vance', date: '2023-10-26T10:30:00', status: 'Open', priority: 'High', message: 'Tutor was rude during the session.' },
        { id: 'r2', youtrackId: 'SUP-2402', type: 'Refund Request', user: 'Sarah Miller', target: 'Session #4421', date: '2023-10-25T14:15:00', status: 'Pending', priority: 'Medium', message: 'Technical issues prevented connection.' },
        { id: 'r3', youtrackId: 'SUP-2399', type: 'Technical Issue', user: 'James Chen', target: 'Classroom', date: '2023-10-25T09:00:00', status: 'Resolved', priority: 'Low', message: 'Whiteboard lag.' },
        { id: 'r4', youtrackId: 'SUP-2398', type: 'Account Access', user: 'Mike T.', target: 'Login', date: '2023-10-24T16:20:00', status: 'Open', priority: 'Medium', message: 'Cannot reset password.' },
    ];

    // --- Mock System Logs ---
    const mockLogs = [
        { id: 'l1', action: 'Admin Created', actor: 'Platform Owner', target: 'Sarah Moderator', date: '2023-10-27T14:30:00', type: 'success' },
        { id: 'l2', action: 'Withdrawals Paused', actor: 'System Admin', target: 'Global Settings', date: '2023-10-27T11:15:00', type: 'warning' },
        { id: 'l3', action: 'Verification Rejected', actor: 'Sarah Moderator', target: 'John Doe (Tutor)', date: '2023-10-26T09:45:00', type: 'info' },
        { id: 'l4', action: 'System Backup', actor: 'System', target: 'Database', date: '2023-10-26T00:00:00', type: 'system' },
    ];

    const openTickets = mockReports.filter(r => r.status !== 'Resolved').length;

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

    const scrollToSection = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    const stats = [
        // Card 1: Revenue (Owner) OR Open Tickets (Admin)
        isOwner ? { 
            label: 'Platform Revenue', 
            value: `$${platformRevenue.toLocaleString(undefined, {minimumFractionDigits: 2})}`, 
            icon: DollarSign, 
            color: 'text-emerald-600', 
            bg: 'bg-emerald-100 dark:bg-emerald-900/30',
            trend: '+12.5%',
            onClick: () => onNavigate && onNavigate('admin-revenue'),
            hoverBorder: 'hover:border-emerald-500',
            hoverShadow: 'hover:shadow-emerald-500/10',
            hoverText: 'group-hover:text-emerald-600 dark:group-hover:text-emerald-400',
            chevronColor: 'text-emerald-500'
        } : {
            label: 'Open Support Tickets', 
            value: openTickets, 
            icon: MessageSquare, 
            color: 'text-red-600', 
            bg: 'bg-red-100 dark:bg-red-900/30',
            trend: 'Needs Attention',
            onClick: () => { setActiveTab('reports'); scrollToSection('users-support-view'); },
            hoverBorder: 'hover:border-red-500',
            hoverShadow: 'hover:shadow-red-500/10',
            hoverText: 'group-hover:text-red-600 dark:group-hover:text-red-400',
            chevronColor: 'text-red-500'
        },
        // Card 2
        { 
            label: 'Pending Verifications', 
            value: pendingRequests.length, 
            icon: Shield, 
            color: 'text-amber-600', 
            bg: 'bg-amber-100 dark:bg-amber-900/30',
            trend: 'Action Required',
            onClick: () => { setActiveTab('requests'); scrollToSection('users-support-view'); },
            hoverBorder: 'hover:border-amber-500',
            hoverShadow: 'hover:shadow-amber-500/10',
            hoverText: 'group-hover:text-amber-600 dark:group-hover:text-amber-400',
            chevronColor: 'text-amber-500'
        },
        // Card 3
        { 
            label: 'Total Sessions', 
            value: sessions.length, 
            icon: Activity, 
            color: 'text-blue-600', 
            bg: 'bg-blue-100 dark:bg-blue-900/30',
            trend: '+8.2%',
            onClick: () => onNavigate && onNavigate('admin-sessions'),
            hoverBorder: 'hover:border-blue-500',
            hoverShadow: 'hover:shadow-blue-500/10',
            hoverText: 'group-hover:text-blue-600 dark:group-hover:text-blue-400',
            chevronColor: 'text-blue-500'
        },
        // Card 4
        { 
            label: 'Active Tutors', 
            value: tutors.length, 
            icon: Users, 
            color: 'text-purple-600', 
            bg: 'bg-purple-100 dark:bg-purple-900/30',
            trend: '+4 this week',
            onClick: () => onNavigate && onNavigate('admin-tutors'),
            hoverBorder: 'hover:border-purple-500',
            hoverShadow: 'hover:shadow-purple-500/10',
            hoverText: 'group-hover:text-purple-600 dark:group-hover:text-purple-400',
            chevronColor: 'text-purple-500'
        },
    ];

    // Mock Data for Charts
    const dailyRevenueData = [
        { name: 'Mon', revenue: 120 }, { name: 'Tue', revenue: 180 }, { name: 'Wed', revenue: 150 },
        { name: 'Thu', revenue: 240 }, { name: 'Fri', revenue: 300 }, { name: 'Sat', revenue: 380 }, { name: 'Sun', revenue: 210 },
    ];

    const handleApprove = (id: string) => {
        onApproveVerification(id);
        setSelectedRequest(null);
    };

    const handleReject = (id: string) => {
        onRejectVerification(id);
        setSelectedRequest(null);
    };

    const handleCreateAdmin = (e: React.FormEvent) => {
        e.preventDefault();
        const newAdmin = {
            id: `a${Date.now()}`,
            name: newAdminName,
            email: newAdminEmail,
            role: 'ADMIN',
            status: 'Active',
            joinedDate: new Date().toISOString().split('T')[0]
        };
        onAddAdmin(newAdmin);
        setIsAdminModalOpen(false);
        setNewAdminName('');
        setNewAdminEmail('');
    };

    const handleConfirmDeleteAdmin = () => {
        if (adminToDelete) {
            onRemoveAdmin(adminToDelete);
            setAdminToDelete(null);
        }
    };

    const handlePauseWithdrawals = () => {
        setWithdrawalsPaused(!withdrawalsPaused);
        setIsPauseModalOpen(false);
    };

    const handleDeleteOrganization = () => {
        if (deleteConfirmText === 'DELETE') {
            alert("Organization deletion initiated. (Mock Action)");
            setIsDeleteOrgModalOpen(false);
            setDeleteConfirmText('');
        }
    };

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            <div className="mb-8 flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        {isOwner ? 'Owner Dashboard' : 'Admin & Support'}
                        {isOwner && (
                            <span className="text-xs bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-2 py-1 rounded uppercase tracking-wider font-bold">Owner Access</span>
                        )}
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400">
                        {isOwner ? 'Platform performance and financial overview.' : 'Manage users, verifications, and support tickets.'}
                    </p>
                </div>
                {/* Global YouTrack Status Indicator */}
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full text-xs font-bold border border-blue-100 dark:border-blue-800">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    YouTrack Connected
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {stats.map((stat, idx) => (
                    <div 
                        key={idx} 
                        onClick={stat.onClick}
                        className={`bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group cursor-pointer transition-all transform active:scale-[0.98] hover:shadow-lg ${stat.hoverBorder} ${stat.hoverShadow}`}
                    >
                        <div className="flex justify-between items-start mb-4">
                            <div className={`p-3 rounded-xl ${stat.bg} ${stat.color} group-hover:scale-110 transition-transform`}>
                                <stat.icon size={24} />
                            </div>
                            <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                                stat.label.includes('Pending') ? 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400' : 
                                stat.label.includes('Tickets') ? 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400' :
                                'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-400'
                            }`}>
                                {stat.trend}
                            </span>
                        </div>
                        <h3 className="text-slate-500 dark:text-slate-400 text-sm font-medium">{stat.label}</h3>
                        <p className={`text-2xl font-bold text-slate-900 dark:text-white mt-1 transition-colors ${stat.hoverText}`}>
                            {stat.value}
                        </p>
                        <div className="absolute right-4 bottom-4 opacity-0 group-hover:opacity-100 transition-opacity">
                            <ChevronRight size={16} className={stat.chevronColor} />
                        </div>
                    </div>
                ))}
            </div>

            {/* OWNER ONLY SECTION */}
            {isOwner && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8 animate-in slide-in-from-top-4 duration-500">
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
                                    {withdrawalsPaused ? <span className="text-red-400">Paused</span> : 'Operational'}
                                </div>
                                <p className="text-xs text-slate-400 mt-1">v2023-10-16</p>
                            </div>
                        </div>
                        <div className="mt-4 flex gap-3">
                            <button 
                                onClick={() => { setActiveTab('admins'); scrollToSection('users-support-view'); }}
                                className="flex-1 py-2 bg-white text-slate-900 rounded-lg text-sm font-bold hover:bg-slate-200 transition-colors"
                            >
                                Manage Admins
                            </button>
                            <button 
                                onClick={() => onNavigate && onNavigate('legal-compliance')}
                                className="flex-1 py-2 border border-white/20 text-white rounded-lg text-sm font-bold hover:bg-white/10 transition-colors"
                            >
                                Legal & Compliance
                            </button>
                        </div>
                    </div>

                    <div className="bg-red-50 dark:bg-red-900/10 rounded-2xl p-6 border border-red-100 dark:border-red-900/30">
                        <h3 className="font-bold text-lg mb-4 flex items-center gap-2 text-red-700 dark:text-red-400">
                            <AlertTriangle size={20} /> Danger Zone
                        </h3>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-900 rounded-lg border border-red-100 dark:border-red-900/30">
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{withdrawalsPaused ? 'Resume All Withdrawals' : 'Pause All Withdrawals'}</span>
                                <button onClick={() => setIsPauseModalOpen(true)} className={`px-3 py-1 rounded text-xs font-bold transition-colors ${withdrawalsPaused ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200' : 'bg-red-100 text-red-700 hover:bg-red-200'}`}>
                                    {withdrawalsPaused ? 'Resume' : 'Pause'}
                                </button>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-900 rounded-lg border border-red-100 dark:border-red-900/30">
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Delete Organization</span>
                                <button onClick={() => setIsDeleteOrgModalOpen(true)} className="px-3 py-1 bg-red-600 text-white rounded text-xs font-bold hover:bg-red-700 transition-colors">
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                
                {/* --- Main Column: Users & Support View --- */}
                <div className="xl:col-span-2 space-y-8">
                    <div id="users-support-view" className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden min-h-[600px] flex flex-col">
                        
                        {/* Improved Header & Tab Navigation */}
                        <div className="p-4 border-b border-slate-200 dark:border-slate-800">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                                <div className="flex items-center gap-2">
                                    <Users size={20} className="text-emerald-500"/> 
                                    <h2 className="text-lg font-bold text-slate-900 dark:text-white">Users & Support</h2>
                                </div>
                                <div className="flex gap-2">
                                    {activeTab === 'requests' && (
                                        <button 
                                            onClick={() => setIsUploadModalOpen(true)}
                                            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-xs font-bold text-slate-600 dark:text-slate-300 transition-colors"
                                        >
                                            <Upload size={14} /> Upload Doc
                                        </button>
                                    )}
                                    {activeTab === 'admins' && isOwner && (
                                        <button 
                                            onClick={() => setIsAdminModalOpen(true)}
                                            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg text-xs font-bold hover:opacity-90 transition-colors"
                                        >
                                            <UserPlus size={14} /> Add Admin
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Scrollable Tabs */}
                            <div className="flex gap-1 overflow-x-auto pb-2 md:pb-0 scrollbar-hide -mx-4 px-4 md:mx-0 md:px-0">
                                <button 
                                    onClick={() => setActiveTab('requests')}
                                    className={`px-4 py-2 rounded-lg text-sm font-bold whitespace-nowrap transition-all ${activeTab === 'requests' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                                >
                                    Verifications {pendingRequests.length > 0 && <span className="ml-1 px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded-full text-[10px]">{pendingRequests.length}</span>}
                                </button>
                                <button 
                                    onClick={() => setActiveTab('reports')}
                                    className={`px-4 py-2 rounded-lg text-sm font-bold whitespace-nowrap transition-all ${activeTab === 'reports' ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                                >
                                    Support Tickets {openTickets > 0 && <span className="ml-1 px-1.5 py-0.5 bg-red-100 text-red-700 rounded-full text-[10px]">{openTickets}</span>}
                                </button>
                                <button 
                                    onClick={() => setActiveTab('tutors')}
                                    className={`px-4 py-2 rounded-lg text-sm font-bold whitespace-nowrap transition-all ${activeTab === 'tutors' ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                                >
                                    Profiles
                                </button>
                                {isOwner && (
                                    <>
                                        <button 
                                            onClick={() => setActiveTab('admins')}
                                            className={`px-4 py-2 rounded-lg text-sm font-bold whitespace-nowrap transition-all ${activeTab === 'admins' ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                                        >
                                            Admins
                                        </button>
                                        <button 
                                            onClick={() => setActiveTab('logs')}
                                            className={`px-4 py-2 rounded-lg text-sm font-bold whitespace-nowrap transition-all ${activeTab === 'logs' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400' : 'text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                                        >
                                            Logs
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                        
                        {/* Tab Content Areas */}
                        <div className="flex-1 bg-slate-50/50 dark:bg-slate-950/20">
                            
                            {/* --- VERIFICATIONS --- */}
                            {activeTab === 'requests' && (
                                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {pendingRequests.length === 0 ? (
                                        <div className="flex flex-col items-center justify-center h-64 text-slate-500">
                                            <CheckCircle size={48} className="text-emerald-200 dark:text-emerald-900/50 mb-4"/>
                                            <p className="font-medium">All caught up!</p>
                                            <p className="text-sm">No pending verification requests.</p>
                                        </div>
                                    ) : (
                                        pendingRequests.map(request => (
                                            <div key={request.id} className="p-4 sm:p-6 hover:bg-white dark:hover:bg-slate-900 transition-colors bg-white dark:bg-slate-900 sm:bg-transparent">
                                                <div className="flex flex-col sm:flex-row justify-between gap-4">
                                                    <div className="flex gap-4">
                                                        <div className="w-12 h-12 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center font-bold text-lg text-slate-600 dark:text-slate-400 shrink-0">
                                                            {request.tutorName.charAt(0)}
                                                        </div>
                                                        <div>
                                                            <div className="flex items-center gap-2">
                                                                <h3 className="font-bold text-slate-900 dark:text-white">{request.tutorName}</h3>
                                                                <span className="px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 text-[10px] font-bold uppercase tracking-wider">Review Needed</span>
                                                            </div>
                                                            <p className="text-sm text-slate-500">{request.email}</p>
                                                            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-2 text-xs text-slate-500 dark:text-slate-400">
                                                                <span className="flex items-center gap-1"><FileText size={12}/> {request.subject}</span>
                                                                <span className="flex items-center gap-1"><Calendar size={12}/> {new Date(request.submittedDate).toLocaleDateString()}</span>
                                                                <a 
                                                                    href={`${YOUTRACK_BASE_URL}/issue/VER-${request.id}`}
                                                                    target="_blank"
                                                                    rel="noreferrer"
                                                                    className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline bg-blue-50 dark:bg-blue-900/20 px-1.5 py-0.5 rounded border border-blue-100 dark:border-blue-900/50"
                                                                >
                                                                    YouTrack: VER-{request.id} <ExternalLink size={10} />
                                                                </a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2 self-start sm:self-center w-full sm:w-auto mt-2 sm:mt-0">
                                                        <button 
                                                            onClick={() => setSelectedRequest(request)}
                                                            className="flex-1 sm:flex-initial px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg text-sm font-bold hover:opacity-90 transition-opacity"
                                                        >
                                                            Review
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            )}

                            {/* --- REPORTS / TICKETS --- */}
                            {activeTab === 'reports' && (
                                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {mockReports.length === 0 ? (
                                        <div className="p-12 text-center text-slate-500">
                                            <CheckCircle size={48} className="mx-auto text-emerald-200 mb-4"/>
                                            <p>No open support reports.</p>
                                        </div>
                                    ) : (
                                        mockReports.map(report => (
                                            <div key={report.id} className="p-4 sm:p-6 hover:bg-white dark:hover:bg-slate-900 transition-colors bg-white dark:bg-slate-900 sm:bg-transparent">
                                                <div className="flex flex-col sm:flex-row justify-between gap-4">
                                                    <div className="flex gap-4">
                                                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                                                            report.priority === 'High' ? 'bg-red-100 text-red-600 dark:bg-red-900/30' :
                                                            report.priority === 'Medium' ? 'bg-amber-100 text-amber-600 dark:bg-amber-900/30' :
                                                            'bg-blue-100 text-blue-600 dark:bg-blue-900/30'
                                                        }`}>
                                                            <Flag size={20} />
                                                        </div>
                                                        <div className="flex-1">
                                                            <div className="flex flex-wrap items-center gap-2 mb-1">
                                                                <h4 className="font-bold text-slate-900 dark:text-white text-sm">{report.type}</h4>
                                                                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                                                                    report.priority === 'High' ? 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400' :
                                                                    report.priority === 'Medium' ? 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400' :
                                                                    'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                                                                }`}>
                                                                    {report.priority}
                                                                </span>
                                                                {report.status === 'Resolved' && <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold uppercase">Resolved</span>}
                                                                
                                                                <a 
                                                                    href={`${YOUTRACK_BASE_URL}/issue/${report.youtrackId}`}
                                                                    target="_blank"
                                                                    rel="noreferrer"
                                                                    className="text-[10px] font-mono text-blue-600 dark:text-blue-400 flex items-center gap-1 hover:underline border border-blue-100 dark:border-blue-900/50 bg-blue-50 dark:bg-blue-900/20 px-1.5 py-0.5 rounded ml-auto sm:ml-0"
                                                                >
                                                                    {report.youtrackId} <ExternalLink size={8} />
                                                                </a>
                                                            </div>
                                                            <p className="text-sm text-slate-700 dark:text-slate-300 font-medium mb-1 line-clamp-1">{report.message}</p>
                                                            <div className="text-xs text-slate-500 flex items-center gap-3">
                                                                <span>From: {report.user}</span>
                                                                <span>•</span>
                                                                <span>Target: {report.target}</span>
                                                                <span>•</span>
                                                                <span>{new Date(report.date).toLocaleDateString()}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2 self-start sm:self-center w-full sm:w-auto pl-14 sm:pl-0">
                                                        <button className="px-3 py-1.5 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 rounded-lg text-xs font-bold hover:bg-slate-50 dark:hover:bg-slate-800">
                                                            Details
                                                        </button>
                                                        <button className="px-3 py-1.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg text-xs font-bold hover:opacity-90">
                                                            Resolve
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            )}

                            {/* --- SYSTEM LOGS --- */}
                            {activeTab === 'logs' && (
                                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {mockLogs.map(log => (
                                        <div key={log.id} className="p-4 flex items-start gap-4 hover:bg-white dark:hover:bg-slate-900 transition-colors group">
                                            <div className={`w-8 h-8 rounded flex items-center justify-center shrink-0 mt-0.5 ${
                                                log.type === 'error' ? 'bg-red-100 text-red-600' :
                                                log.type === 'warning' ? 'bg-amber-100 text-amber-600' :
                                                'bg-slate-100 text-slate-600'
                                            }`}>
                                                {log.type === 'error' ? <AlertTriangle size={16}/> : <FileClock size={16}/>}
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex justify-between">
                                                    <span className="font-mono text-xs font-bold text-slate-900 dark:text-white">{log.action}</span>
                                                    <span className="text-[10px] text-slate-400">{new Date(log.date).toLocaleString()}</span>
                                                </div>
                                                <div className="text-xs text-slate-500 mt-1 mb-1">
                                                    <span className="font-medium text-slate-700 dark:text-slate-300">{log.actor}</span> acted on <span className="font-medium text-slate-700 dark:text-slate-300">{log.target}</span>
                                                </div>
                                                
                                                {/* Log-Specific YouTrack Create Action */}
                                                {(log.type === 'warning' || log.type === 'error') && (
                                                    <a 
                                                        href={`${YOUTRACK_BASE_URL}/newIssue?summary=${encodeURIComponent(`Log: ${log.action}`)}&description=${encodeURIComponent(`Actor: ${log.actor}\nTarget: ${log.target}`)}`}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className="text-[10px] font-bold text-blue-600 hover:underline flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                                                    >
                                                        <ExternalLink size={8} /> Report Bug in YouTrack
                                                    </a>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* --- ADMINS LIST --- */}
                            {activeTab === 'admins' && (
                                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {admins.map(admin => (
                                        <div key={admin.id} className="p-4 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 sm:bg-transparent">
                                            <div className="flex items-center gap-4">
                                                <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-700 dark:text-purple-300 font-bold">
                                                    {admin.name.charAt(0)}
                                                </div>
                                                <div>
                                                    <h3 className="font-bold text-slate-900 dark:text-white text-sm">{admin.name}</h3>
                                                    <div className="flex items-center gap-2">
                                                        <p className="text-xs text-slate-500">{admin.email}</p>
                                                        <a 
                                                            href={`${YOUTRACK_BASE_URL}/users?q=${encodeURIComponent(admin.email)}`}
                                                            target="_blank" 
                                                            rel="noreferrer"
                                                            className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-0.5"
                                                            title="Find User in YouTrack"
                                                        >
                                                            <ExternalLink size={8} />
                                                        </a>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4 justify-between sm:justify-end w-full sm:w-auto pl-14 sm:pl-0">
                                                <span className="text-xs font-medium px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-slate-600 dark:text-slate-300">
                                                    Joined: {new Date(admin.joinedDate).toLocaleDateString()}
                                                </span>
                                                <button 
                                                    onClick={() => setAdminToDelete(admin.id)}
                                                    className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* --- TUTORS LIST --- */}
                            {activeTab === 'tutors' && (
                                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {tutors.slice(0, 5).map(tutor => (
                                        <div key={tutor.id} className="p-4 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 sm:bg-transparent">
                                            <div className="flex items-center gap-4">
                                                <img src={tutor.imageUrl} className="w-10 h-10 rounded-full object-cover" alt={tutor.name} />
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <h3 className="font-bold text-slate-900 dark:text-white text-sm">{tutor.name}</h3>
                                                        {tutor.isVerified && <CheckCircle size={12} className="text-emerald-500" />}
                                                    </div>
                                                    <p className="text-xs text-slate-500">{tutor.subject}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2 justify-end w-full sm:w-auto">
                                                <a 
                                                    href={`${YOUTRACK_BASE_URL}/issues?q=${encodeURIComponent(tutor.name)}`}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="px-3 py-1.5 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-1"
                                                >
                                                    YouTrack <LinkIcon size={10} />
                                                </a>
                                                <button 
                                                    onClick={() => onViewProfile && onViewProfile(tutor)}
                                                    className="px-3 py-1.5 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                                                >
                                                    Profile
                                                </button>
                                                <button className="p-2 text-slate-400 hover:text-slate-600 rounded">
                                                    <MoreHorizontal size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                    <div className="p-4 text-center border-t border-slate-200 dark:border-slate-800">
                                        <button 
                                            onClick={() => onNavigate && onNavigate('admin-tutors')}
                                            className="text-sm font-bold text-emerald-600 hover:underline"
                                        >
                                            View all {tutors.length} tutors
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* --- Right Column: Financials OR Activity --- */}
                <div className="space-y-8">
                    {/* Activity / Quick Feed */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
                                <Activity size={20} className="text-blue-500"/> Live Activity
                            </h3>
                        </div>
                        <div className="space-y-6 relative">
                            <div className="absolute left-2 top-2 bottom-2 w-0.5 bg-slate-100 dark:bg-slate-800"></div>
                            
                            <div className="relative pl-8">
                                <div className="absolute left-0 top-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-900"></div>
                                <p className="text-sm font-medium text-slate-900 dark:text-white">New Tutor Signup</p>
                                <p className="text-xs text-slate-500">Alex M. joined 5m ago</p>
                            </div>
                            
                            <div className="relative pl-8">
                                <div className="absolute left-0 top-1 w-4 h-4 rounded-full bg-blue-500 border-2 border-white dark:border-slate-900"></div>
                                <p className="text-sm font-medium text-slate-900 dark:text-white">Session Completed</p>
                                <p className="text-xs text-slate-500">Physics 101 • 15m ago</p>
                            </div>
                            
                            <div className="relative pl-8">
                                <div className="absolute left-0 top-1 w-4 h-4 rounded-full bg-amber-500 border-2 border-white dark:border-slate-900"></div>
                                <p className="text-sm font-medium text-slate-900 dark:text-white">Verification Pending</p>
                                <p className="text-xs text-slate-500">Sarah J. uploaded docs • 1h ago</p>
                            </div>
                        </div>
                    </div>

                    {isOwner && (
                        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                            <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                                <TrendingUp size={20} className="text-emerald-500"/> Revenue Trend
                            </h3>
                            <div className="h-40 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={dailyRevenueData}>
                                        <defs>
                                            <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                            </linearGradient>
                                        </defs>
                                        <Area type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorRevenue)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                            <button 
                                onClick={() => onNavigate && onNavigate('admin-revenue')}
                                className="w-full mt-4 py-2 text-sm font-bold text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                            >
                                View Detailed Report
                            </button>
                        </div>
                    )}
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

            {/* Create Admin Modal */}
            <Modal
                isOpen={isAdminModalOpen}
                onClose={() => setIsAdminModalOpen(false)}
                title="Create New Admin"
            >
                <form onSubmit={handleCreateAdmin} className="space-y-4">
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                        Add a new administrator to the platform. They will have full access to user management and moderation tools.
                    </p>
                    
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Full Name</label>
                        <input 
                            type="text" 
                            required
                            value={newAdminName}
                            onChange={(e) => setNewAdminName(e.target.value)}
                            placeholder="e.g. Alex Smith" 
                            className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white" 
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Email Address</label>
                        <input 
                            type="email" 
                            required
                            value={newAdminEmail}
                            onChange={(e) => setNewAdminEmail(e.target.value)}
                            placeholder="admin@edu.com" 
                            className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white" 
                        />
                    </div>

                    <div className="flex justify-end pt-2">
                         <button 
                            type="submit"
                            className="px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg text-sm font-bold"
                        >
                            Create Admin User
                        </button>
                    </div>
                </form>
            </Modal>

            {/* Delete Admin Modal */}
            <Modal
                isOpen={!!adminToDelete}
                onClose={() => setAdminToDelete(null)}
                title="Remove Administrator"
            >
                <div className="space-y-6">
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-xl">
                        <div className="flex gap-3">
                            <AlertTriangle size={24} className="text-red-600 dark:text-red-400 shrink-0" />
                            <div>
                                <h4 className="font-bold text-red-800 dark:text-red-200 mb-1">Are you sure?</h4>
                                <p className="text-sm text-red-700 dark:text-red-300">
                                    This action will immediately remove the administrator from the platform. They will lose all access to the admin dashboard.
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end gap-3">
                        <button 
                            onClick={() => setAdminToDelete(null)}
                            className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
                        >
                            Cancel
                        </button>
                        <button 
                            onClick={handleConfirmDeleteAdmin}
                            className="px-4 py-2 text-sm font-bold text-white bg-red-600 rounded-lg hover:bg-red-700 shadow-lg shadow-red-500/20 transition-all"
                        >
                            Remove Admin
                        </button>
                    </div>
                </div>
            </Modal>

            {/* Pause Withdrawals Confirmation Modal */}
            <Modal
                isOpen={isPauseModalOpen}
                onClose={() => setIsPauseModalOpen(false)}
                title={withdrawalsPaused ? "Resume Withdrawals" : "Pause All Withdrawals"}
            >
                <div className="space-y-4">
                    <div className={`p-4 rounded-xl border ${withdrawalsPaused ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                        <div className="flex gap-3">
                            {withdrawalsPaused ? <PlayCircle size={24} /> : <AlertTriangle size={24} />}
                            <div>
                                <h4 className="font-bold text-sm mb-1">Are you sure?</h4>
                                <p className="text-xs opacity-90">
                                    {withdrawalsPaused 
                                        ? "This will re-enable payout processing for all tutors immediately." 
                                        : "This will stop all payouts to tutors. Use this only in emergencies."}
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div className="flex justify-end gap-3 pt-2">
                        <button 
                            onClick={() => setIsPauseModalOpen(false)}
                            className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
                        >
                            Cancel
                        </button>
                        <button 
                            onClick={handlePauseWithdrawals}
                            className={`px-4 py-2 text-sm font-bold text-white rounded-lg shadow-lg transition-colors ${withdrawalsPaused ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-red-600 hover:bg-red-500'}`}
                        >
                            {withdrawalsPaused ? "Resume Operations" : "Pause Operations"}
                        </button>
                    </div>
                </div>
            </Modal>

            {/* Delete Organization Modal */}
            <Modal
                isOpen={isDeleteOrgModalOpen}
                onClose={() => setIsDeleteOrgModalOpen(false)}
                title="Delete Organization"
            >
                <div className="space-y-6">
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-xl">
                        <h4 className="font-bold text-red-800 dark:text-red-200 flex items-center gap-2 mb-2">
                            <AlertTriangle size={20} /> Critical Warning
                        </h4>
                        <p className="text-sm text-red-700 dark:text-red-300">
                            This action is <strong>irreversible</strong>. This will permanently delete the organization "EduConnect", remove all users, wipe all database records, and cancel all active subscriptions.
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">
                            Type <span className="font-mono text-red-600 dark:text-red-400">DELETE</span> to confirm
                        </label>
                        <input 
                            type="text" 
                            value={deleteConfirmText}
                            onChange={(e) => setDeleteConfirmText(e.target.value)}
                            placeholder="DELETE"
                            className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
                        />
                    </div>

                    <div className="flex justify-end gap-3">
                        <button 
                            onClick={() => setIsDeleteOrgModalOpen(false)}
                            className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
                        >
                            Cancel
                        </button>
                        <button 
                            onClick={handleDeleteOrganization}
                            disabled={deleteConfirmText !== 'DELETE'}
                            className="px-4 py-2 text-sm font-bold text-white bg-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-500/20 transition-all"
                        >
                            Permanently Delete
                        </button>
                    </div>
                </div>
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
