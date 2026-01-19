
import React, { useState } from 'react';
import { ChevronLeft, Activity, Search, Filter, Calendar, Clock, DollarSign, ArrowDown, ArrowUp } from 'lucide-react';
import { Session } from '../domain/types';

interface AdminSessionsPageProps {
    sessions: Session[];
    onBack: () => void;
}

export const AdminSessionsPage: React.FC<AdminSessionsPageProps> = ({ sessions, onBack }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('All');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

    const filteredSessions = sessions.filter(session => {
        const matchesSearch = 
            session.tutorName.toLowerCase().includes(searchQuery.toLowerCase()) || 
            session.subject.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = statusFilter === 'All' || session.status === statusFilter.toLowerCase();
        return matchesSearch && matchesStatus;
    }).sort((a, b) => {
        const dateA = new Date(a.date).getTime();
        const dateB = new Date(b.date).getTime();
        return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
    });

    const getStatusColor = (status: string) => {
        switch(status) {
            case 'upcoming': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300';
            case 'completed': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300';
            case 'cancelled': return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400';
            default: return 'bg-slate-100 text-slate-700';
        }
    };

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            <button 
                onClick={onBack}
                className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-6 group"
            >
                <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                Back to Dashboard
            </button>

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                        <Activity size={32} className="text-blue-500" /> Total Sessions
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Full history of all lessons conducted on the platform.</p>
                </div>
                
                <div className="flex gap-3">
                    <div className="relative">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input 
                            type="text" 
                            placeholder="Search by tutor or subject..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 w-64"
                        />
                    </div>
                    <div className="relative">
                        <select 
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="pl-9 pr-8 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
                        >
                            <option>All</option>
                            <option>Upcoming</option>
                            <option>Completed</option>
                            <option>Cancelled</option>
                        </select>
                        <Filter size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                    </div>
                </div>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">ID</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide cursor-pointer flex items-center gap-1" onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}>
                                    Date {sortOrder === 'asc' ? <ArrowUp size={12}/> : <ArrowDown size={12}/>}
                                </th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Tutor</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Student</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Subject</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Price</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {filteredSessions.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                                        No sessions found.
                                    </td>
                                </tr>
                            ) : (
                                filteredSessions.map((session) => (
                                    <tr key={session.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4 text-sm font-mono text-slate-500">{session.id.substring(0, 8)}...</td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm text-slate-900 dark:text-white font-medium">{new Date(session.date).toLocaleDateString()}</div>
                                            <div className="text-xs text-slate-500">{new Date(session.date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300 font-medium">{session.tutorName}</td>
                                        <td className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">{session.studentId === 's1' ? 'Luis P.' : session.studentId}</td>
                                        <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{session.subject}</td>
                                        <td className="px-6 py-4 text-sm font-bold text-slate-900 dark:text-white">${session.price}</td>
                                        <td className="px-6 py-4 text-right">
                                            <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold capitalize ${getStatusColor(session.status)}`}>
                                                {session.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
