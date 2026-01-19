
import React, { useState } from 'react';
import { ChevronLeft, Shield, CheckCircle, XCircle, Clock, FileText, Download, Eye, Search, Filter } from 'lucide-react';
import { VerificationRequest, Tutor } from '../domain/types';
import { Modal } from '../components/shared/UI';

interface AdminVerificationsPageProps {
    requests: VerificationRequest[];
    tutors: Tutor[];
    onApprove: (id: string) => void;
    onReject: (id: string) => void;
    onBack: () => void;
    onViewProfile: (tutor: Tutor) => void;
}

export const AdminVerificationsPage: React.FC<AdminVerificationsPageProps> = ({ 
    requests, tutors, onApprove, onReject, onBack, onViewProfile 
}) => {
    const [selectedRequest, setSelectedRequest] = useState<VerificationRequest | null>(null);
    const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
    const [searchQuery, setSearchQuery] = useState('');

    const filteredRequests = requests.filter(req => {
        const matchesStatus = filterStatus === 'all' || req.status === filterStatus;
        const matchesSearch = req.tutorName.toLowerCase().includes(searchQuery.toLowerCase()) || req.email.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesStatus && matchesSearch;
    });

    const getReviewTutor = (req: VerificationRequest) => tutors.find(t => t.id === req.tutorId);

    const handleApprove = (id: string) => {
        onApprove(id);
        setSelectedRequest(null);
    };

    const handleReject = (id: string) => {
        onReject(id);
        setSelectedRequest(null);
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
                        <Shield size={32} className="text-amber-500" /> Verification Queue
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Review and approve tutor credentials to maintain platform quality.</p>
                </div>
                <div className="flex gap-3">
                    <div className="relative">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input 
                            type="text" 
                            placeholder="Search tutors..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        />
                    </div>
                    <div className="relative">
                        <select 
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value as any)}
                            className="pl-9 pr-8 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
                        >
                            <option value="all">All Status</option>
                            <option value="pending">Pending</option>
                            <option value="approved">Approved</option>
                            <option value="rejected">Rejected</option>
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
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Tutor</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Subject</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Submitted</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Documents</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Status</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {filteredRequests.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                                        No verification requests found matching your criteria.
                                    </td>
                                </tr>
                            ) : (
                                filteredRequests.map((req) => (
                                    <tr key={req.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-bold text-slate-600 dark:text-slate-300">
                                                    {req.tutorName.charAt(0)}
                                                </div>
                                                <div>
                                                    <div className="font-bold text-slate-900 dark:text-white text-sm">{req.tutorName}</div>
                                                    <div className="text-xs text-slate-500">{req.email}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                                            {req.subject}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                                            {new Date(req.submittedDate).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                                            {req.documents.length} files
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                                                req.status === 'pending' 
                                                    ? 'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800' 
                                                    : req.status === 'approved'
                                                    ? 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800'
                                                    : 'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800'
                                            }`}>
                                                {req.status === 'pending' && <Clock size={12} className="mr-1 mt-0.5" />}
                                                {req.status.charAt(0).toUpperCase() + req.status.slice(1)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button 
                                                onClick={() => setSelectedRequest(req)}
                                                className="bg-slate-100 dark:bg-slate-800 hover:bg-emerald-600 hover:text-white text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-lg font-medium text-xs transition-all inline-flex items-center gap-1"
                                            >
                                                <Eye size={14} /> Review
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Detail Modal */}
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
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${
                                        selectedRequest.status === 'pending' ? 'bg-amber-100 text-amber-700 border-amber-200' : 'bg-slate-100 text-slate-700 border-slate-200'
                                    }`}>
                                        {selectedRequest.status.toUpperCase()}
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

                        {getReviewTutor(selectedRequest) && (
                             <button 
                                onClick={() => {
                                    onViewProfile(getReviewTutor(selectedRequest)!);
                                    setSelectedRequest(null);
                                }}
                                className="w-full mb-2 px-4 py-3 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl font-semibold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center justify-center gap-2"
                            >
                                <Eye size={18} /> View Full Profile
                            </button>
                        )}

                        {selectedRequest.status === 'pending' && (
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
                        )}
                    </div>
                )}
            </Modal>
        </div>
    );
};
