
import React from 'react';
import { ChevronLeft, Quote, Star, ArrowRight } from 'lucide-react';

interface SuccessStoriesPageProps {
    onBack: () => void;
}

export const SuccessStoriesPage: React.FC<SuccessStoriesPageProps> = ({ onBack }) => {
    const stories = [
        {
            name: "Sarah Jenkins",
            role: "Software Developer",
            image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=200&auto=format&fit=crop",
            quote: "I landed my dream job at a tech giant after 6 months of coding lessons with James. He didn't just teach me syntax; he taught me how to think like an engineer.",
            tutor: "James Chen",
            subject: "Computer Science"
        },
        {
            name: "Marco Diaz",
            role: "University Student",
            image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=200&auto=format&fit=crop",
            quote: "Calculus was a nightmare until I met Dr. Vance. She made complex concepts visual and intuitive. I passed with an A!",
            tutor: "Dr. Elena Vance",
            subject: "Physics"
        },
        {
            name: "Emily Chen",
            role: "Writer",
            image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=200&auto=format&fit=crop",
            quote: "Marcus helped me refine my creative writing portfolio. His feedback was critical yet encouraging. I've just published my first short story.",
            tutor: "Marcus Thorne",
            subject: "Literature"
        },
        {
            name: "David O.",
            role: "Entrepreneur",
            image: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=200&auto=format&fit=crop",
            quote: "Learning Spanish was key for my business expansion in Latin America. My tutor customized every lesson to business contexts.",
            tutor: "Maria G.",
            subject: "Spanish"
        }
    ];

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            <button 
                onClick={onBack} 
                className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-12 group"
            >
                <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                Back to Dashboard
            </button>

            <div className="text-center max-w-3xl mx-auto mb-16">
                <h1 className="text-4xl md:text-5xl font-black text-slate-900 dark:text-white mb-6">Real stories from real learners</h1>
                <p className="text-xl text-slate-600 dark:text-slate-400">
                    See how EduConnect is helping students achieving their goals, one lesson at a time.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
                {stories.map((story, i) => (
                    <div key={i} className="bg-white dark:bg-slate-900 p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-xl transition-shadow flex flex-col h-full">
                        <div className="mb-6">
                            <Quote size={40} className="text-emerald-200 dark:text-emerald-900 mb-4 fill-current" />
                            <p className="text-lg text-slate-700 dark:text-slate-300 font-medium leading-relaxed italic">
                                "{story.quote}"
                            </p>
                        </div>
                        <div className="mt-auto flex items-center gap-4 pt-6 border-t border-slate-100 dark:border-slate-800">
                            <img src={story.image} alt={story.name} className="w-14 h-14 rounded-full object-cover" />
                            <div>
                                <h4 className="font-bold text-slate-900 dark:text-white">{story.name}</h4>
                                <p className="text-sm text-slate-500 dark:text-slate-400">{story.role}</p>
                            </div>
                            <div className="ml-auto text-right">
                                <p className="text-xs text-slate-400 uppercase tracking-wider font-bold">Learned</p>
                                <p className="text-sm font-bold text-emerald-600 dark:text-emerald-400">{story.subject}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="bg-slate-900 dark:bg-white rounded-3xl p-12 text-center relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-full bg-grid-white/[0.1] dark:bg-grid-slate-900/[0.1]"></div>
                <div className="relative z-10">
                    <h2 className="text-3xl font-bold text-white dark:text-slate-900 mb-6">Ready to write your own success story?</h2>
                    <button onClick={onBack} className="bg-emerald-500 hover:bg-emerald-400 text-white font-bold py-4 px-8 rounded-xl transition-colors shadow-lg hover:shadow-emerald-500/25 flex items-center gap-2 mx-auto">
                        Find a Tutor <ArrowRight size={20} />
                    </button>
                </div>
            </div>
        </div>
    );
};
