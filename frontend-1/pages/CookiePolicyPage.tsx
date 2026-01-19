
import React from 'react';
import { ChevronLeft, Cookie } from 'lucide-react';

interface CookiePolicyPageProps {
    onBack: () => void;
}

export const CookiePolicyPage: React.FC<CookiePolicyPageProps> = ({ onBack }) => {
    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
            <button 
                onClick={onBack} 
                className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-8 group"
            >
                <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                Back
            </button>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 md:p-12 shadow-sm">
                <div className="flex items-center gap-4 mb-8 pb-8 border-b border-slate-100 dark:border-slate-800">
                    <div className="w-12 h-12 bg-amber-100 dark:bg-amber-900/30 rounded-xl flex items-center justify-center text-amber-600 dark:text-amber-400">
                        <Cookie size={24} />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Cookie Policy</h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">Last updated: January 15, 2024</p>
                    </div>
                </div>

                <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-300">
                    <h3>1. What are cookies?</h3>
                    <p>
                        Cookies are small text files that are placed on your computer or mobile device when you visit a website. 
                        They are widely used to make websites work more efficiently and to provide information to the owners of the site.
                    </p>

                    <h3>2. How we use cookies</h3>
                    <p>We use cookies for the following purposes:</p>
                    <ul>
                        <li><strong>Essential Cookies:</strong> These are necessary for the website to function properly (e.g., keeping you logged in).</li>
                        <li><strong>Performance Cookies:</strong> These help us understand how visitors interact with our website by collecting anonymous information.</li>
                        <li><strong>Functional Cookies:</strong> These allow the website to remember choices you make (such as your username or language).</li>
                        <li><strong>Marketing Cookies:</strong> These are used to track visitors across websites to display relevant ads.</li>
                    </ul>

                    <h3>3. Managing Cookies</h3>
                    <p>
                        Most web browsers allow you to control cookies through their settings preferences. However, if you limit the ability of websites to set cookies, 
                        you may worsen your overall user experience, since it will no longer be personalized to you.
                    </p>

                    <h3>4. Updates to this policy</h3>
                    <p>
                        We may update this Cookie Policy from time to time. We encourage you to periodically review this page for the latest information on our privacy practices.
                    </p>

                    <h3>5. Contact Us</h3>
                    <p>
                        If you have any questions about our use of cookies, please contact us at support@educonnect.com.
                    </p>
                </div>
            </div>
        </div>
    );
};
