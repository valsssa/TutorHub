
import React, { useState } from 'react';
import { Star, X } from 'lucide-react';
import { Modal } from './UI';

interface ReviewModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (rating: number, comment: string) => void;
    tutorName: string;
}

export const ReviewModal: React.FC<ReviewModalProps> = ({ isOpen, onClose, onSubmit, tutorName }) => {
    const [rating, setRating] = useState(0);
    const [hoverRating, setHoverRating] = useState(0);
    const [comment, setComment] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (rating === 0) return;
        onSubmit(rating, comment);
        // Reset form
        setRating(0);
        setComment('');
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Rate your session">
            <div className="text-center mb-6">
                <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                    👋
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white">How was your lesson?</h3>
                <p className="text-slate-500 dark:text-slate-400">
                    Share your experience with <span className="font-semibold text-slate-900 dark:text-white">{tutorName}</span>
                </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="flex justify-center gap-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                        <button
                            key={star}
                            type="button"
                            onClick={() => setRating(star)}
                            onMouseEnter={() => setHoverRating(star)}
                            onMouseLeave={() => setHoverRating(0)}
                            className="p-1 focus:outline-none transition-transform hover:scale-110"
                        >
                            <Star 
                                size={32} 
                                className={`transition-colors ${
                                    star <= (hoverRating || rating) 
                                        ? 'fill-amber-400 text-amber-400' 
                                        : 'fill-transparent text-slate-300 dark:text-slate-600'
                                }`} 
                            />
                        </button>
                    ))}
                </div>
                
                <div className="text-center text-sm font-medium text-emerald-600 h-5">
                    {rating > 0 ? (
                        rating === 5 ? 'Excellent!' :
                        rating === 4 ? 'Good' :
                        rating === 3 ? 'Okay' :
                        rating === 2 ? 'Poor' : 'Terrible'
                    ) : (
                        hoverRating > 0 ? (
                            hoverRating === 5 ? 'Excellent!' :
                            hoverRating === 4 ? 'Good' :
                            hoverRating === 3 ? 'Okay' :
                            hoverRating === 2 ? 'Poor' : 'Terrible'
                        ) : ''
                    )}
                </div>

                <div>
                    <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">
                        Write a review
                    </label>
                    <textarea
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        placeholder="What did you like? What could be improved?"
                        className="w-full p-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 min-h-[120px] resize-none transition-all"
                    />
                </div>

                <div className="flex gap-3">
                    <button
                        type="button"
                        onClick={onClose}
                        className="flex-1 py-3 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                    >
                        Skip
                    </button>
                    <button
                        type="submit"
                        disabled={rating === 0}
                        className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        Submit Review
                    </button>
                </div>
            </form>
        </Modal>
    );
};
