
import React from 'react';
import { Heart, Search } from 'lucide-react';
import { Tutor } from '../domain/types';
import { TutorCard } from '../components/tutor/TutorCard';

interface SavedTutorsPageProps {
    savedTutors: Tutor[];
    onViewProfile: (tutor: Tutor) => void;
    onToggleSave: (e: React.MouseEvent, id: string) => void;
    onBook: (e: React.MouseEvent, tutor: Tutor) => void;
    onQuickBook: (e: React.MouseEvent, tutor: Tutor) => void;
    onSlotBook: (e: React.MouseEvent, tutor: Tutor, slot: string) => void;
    onMessage: (e: React.MouseEvent, tutor: Tutor) => void;
    onBrowse: () => void;
}

export const SavedTutorsPage: React.FC<SavedTutorsPageProps> = ({ 
    savedTutors, onViewProfile, onToggleSave, onBook, onQuickBook, onSlotBook, onMessage, onBrowse
}) => {
    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            <h1 className="text-3xl font-bold mb-2 text-slate-900 dark:text-white flex items-center gap-3">
                <Heart size={28} className="text-emerald-500 fill-emerald-500"/> Saved Tutors
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mb-8">Your shortlisted educators for quick access.</p>
            
            {savedTutors.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {savedTutors.map(tutor => (
                        <TutorCard 
                            key={tutor.id} 
                            tutor={tutor} 
                            onViewProfile={onViewProfile}
                            onToggleSave={onToggleSave}
                            onBook={onBook}
                            onQuickBook={onQuickBook}
                            onSlotBook={onSlotBook}
                            onMessage={onMessage}
                            isSaved={true}
                        />
                    ))}
                </div>
            ) : (
                <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 border-dashed">
                    <div className="w-20 h-20 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
                        <Heart size={32} />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">No saved tutors yet</h3>
                    <p className="text-slate-500 dark:text-slate-400 max-w-xs mx-auto mb-6">
                        Browse the marketplace and save tutors you're interested in to see them here.
                    </p>
                    <button 
                        onClick={onBrowse}
                        className="inline-flex items-center gap-2 text-emerald-600 font-bold hover:underline transition-colors focus:outline-none"
                    >
                        <Search size={18} /> Browse Tutors
                    </button>
                </div>
            )}
        </div>
    );
};
