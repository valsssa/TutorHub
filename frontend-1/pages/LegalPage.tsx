
import React, { useState } from 'react';
import { ChevronLeft, FileText, Shield, Lock, Download, CheckCircle, AlertTriangle } from 'lucide-react';

interface LegalPageProps {
    onBack: () => void;
}

export const LegalPage: React.FC<LegalPageProps> = ({ onBack }) => {
    const [activeTab, setActiveTab] = useState<'tos' | 'privacy' | 'compliance'>('compliance');

    const logs = [
        { id: 1, action: 'Terms Updated', user: 'System Admin', date: '2024-10-25', status: 'Active' },
        { id: 2, action: 'GDPR Audit', user: 'External Auditor', date: '2024-09-12', status: 'Passed' },
        { id: 3, action: 'Tax Compliance Check', user: 'System', date: '2024-08-30', status: 'Flagged' },
    ];

    return (
        <div className="container mx-auto px-4 py-8 max-w-5xl">
            <button 
                onClick={onBack} 
                className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-6"
            >
                <ChevronLeft size={20} /> Back to Dashboard
            </button>

            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Legal & Compliance</h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Manage platform policies and view compliance logs.</p>
                </div>
                <button className="px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg font-bold text-sm flex items-center gap-2 hover:opacity-90 transition-opacity">
                    <Download size={16} /> Export All Data
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                {/* Sidebar */}
                <div className="space-y-1">
                    <button 
                        onClick={() => setActiveTab('compliance')}
                        className={`w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 font-medium transition-all ${activeTab === 'compliance' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                    >
                        <Shield size={18} /> Compliance Logs
                    </button>
                    <button 
                        onClick={() => setActiveTab('tos')}
                        className={`w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 font-medium transition-all ${activeTab === 'tos' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                    >
                        <FileText size={18} /> Terms of Service
                    </button>
                    <button 
                        onClick={() => setActiveTab('privacy')}
                        className={`w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 font-medium transition-all ${activeTab === 'privacy' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                    >
                        <Lock size={18} /> Privacy Policy
                    </button>
                </div>

                {/* Content */}
                <div className="md:col-span-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 min-h-[500px]">
                    {activeTab === 'compliance' && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Compliance & Audit Logs</h2>
                            
                            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-xl p-4 mb-8 flex gap-3">
                                <Shield className="text-blue-600 dark:text-blue-400 shrink-0" size={24} />
                                <div>
                                    <h4 className="font-bold text-blue-900 dark:text-blue-100">PCI DSS Compliant</h4>
                                    <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                                        Last scan completed on Oct 20, 2024. No vulnerabilities found.
                                    </p>
                                </div>
                            </div>

                            <table className="w-full text-left">
                                <thead>
                                    <tr className="border-b border-slate-100 dark:border-slate-800">
                                        <th className="pb-3 text-xs font-bold text-slate-500 uppercase">Action</th>
                                        <th className="pb-3 text-xs font-bold text-slate-500 uppercase">User</th>
                                        <th className="pb-3 text-xs font-bold text-slate-500 uppercase">Date</th>
                                        <th className="pb-3 text-xs font-bold text-slate-500 uppercase">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {logs.map(log => (
                                        <tr key={log.id} className="group">
                                            <td className="py-4 text-sm font-medium text-slate-900 dark:text-white">{log.action}</td>
                                            <td className="py-4 text-sm text-slate-500">{log.user}</td>
                                            <td className="py-4 text-sm text-slate-500">{log.date}</td>
                                            <td className="py-4">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${
                                                    log.status === 'Flagged' 
                                                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' 
                                                        : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                                                }`}>
                                                    {log.status === 'Flagged' ? <AlertTriangle size={12}/> : <CheckCircle size={12}/>}
                                                    {log.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {activeTab === 'tos' && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Terms of Service</h2>
                                <button className="text-sm font-medium text-emerald-600 hover:text-emerald-500">Edit Document</button>
                            </div>
                            <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-300">
                                <h3>1. Introduction</h3>
                                <p>Welcome to EduConnect. By accessing our platform, you agree to these Terms of Service. Please read them carefully.</p>
                                <h3>2. User Responsibilities</h3>
                                <p>Users are responsible for maintaining the confidentiality of their account credentials and for all activities that occur under their account.</p>
                                <h3>3. Payments</h3>
                                <p>All payments are processed securely through our payment provider. Refunds are subject to our cancellation policy.</p>
                                <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 mt-4">
                                    <p className="text-xs text-slate-500 font-mono">Last updated: October 15, 2024</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'privacy' && (
                        <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Privacy Policy</h2>
                                <button className="text-sm font-medium text-emerald-600 hover:text-emerald-500">Edit Document</button>
                            </div>
                            <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-300">
                                <h3>Data Collection</h3>
                                <p>We collect information you provide directly to us, such as when you create an account, update your profile, or communicate with us.</p>
                                <h3>Data Usage</h3>
                                <p>We use the information we collect to provide, maintain, and improve our services, including to process transactions and send you related information.</p>
                                <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 mt-4">
                                    <p className="text-xs text-slate-500 font-mono">Version 2.4 • Effective Date: January 1, 2024</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
