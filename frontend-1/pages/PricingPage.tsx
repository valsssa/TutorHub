
import React from 'react';
import { ChevronLeft, Check, X, ArrowRight } from 'lucide-react';
import { ViewState } from '../domain/types';

interface PricingPageProps {
    onBack: () => void;
    onNavigate: (view: ViewState) => void;
}

export const PricingPage: React.FC<PricingPageProps> = ({ onBack, onNavigate }) => {
    return (
        <div className="container mx-auto px-4 py-8 max-w-6xl">
            <button 
                onClick={onBack} 
                className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-6 group"
            >
                <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                Back to Dashboard
            </button>

            <div className="text-center mb-16">
                <h1 className="text-4xl md:text-5xl font-black text-slate-900 dark:text-white mb-6">Simple, transparent pricing</h1>
                <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
                    EduConnect is free to join. You only pay when you book a lesson. 
                    No hidden subscription fees for students.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                {/* Student Plan */}
                <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-2 bg-slate-200 dark:bg-slate-700"></div>
                    <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Students</h3>
                    <p className="text-slate-500 dark:text-slate-400 mb-6">For lifelong learners</p>
                    <div className="text-4xl font-black text-slate-900 dark:text-white mb-1">$0<span className="text-lg font-medium text-slate-500 dark:text-slate-400">/mo</span></div>
                    <p className="text-sm text-slate-500 mb-8">Pay per lesson only</p>

                    <ul className="space-y-4 mb-8">
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-emerald-500 shrink-0" size={18} />
                            <span>Access to 30,000+ tutors</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-emerald-500 shrink-0" size={18} />
                            <span>Use of online classroom</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-emerald-500 shrink-0" size={18} />
                            <span>Free tutor replacement</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-emerald-500 shrink-0" size={18} />
                            <span>Secure payments</span>
                        </li>
                    </ul>

                    <button 
                        onClick={() => onNavigate('home')}
                        className="w-full py-3 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-bold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                    >
                        Start Learning
                    </button>
                </div>

                {/* Tutor Standard */}
                <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border-2 border-emerald-500 shadow-2xl relative transform md:-translate-y-4">
                    <div className="absolute top-4 right-4 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                        Popular
                    </div>
                    <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Tutors</h3>
                    <p className="text-slate-500 dark:text-slate-400 mb-6">For passionate educators</p>
                    <div className="text-4xl font-black text-slate-900 dark:text-white mb-1">15%<span className="text-lg font-medium text-slate-500 dark:text-slate-400"> fee</span></div>
                    <p className="text-sm text-slate-500 mb-8">Per completed lesson</p>

                    <ul className="space-y-4 mb-8">
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-emerald-500 shrink-0" size={18} />
                            <span>Guaranteed payments</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-emerald-500 shrink-0" size={18} />
                            <span>Integrated video classroom</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-emerald-500 shrink-0" size={18} />
                            <span>Marketing & student acquisition</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-emerald-500 shrink-0" size={18} />
                            <span>Calendar management tools</span>
                        </li>
                    </ul>

                    <button 
                        onClick={() => onNavigate('become-tutor')}
                        className="w-full py-3 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-500/20"
                    >
                        Become a Tutor
                    </button>
                </div>

                {/* Enterprise */}
                <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-2 bg-purple-500"></div>
                    <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Enterprise</h3>
                    <p className="text-slate-500 dark:text-slate-400 mb-6">For schools & organizations</p>
                    <div className="text-4xl font-black text-slate-900 dark:text-white mb-1">Custom</div>
                    <p className="text-sm text-slate-500 mb-8">Tailored to your needs</p>

                    <ul className="space-y-4 mb-8">
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-purple-500 shrink-0" size={18} />
                            <span>Bulk lesson purchasing</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-purple-500 shrink-0" size={18} />
                            <span>Dedicated account manager</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-purple-500 shrink-0" size={18} />
                            <span>Custom reporting</span>
                        </li>
                        <li className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                            <Check className="text-purple-500 shrink-0" size={18} />
                            <span>SSO Integration</span>
                        </li>
                    </ul>

                    <button 
                        onClick={() => onNavigate('support')}
                        className="w-full py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-bold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                    >
                        Contact Sales
                    </button>
                </div>
            </div>
        </div>
    );
};
