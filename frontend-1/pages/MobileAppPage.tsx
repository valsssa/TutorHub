
import React from 'react';
import { ChevronLeft, Star } from 'lucide-react';

interface MobileAppPageProps {
    onBack: () => void;
}

export const MobileAppPage: React.FC<MobileAppPageProps> = ({ onBack }) => {
    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
            <div className="container mx-auto px-4 py-8 max-w-6xl">
                <button 
                    onClick={onBack} 
                    className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-6 group"
                >
                    <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                    Back to Dashboard
                </button>

                <div className="flex flex-col lg:flex-row items-center gap-16 py-12">
                    <div className="flex-1 space-y-8 text-center lg:text-left">
                        <h1 className="text-5xl lg:text-7xl font-black text-slate-900 dark:text-white tracking-tight leading-tight">
                            Learn on the go with <span className="text-emerald-600 dark:text-emerald-400">EduConnect App</span>
                        </h1>
                        <p className="text-xl text-slate-600 dark:text-slate-400 leading-relaxed max-w-2xl mx-auto lg:mx-0">
                            Take your classroom with you. Message tutors, schedule lessons, and join video calls directly from your pocket.
                        </p>
                        
                        <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                            <button className="bg-slate-900 text-white px-6 py-3 rounded-xl flex items-center justify-center gap-3 hover:bg-slate-800 transition-all shadow-lg hover:-translate-y-1">
                                <svg viewBox="0 0 24 24" className="w-8 h-8 fill-current"><path d="M17.5 12.5c-.3 2.5 1.5 3.9 1.6 4-1.3 2-3 3.5-4.2 3.5-1.1 0-1.5-.7-2.9-.7s-1.8.7-2.9.7c-1.1 0-2.8-1.7-4.1-4.2-2.1-4-1-8.9 2-10.4 1.1-.5 2.1-.2 2.9.2.7.4 1.9.4 2.6.2.9-.3 2.3-1.4 3.3-1 1.6.1 3 1 3.8 2.2-.1.1-2.2 1.3-2.1 5.5m-3.2-9c.6-.7 1-1.7.9-2.6-.9 0-1.9.5-2.5 1.3-.5.6-.9 1.6-.8 2.5.9.1 1.9-.5 2.4-1.2"/></svg>
                                <div className="text-left">
                                    <div className="text-[10px] uppercase font-bold opacity-80">Download on the</div>
                                    <div className="text-lg font-bold leading-none">App Store</div>
                                </div>
                            </button>
                            <button className="bg-slate-900 text-white px-6 py-3 rounded-xl flex items-center justify-center gap-3 hover:bg-slate-800 transition-all shadow-lg hover:-translate-y-1">
                                <svg viewBox="0 0 24 24" className="w-8 h-8 fill-current"><path d="M3,20.5V3.5C3,2.91 3.34,2.39 3.84,2.15L13.69,12L3.84,21.85C3.34,21.6 3,21.09 3,20.5M16.81,15.12L6.05,21.34L14.54,12.85L16.81,15.12M20.16,10.81C20.5,11.08 20.75,11.5 20.75,12C20.75,12.5 20.53,12.92 20.16,13.19L17.89,14.5L15.39,12L17.89,9.5L20.16,10.81M6.05,2.66L16.81,8.88L14.54,11.15L6.05,2.66Z" /></svg>
                                <div className="text-left">
                                    <div className="text-[10px] uppercase font-bold opacity-80">Get it on</div>
                                    <div className="text-lg font-bold leading-none">Google Play</div>
                                </div>
                            </button>
                        </div>

                        <div className="flex items-center justify-center lg:justify-start gap-6 pt-4">
                            <div className="flex items-center gap-1">
                                <div className="flex text-amber-400">
                                    <Star size={20} fill="currentColor" />
                                    <Star size={20} fill="currentColor" />
                                    <Star size={20} fill="currentColor" />
                                    <Star size={20} fill="currentColor" />
                                    <Star size={20} fill="currentColor" />
                                </div>
                                <span className="font-bold text-slate-900 dark:text-white ml-2">4.9/5</span>
                            </div>
                            <div className="w-px h-8 bg-slate-300 dark:bg-slate-700"></div>
                            <div className="font-bold text-slate-900 dark:text-white">
                                1M+ <span className="font-normal text-slate-500 dark:text-slate-400">Downloads</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 relative">
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-emerald-500/20 rounded-full blur-3xl -z-10"></div>
                        {/* Mock Phone */}
                        <div className="relative mx-auto border-gray-800 dark:border-gray-800 bg-gray-800 border-[14px] rounded-[2.5rem] h-[600px] w-[300px] shadow-2xl">
                            <div className="h-[32px] w-[3px] bg-gray-800 absolute -start-[17px] top-[72px] rounded-s-lg"></div>
                            <div className="h-[46px] w-[3px] bg-gray-800 absolute -start-[17px] top-[124px] rounded-s-lg"></div>
                            <div className="h-[46px] w-[3px] bg-gray-800 absolute -start-[17px] top-[178px] rounded-s-lg"></div>
                            <div className="h-[64px] w-[3px] bg-gray-800 absolute -end-[17px] top-[142px] rounded-e-lg"></div>
                            <div className="rounded-[2rem] overflow-hidden w-full h-full bg-white dark:bg-slate-900 relative">
                                {/* App UI Mock */}
                                <div className="p-4 bg-emerald-600 text-white h-32 pt-12">
                                    <div className="font-bold text-lg mb-1">Hello, Alex!</div>
                                    <div className="text-emerald-100 text-xs">You have a lesson in 30 mins</div>
                                </div>
                                <div className="p-4 -mt-6">
                                    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-lg mb-4">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="w-10 h-10 bg-slate-200 rounded-full"></div>
                                            <div>
                                                <div className="font-bold text-slate-900 dark:text-white text-sm">English Lesson</div>
                                                <div className="text-xs text-slate-500">with Marcus Thorne</div>
                                            </div>
                                        </div>
                                        <div className="w-full bg-emerald-600 text-white text-center py-2 rounded-lg text-sm font-bold">Join Class</div>
                                    </div>
                                    <div className="space-y-3">
                                        <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
                                        <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
                                        <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
                                    </div>
                                </div>
                                {/* Bottom Nav */}
                                <div className="absolute bottom-0 w-full h-16 bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 flex justify-around items-center px-4">
                                    <div className="w-6 h-6 bg-emerald-600 rounded-full"></div>
                                    <div className="w-6 h-6 bg-slate-300 dark:bg-slate-700 rounded-full"></div>
                                    <div className="w-6 h-6 bg-slate-300 dark:bg-slate-700 rounded-full"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
