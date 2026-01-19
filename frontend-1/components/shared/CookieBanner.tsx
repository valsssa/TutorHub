
import React, { useState, useEffect } from 'react';
import { X, Shield, PieChart, Megaphone, ChevronDown, ChevronUp, Cookie } from 'lucide-react';
import { ViewState } from '../../domain/types';

interface CookieBannerProps {
    onNavigate: (view: ViewState) => void;
    isOpen?: boolean;
    onClose?: () => void;
}

export const CookieBanner: React.FC<CookieBannerProps> = ({ onNavigate, isOpen, onClose }) => {
    const [isVisible, setIsVisible] = useState(false);
    const [showDetails, setShowDetails] = useState(false);
    const [preferences, setPreferences] = useState({
        necessary: true,
        analytics: false,
        marketing: false
    });

    useEffect(() => {
        // Check if user has already made a choice
        const savedConsent = localStorage.getItem('educonnect_cookie_consent');
        if (!savedConsent && !isOpen) {
            // Small delay for better UX on initial load
            const timer = setTimeout(() => setIsVisible(true), 1000);
            return () => clearTimeout(timer);
        }
    }, [isOpen]);

    useEffect(() => {
        if (isOpen) {
            setIsVisible(true);
            setShowDetails(true);
        }
    }, [isOpen]);

    const closeBanner = () => {
        setIsVisible(false);
        if (onClose) onClose();
    };

    const saveConsent = (settings: typeof preferences) => {
        localStorage.setItem('educonnect_cookie_consent', JSON.stringify({
            ...settings,
            timestamp: new Date().toISOString()
        }));
        closeBanner();
    };

    const handleAcceptAll = () => {
        saveConsent({ necessary: true, analytics: true, marketing: true });
    };

    const handleRejectAll = () => {
        saveConsent({ necessary: true, analytics: false, marketing: false });
    };

    const handleSavePreferences = () => {
        saveConsent(preferences);
    };

    const handleCancel = () => {
        setShowDetails(false);
        if (isOpen) closeBanner();
    };

    if (!isVisible) return null;

    return (
        <div className="fixed bottom-4 left-4 right-4 z-[60] animate-in slide-in-from-bottom duration-500 flex justify-center">
            <div className="w-full max-w-3xl bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden relative">
                {/* Close button for manual mode */}
                {isOpen && (
                    <button 
                        onClick={closeBanner} 
                        className="absolute top-2 right-2 p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors z-10"
                    >
                        <X size={16} />
                    </button>
                )}

                {/* Main Banner Content */}
                <div className="p-4 md:flex items-center gap-4">
                    <div className="hidden md:flex p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg text-emerald-600 dark:text-emerald-400 shrink-0">
                        <Cookie size={24} />
                    </div>
                    
                    <div className="flex-1">
                        <div className="md:flex justify-between items-center gap-4">
                            <div className="mb-3 md:mb-0">
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-1">
                                    <span className="md:hidden"><Cookie size={16} className="text-emerald-500"/></span>
                                    We use cookies
                                </h3>
                                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                                    We use cookies to enhance your experience. By continuing to visit this site you agree to our use of cookies. <button onClick={() => onNavigate('cookie-policy')} className="text-emerald-600 hover:underline font-medium">Learn more</button>.
                                </p>
                            </div>

                            {!showDetails && (
                                <div className="flex gap-2 shrink-0">
                                    <button 
                                        onClick={() => setShowDetails(true)}
                                        className="px-3 py-1.5 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 text-xs font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                                    >
                                        Customize
                                    </button>
                                    <button 
                                        onClick={handleRejectAll}
                                        className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
                                    >
                                        Reject
                                    </button>
                                    <button 
                                        onClick={handleAcceptAll}
                                        className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition-colors shadow-sm whitespace-nowrap"
                                    >
                                        Accept All
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Detailed Preferences */}
                {showDetails && (
                    <div className="border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 p-4 animate-in slide-in-from-bottom-4 fade-in">
                        <div className="grid gap-3 mb-4">
                            
                            {/* Strictly Necessary */}
                            <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                                <div className="flex gap-3 items-center">
                                    <Shield className="text-emerald-500 shrink-0" size={16} />
                                    <div>
                                        <h4 className="font-bold text-slate-900 dark:text-white text-xs">Strictly Necessary</h4>
                                    </div>
                                </div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                                    Required
                                </div>
                            </div>

                            {/* Analytics */}
                            <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                                <div className="flex gap-3 items-center">
                                    <PieChart className="text-blue-500 shrink-0" size={16} />
                                    <div>
                                        <h4 className="font-bold text-slate-900 dark:text-white text-xs">Analytics</h4>
                                    </div>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input 
                                        type="checkbox" 
                                        className="sr-only peer"
                                        checked={preferences.analytics}
                                        onChange={(e) => setPreferences(p => ({ ...p, analytics: e.target.checked }))}
                                    />
                                    <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                                </label>
                            </div>

                            {/* Marketing */}
                            <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                                <div className="flex gap-3 items-center">
                                    <Megaphone className="text-purple-500 shrink-0" size={16} />
                                    <div>
                                        <h4 className="font-bold text-slate-900 dark:text-white text-xs">Marketing</h4>
                                    </div>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input 
                                        type="checkbox" 
                                        className="sr-only peer"
                                        checked={preferences.marketing}
                                        onChange={(e) => setPreferences(p => ({ ...p, marketing: e.target.checked }))}
                                    />
                                    <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                                </label>
                            </div>
                        </div>

                        <div className="flex justify-end gap-2">
                            <button 
                                onClick={handleCancel}
                                className="text-xs text-slate-500 hover:text-slate-900 dark:hover:text-white font-medium px-3 py-1.5"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={handleSavePreferences}
                                className="px-4 py-1.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold rounded-lg hover:opacity-90 transition-opacity"
                            >
                                Save Preferences
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
