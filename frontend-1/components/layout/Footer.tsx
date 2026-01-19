
import React from 'react';
import { BookOpen, Heart } from 'lucide-react';
import { useNavigation } from '../../contexts/NavigationContext';

export const Footer: React.FC = () => {
    const { navigate } = useNavigation();

    return (
        <footer className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 pt-16 pb-8 transition-colors duration-200 mt-auto">
            <div className="container mx-auto px-4 max-w-7xl">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-16">
                    {/* Brand Column */}
                    <div className="space-y-4">
                        <div 
                            className="flex items-center gap-2 cursor-pointer"
                            onClick={() => navigate('home')}
                        >
                            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
                                <BookOpen className="text-white" size={20} />
                            </div>
                            <span className="text-xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-700 dark:from-emerald-400 dark:to-emerald-600 bg-clip-text text-transparent">
                                EduConnect
                            </span>
                        </div>
                        <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed max-w-xs">
                            Connecting students with elite educators for personalized 1-on-1 learning. Master any subject, anytime, anywhere.
                        </p>
                    </div>

                    {/* Product */}
                    <div>
                        <h4 className="font-bold text-slate-900 dark:text-white mb-6">Product</h4>
                        <ul className="space-y-3 text-sm">
                            <li><button onClick={() => navigate('home')} className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors text-left">Find a Tutor</button></li>
                            <li><button onClick={() => navigate('referral')} className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors text-left">Refer a friend</button></li>
                            <li><button onClick={() => navigate('affiliate-program')} className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors text-left">Affiliate Program</button></li>
                        </ul>
                    </div>

                    {/* Support */}
                    <div>
                        <h4 className="font-bold text-slate-900 dark:text-white mb-6">Support</h4>
                        <ul className="space-y-3 text-sm">
                            <li><button onClick={() => navigate('support')} className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors text-left">Help Center</button></li>
                        </ul>
                    </div>

                    {/* For Tutors */}
                    <div>
                        <h4 className="font-bold text-slate-900 dark:text-white mb-6">For Tutors</h4>
                        <ul className="space-y-3 text-sm">
                            <li><button onClick={() => navigate('become-tutor')} className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors text-left">Become a Tutor</button></li>
                        </ul>
                    </div>
                </div>

                <div className="pt-8 border-t border-slate-100 dark:border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-slate-500 dark:text-slate-500 text-sm flex items-center gap-1">
                        © 2024 EduConnect Inc. Made with <Heart size={12} className="text-red-500 fill-red-500" /> globally.
                    </p>
                    <div className="flex gap-6 text-sm font-medium">
                        <button onClick={() => navigate('privacy')} className="text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">Privacy</button>
                        <button onClick={() => navigate('terms')} className="text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">Terms</button>
                        <button onClick={() => navigate('cookie-policy')} className="text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">Cookies</button>
                    </div>
                </div>
            </div>
        </footer>
    );
};
