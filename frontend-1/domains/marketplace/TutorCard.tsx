
import React from 'react';
import { Star, Heart, MessageCircle, GraduationCap, MessageSquareQuote } from 'lucide-react';
import { Tutor } from '../../types';
import { Badge } from '../../components/shared/UI';

interface TutorCardProps {
    tutor: Tutor;
    onViewProfile: (tutor: Tutor) => void;
    onToggleSave: (e: React.MouseEvent, id: string) => void;
    onBook: (e: React.MouseEvent, tutor: Tutor) => void;
    onQuickBook: (e: React.MouseEvent, tutor: Tutor) => void;
    onSlotBook: (e: React.MouseEvent, tutor: Tutor, slot: string) => void;
    onMessage: (e: React.MouseEvent, tutor: Tutor) => void;
    isSaved: boolean;
}

export const TutorCard: React.FC<TutorCardProps> = ({ tutor, onViewProfile, onToggleSave, onBook, onQuickBook, onSlotBook, onMessage, isSaved }) => (
    <div 
        onClick={() => onViewProfile(tutor)}
        className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 transition-all hover:shadow-[0_0_20px_rgba(16,185,129,0.1)] group overflow-hidden flex flex-col cursor-pointer"
    >
        <div className="p-5 flex-1 relative flex flex-col">
            <div className="absolute top-4 right-4 z-10">
                <button 
                    onClick={(e) => onToggleSave(e, tutor.id)}
                    className="p-2 rounded-full bg-slate-100 dark:bg-slate-900/50 hover:bg-slate-200 dark:hover:bg-slate-800 transition-all active:scale-90"
                    title={isSaved ? "Remove from saved" : "Save tutor"}
                >
                    <Heart 
                        size={18} 
                        className={`transition-colors duration-200 ${isSaved ? "fill-emerald-500 text-emerald-500" : "text-slate-400"}`}
                    />
                </button>
            </div>

            <div className="flex gap-4 mb-4">
                <img src={tutor.imageUrl} alt={tutor.name} className="w-16 h-16 rounded-full object-cover border-2 border-slate-200 dark:border-slate-700 shrink-0" />
                <div>
                     <h3 className="font-bold text-lg text-slate-900 dark:text-white group-hover:text-emerald-500 dark:group-hover:text-emerald-400 transition-colors line-clamp-1">{tutor.name}</h3>
                     <p className="text-slate-500 dark:text-slate-400 text-xs line-clamp-1 mb-1">{tutor.title}</p>
                     <div className="flex items-center gap-1 text-amber-500 dark:text-amber-400 text-xs font-bold">
                        <Star size={12} fill="currentColor" /> {tutor.rating} <span className="text-slate-400 font-normal">({tutor.reviews})</span>
                    </div>
                </div>
            </div>
            
            <div className="mb-3">
                {tutor.isVerified && <Badge variant="verified">Verified Expert</Badge>}
            </div>

            {/* Educational Background Snippet */}
            {tutor.education.length > 0 && (
                <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 mb-3 bg-slate-50 dark:bg-slate-800/50 p-1.5 rounded-lg">
                    <GraduationCap size={14} className="text-emerald-500 shrink-0" />
                    <span className="truncate">{tutor.education[0]}</span>
                </div>
            )}

            {/* Teaching Philosophy Snippet */}
            {tutor.philosophy && (
                <div className="mb-3 relative pl-3 border-l-2 border-emerald-500/30">
                     <p className="text-xs italic text-slate-500 dark:text-slate-400 line-clamp-2">
                        "{tutor.philosophy}"
                     </p>
                </div>
            )}
            
            <div className="flex flex-wrap gap-1.5 mb-4 mt-auto">
                {tutor.topics.slice(0, 3).map(topic => (
                    <span key={topic} className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">{topic}</span>
                ))}
            </div>

            {/* Testimonial Snippet */}
            {tutor.reviewsList.length > 0 && (
                <div className="flex items-start gap-2 mb-4 text-xs text-slate-500 dark:text-slate-500 bg-slate-50 dark:bg-slate-800/30 p-2 rounded">
                    <MessageSquareQuote size={12} className="shrink-0 mt-0.5 text-emerald-500" />
                    <span className="line-clamp-1 italic">"{tutor.reviewsList[0].comment}"</span>
                </div>
            )}

            <div className="border-t border-slate-100 dark:border-slate-800 pt-3">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-2">Next Available</p>
                <div className="flex gap-2 overflow-hidden">
                    {tutor.availability.slice(0, 2).map((slot, idx) => (
                        <button 
                            key={idx}
                            onClick={(e) => onSlotBook(e, tutor, slot)}
                            className="text-[10px] whitespace-nowrap bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 px-2 py-1 rounded hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors"
                        >
                           {new Date(slot).toLocaleDateString([], {weekday: 'short'})}, {new Date(slot).toLocaleTimeString([], {hour: 'numeric', minute:'2-digit'})}
                        </button>
                    ))}
                </div>
            </div>
        </div>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 flex items-center justify-between">
             <div className="font-bold text-lg text-slate-900 dark:text-white">${tutor.hourlyRate}<span className="text-slate-500 text-xs font-normal">/hr</span></div>
             <button 
                onClick={(e) => onMessage(e, tutor)}
                className="text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                title="Message Tutor"
             >
                <MessageCircle size={24} />
             </button>
        </div>
    </div>
);
