
import React from 'react';
import { ChevronLeft, FileX } from 'lucide-react';

interface CancellationPolicyPageProps {
    onBack: () => void;
}

export const CancellationPolicyPage: React.FC<CancellationPolicyPageProps> = ({ onBack }) => {
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
                    <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-xl flex items-center justify-center text-red-600 dark:text-red-400">
                        <FileX size={24} />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Cancellation Policy</h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">Last updated: September 1, 2024</p>
                    </div>
                </div>

                <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-300">
                    <h3>1. Overview</h3>
                    <p>
                        We understand that plans change. Our cancellation policy is designed to be fair to both students and tutors, ensuring that everyone's time is respected.
                    </p>

                    <h3>2. For Students</h3>
                    <ul>
                        <li><strong>Free Cancellation:</strong> You can cancel or reschedule a lesson for free up to 24 hours before the scheduled start time.</li>
                        <li><strong>Late Cancellation:</strong> Cancellations made within 24 hours of the lesson start time are subject to a 100% cancellation fee. The tutor will be paid for the reserved time.</li>
                        <li><strong>No-Show:</strong> If you do not show up for your lesson within the first 15 minutes, it will be considered a no-show and charged at the full rate.</li>
                    </ul>

                    <h3>3. For Tutors</h3>
                    <ul>
                        <li><strong>Commitment:</strong> Tutors are expected to honor all scheduled lessons. Frequent cancellations may result in lower visibility or removal from the platform.</li>
                        <li><strong>Emergency Cancellation:</strong> If a tutor must cancel due to an emergency, the student will receive a full refund or a free rescheduled lesson.</li>
                        <li><strong>No-Show:</strong> If a tutor fails to attend a lesson, the student will be fully refunded and granted a credit for a future lesson.</li>
                    </ul>

                    <h3>4. Rescheduling</h3>
                    <p>
                        Rescheduling follows the same rules as cancellation. You may reschedule a lesson for free if done more than 24 hours in advance. 
                        Requests to reschedule within 24 hours are at the discretion of the tutor.
                    </p>

                    <h3>5. Exceptions</h3>
                    <p>
                        We waive cancellation fees for documented emergencies (medical issues, natural disasters, etc.) or technical issues verified by our support team. 
                        If you believe you have been charged unfairly, please contact <a href="#" className="text-emerald-600 hover:underline">Support</a>.
                    </p>

                    <h3>6. Refunds</h3>
                    <p>
                        Refunds for cancelled lessons are processed back to the original payment method within 5-10 business days. Credits applied to your EduConnect wallet are available immediately.
                    </p>
                </div>
            </div>
        </div>
    );
};
