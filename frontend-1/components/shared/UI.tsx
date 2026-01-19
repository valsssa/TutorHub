
import React from 'react';
import { X, Shield } from 'lucide-react';

export const Badge: React.FC<{ children: React.ReactNode, variant?: 'default' | 'verified' | 'pending' | 'rejected' | 'approved' }> = ({ children, variant = 'default' }) => {
    let classes = 'bg-slate-100 text-slate-600 border border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
    
    if (variant === 'verified' || variant === 'approved') {
        classes = 'bg-emerald-100 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/50 dark:text-emerald-400 dark:border-emerald-800';
    } else if (variant === 'pending') {
        classes = 'bg-amber-100 text-amber-700 border border-amber-200 dark:bg-amber-900/50 dark:text-amber-400 dark:border-amber-800';
    } else if (variant === 'rejected') {
        classes = 'bg-red-100 text-red-700 border border-red-200 dark:bg-red-900/50 dark:text-red-400 dark:border-red-800';
    }

    return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${classes}`}>
            {(variant === 'verified' || variant === 'approved') && <Shield size={10} className="mr-1 fill-emerald-500/20" />}
            {children}
        </span>
    );
};

export const Modal: React.FC<{ isOpen: boolean; onClose: () => void; title?: string; children: React.ReactNode, maxWidth?: string }> = ({ isOpen, onClose, title, children, maxWidth = 'max-w-lg' }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className={`bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full ${maxWidth} shadow-2xl animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto`}>
        <div className="flex justify-between items-center p-6 border-b border-slate-100 dark:border-slate-800 sticky top-0 bg-white/95 dark:bg-slate-900/95 backdrop-blur z-10">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{title}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors"><X size={24} /></button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};
