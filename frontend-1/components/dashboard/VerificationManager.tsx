
import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, X, Clock } from 'lucide-react';
import { VerificationRequest } from '../../domain/types';

interface VerificationManagerProps {
    status: 'verified' | 'pending' | 'rejected' | 'unverified' | 'approved';
    currentRequest?: VerificationRequest;
    onSubmit: (documents: File[]) => void;
    onClose: () => void;
}

export const VerificationManager: React.FC<VerificationManagerProps> = ({ status, currentRequest, onSubmit, onClose }) => {
    const [files, setFiles] = useState<File[]>([]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles(Array.from(e.target.files));
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(files);
    };

    return (
        <div className="space-y-6">
            <div className="text-center">
                {(status === 'verified' || status === 'approved') && (
                    <div className="flex flex-col items-center gap-2 text-emerald-600 mb-4">
                        <CheckCircle size={48} />
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">You are Verified!</h3>
                        <p className="text-slate-500">Your profile has the verified badge. No further action is needed.</p>
                    </div>
                )}
                {status === 'pending' && (
                    <div className="flex flex-col items-center gap-2 text-amber-500 mb-4">
                        <Clock size={48} />
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">Verification Pending</h3>
                        <p className="text-slate-500">We are reviewing your documents. This usually takes 24-48 hours.</p>
                    </div>
                )}
                {status === 'rejected' && (
                    <div className="flex flex-col items-center gap-2 text-red-500 mb-4">
                        <AlertCircle size={48} />
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">Verification Rejected</h3>
                        <p className="text-slate-500">Please review our guidelines and resubmit valid credentials.</p>
                    </div>
                )}
                {status === 'unverified' && (
                    <div className="flex flex-col items-center gap-2 text-slate-500 mb-4">
                        <ShieldIcon size={48} className="text-slate-300"/>
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">Get Verified</h3>
                        <p className="text-slate-500">Upload your degree or teaching certification to earn the Verified badge and boost student trust.</p>
                    </div>
                )}
            </div>

            {currentRequest && (
                <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700">
                    <h4 className="font-semibold text-slate-900 dark:text-white mb-3 text-sm">Submitted Documents</h4>
                    <div className="space-y-2">
                        {currentRequest.documents.map((doc, idx) => (
                            <div key={idx} className="flex items-center gap-3 p-2 bg-white dark:bg-slate-900 rounded border border-slate-100 dark:border-slate-800">
                                <FileText size={16} className="text-slate-400"/>
                                <span className="text-sm text-slate-600 dark:text-slate-300">{doc.name}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {(status === 'unverified' || status === 'rejected') && (
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-8 text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer relative">
                        <input 
                            type="file" 
                            multiple 
                            onChange={handleFileChange}
                            className="absolute inset-0 opacity-0 cursor-pointer"
                        />
                        <Upload size={24} className="mx-auto text-slate-400 mb-2"/>
                        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                            {files.length > 0 ? `${files.length} files selected` : "Click to upload documents"}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">PDF, JPG, PNG up to 5MB</p>
                    </div>
                    
                    {files.length > 0 && (
                        <div className="text-sm text-slate-600 dark:text-slate-400">
                            Files: {files.map(f => f.name).join(', ')}
                        </div>
                    )}

                    <div className="flex gap-3 justify-end pt-2">
                        <button 
                            type="button" 
                            onClick={onClose}
                            className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                        <button 
                            type="submit"
                            disabled={files.length === 0}
                            className="px-6 py-2 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Submit for Verification
                        </button>
                    </div>
                </form>
            )}
            
            {(status === 'verified' || status === 'pending' || status === 'approved') && (
                 <div className="flex justify-center">
                    <button 
                        onClick={onClose}
                        className="px-6 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                    >
                        Close
                    </button>
                </div>
            )}
        </div>
    );
};

const ShieldIcon = ({size, className}: {size: number, className?: string}) => (
    <svg 
        xmlns="http://www.w3.org/2000/svg" 
        width={size} 
        height={size} 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        className={className}
    >
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
);
