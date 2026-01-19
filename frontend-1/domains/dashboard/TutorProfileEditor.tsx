
import React, { useState, useRef, useEffect } from 'react';
import { Tutor } from '../../types';
import { Save, X, Youtube, Move, Minus, Plus, User, DollarSign, Globe, BookOpen, MessageSquare, Briefcase, Camera, Video, Sparkles, Layout } from 'lucide-react';
import { Modal } from '../../components/shared/UI';

interface TutorProfileEditorProps {
    tutor: Tutor;
    onSave: (updatedTutor: Tutor) => void;
    onCancel: () => void;
}

export const TutorProfileEditor: React.FC<TutorProfileEditorProps> = ({ tutor, onSave, onCancel }) => {
    const [formData, setFormData] = useState<Tutor>({ ...tutor });
    const [showPhotoModal, setShowPhotoModal] = useState(false);
    const [zoom, setZoom] = useState(1);
    
    // Local state for array inputs
    const [topicsString, setTopicsString] = useState(tutor.topics.join(', '));
    const [languagesString, setLanguagesString] = useState(tutor.languages?.join(', ') || '');
    
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (showPhotoModal) setZoom(1);
    }, [showPhotoModal]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: name === 'hourlyRate' ? parseFloat(value) || 0 : value
        }));
    };

    const handleTopicsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setTopicsString(e.target.value);
        const topics = e.target.value.split(',').map(t => t.trim()).filter(Boolean);
        setFormData(prev => ({ ...prev, topics }));
    };

    const handleLanguagesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setLanguagesString(e.target.value);
        const languages = e.target.value.split(',').map(t => t.trim()).filter(Boolean);
        setFormData(prev => ({ ...prev, languages }));
    };
    
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.size > 2 * 1024 * 1024) {
                alert("File size exceeds 2MB");
                return;
            }
            const reader = new FileReader();
            reader.onloadend = () => {
                setFormData(prev => ({ ...prev, imageUrl: reader.result as string }));
                setShowPhotoModal(true);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(formData);
    };

    return (
        <form onSubmit={handleSubmit} className="flex flex-col h-full bg-slate-50 dark:bg-slate-950">
            <div className="flex-1 overflow-y-auto">
                <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
                    <div className="mb-6 lg:hidden flex items-center justify-between">
                        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Edit Profile</h1>
                        <button 
                            type="button" 
                            onClick={onCancel}
                            className="p-2 text-slate-500 hover:text-slate-900 dark:hover:text-white"
                        >
                            <X size={24} />
                        </button>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
                        
                        {/* LEFT COLUMN: Identity & Photo */}
                        <div className="lg:col-span-4 space-y-6">
                            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm sticky top-6">
                                <div className="flex flex-col items-center text-center">
                                    <div className="relative group mb-6">
                                        <div className="w-32 h-32 sm:w-40 sm:h-40 rounded-full p-1.5 border-2 border-dashed border-slate-300 dark:border-slate-700 group-hover:border-emerald-500 transition-colors">
                                            <div className="w-full h-full rounded-full overflow-hidden relative bg-slate-100 dark:bg-slate-800">
                                                <img 
                                                    src={formData.imageUrl} 
                                                    alt="Profile" 
                                                    className="w-full h-full object-cover"
                                                    onError={(e) => { (e.target as HTMLImageElement).src = 'https://via.placeholder.com/150?text=No+Img' }} 
                                                />
                                            </div>
                                        </div>
                                        <button 
                                            type="button"
                                            onClick={() => fileInputRef.current?.click()}
                                            className="absolute bottom-1 right-1 p-2.5 bg-emerald-600 text-white rounded-full shadow-lg hover:bg-emerald-500 transition-transform hover:scale-105 active:scale-95 border-4 border-white dark:border-slate-900"
                                            title="Change photo"
                                        >
                                            <Camera size={18} />
                                        </button>
                                        <input 
                                            type="file" 
                                            ref={fileInputRef}
                                            onChange={handleFileChange}
                                            accept="image/png, image/jpeg"
                                            className="hidden"
                                        />
                                    </div>

                                    <div className="w-full space-y-4">
                                        <div className="space-y-1.5 text-left">
                                            <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide ml-1">Display Name</label>
                                            <div className="relative">
                                                <User size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                                <input 
                                                    type="text" 
                                                    name="name" 
                                                    value={formData.name} 
                                                    onChange={handleChange}
                                                    className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-medium text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                    placeholder="e.g. Dr. Elena Vance"
                                                    required
                                                />
                                            </div>
                                        </div>

                                        <div className="space-y-1.5 text-left">
                                            <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide ml-1">Professional Title</label>
                                            <div className="relative">
                                                <Briefcase size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                                <input 
                                                    type="text" 
                                                    name="title" 
                                                    value={formData.title} 
                                                    onChange={handleChange}
                                                    className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-medium text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                    placeholder="e.g. PhD in Astrophysics"
                                                    required
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* RIGHT COLUMN: Details */}
                        <div className="lg:col-span-8 space-y-6">
                            
                            {/* Bio & Philosophy Card */}
                            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
                                <div className="flex items-center gap-2 mb-6 border-b border-slate-100 dark:border-slate-800 pb-4">
                                    <BookOpen className="text-emerald-500" size={24} />
                                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">About & Philosophy</h3>
                                </div>
                                
                                <div className="space-y-6">
                                    <div className="space-y-2">
                                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Bio</label>
                                        <textarea 
                                            name="bio" 
                                            value={formData.bio} 
                                            onChange={handleChange}
                                            rows={6}
                                            className="w-full p-4 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all leading-relaxed resize-y"
                                            placeholder="Tell students about your experience..."
                                            required
                                        />
                                        <p className="text-xs text-slate-400 text-right">Markdown supported</p>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Teaching Philosophy</label>
                                        <div className="relative">
                                            <MessageSquare size={18} className="absolute top-3.5 left-3.5 text-slate-400" />
                                            <textarea 
                                                name="philosophy" 
                                                value={formData.philosophy} 
                                                onChange={handleChange}
                                                rows={3}
                                                className="w-full pl-10 pr-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all italic resize-y"
                                                placeholder="What is your approach to teaching?"
                                                required
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Expertise & Rates Card */}
                            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
                                <div className="flex items-center gap-2 mb-6 border-b border-slate-100 dark:border-slate-800 pb-4">
                                    <Sparkles className="text-purple-500" size={24} />
                                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">Expertise & Rates</h3>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Hourly Rate ($)</label>
                                        <div className="relative">
                                            <DollarSign size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                            <input 
                                                type="number" 
                                                name="hourlyRate" 
                                                value={formData.hourlyRate} 
                                                onChange={handleChange}
                                                min="0"
                                                step="5"
                                                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-medium text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                required
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Native Language</label>
                                        <div className="relative">
                                            <Globe size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                            <input 
                                                type="text" 
                                                name="nativeLanguage" 
                                                value={formData.nativeLanguage || ''} 
                                                onChange={handleChange}
                                                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-medium text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                placeholder="e.g. English"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Subjects</label>
                                        <div className="relative">
                                            <Layout size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                            <input 
                                                type="text" 
                                                name="topics" 
                                                value={topicsString} 
                                                onChange={handleTopicsChange}
                                                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-medium text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                placeholder="Math, Physics (comma separated)"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Spoken Languages</label>
                                        <div className="relative">
                                            <MessageSquare size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                            <input 
                                                type="text" 
                                                name="languages" 
                                                value={languagesString} 
                                                onChange={handleLanguagesChange}
                                                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-medium text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                                placeholder="English, Spanish (comma separated)"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Media Card */}
                            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
                                <div className="flex items-center gap-2 mb-6 border-b border-slate-100 dark:border-slate-800 pb-4">
                                    <Video className="text-red-500" size={24} />
                                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">Media</h3>
                                </div>

                                <div className="space-y-1.5">
                                    <label className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Video Introduction URL</label>
                                    <div className="relative">
                                        <Youtube size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                        <input 
                                            type="url" 
                                            name="videoUrl" 
                                            value={formData.videoUrl || ''} 
                                            onChange={handleChange}
                                            className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-medium text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all"
                                            placeholder="https://www.youtube.com/watch?v=..."
                                        />
                                    </div>
                                    <p className="text-xs text-slate-400 pt-1">Paste a link to your introduction video from YouTube or Vimeo.</p>
                                </div>
                            </div>

                        </div>
                    </div>
                </div>
            </div>

            {/* Sticky Action Footer */}
            <div className="sticky bottom-0 z-20 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 px-6 py-4 flex justify-end gap-3 safe-area-pb shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
                <button 
                    type="button" 
                    onClick={onCancel}
                    className="px-6 py-2.5 text-sm font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors flex items-center gap-2"
                >
                    <X size={18} /> Cancel
                </button>
                <button 
                    type="submit"
                    className="px-8 py-2.5 bg-emerald-600 text-white text-sm font-bold rounded-xl hover:bg-emerald-500 transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2 active:scale-95"
                >
                    <Save size={18} /> Save Profile
                </button>
            </div>

            {/* Photo Crop Modal */}
            <Modal isOpen={showPhotoModal} onClose={() => setShowPhotoModal(false)} title="Adjust Profile Picture" maxWidth="max-w-xl">
                <div className="flex flex-col gap-6 p-2">
                    <div className="bg-slate-950 rounded-2xl overflow-hidden relative aspect-square w-full max-w-sm mx-auto shadow-inner border border-slate-800">
                        <img 
                            src={formData.imageUrl} 
                            className="w-full h-full object-cover opacity-90 transition-transform duration-100 origin-center" 
                            style={{ transform: `scale(${zoom})` }}
                            alt="Crop target"
                        />
                        <div className="absolute inset-0 pointer-events-none">
                            <div className="absolute inset-0 bg-black/50 mask-circle"></div>
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 border-2 border-white rounded-full shadow-[0_0_0_9999px_rgba(0,0,0,0.5)]"></div>
                        </div>
                        <div className="absolute top-4 right-4 bg-black/60 text-white text-xs px-2 py-1 rounded backdrop-blur-md pointer-events-none flex items-center gap-1">
                            <Move size={12} /> Drag to adjust
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-4 bg-slate-100 dark:bg-slate-800 p-3 rounded-xl">
                        <Minus size={18} className="text-slate-500 cursor-pointer hover:text-emerald-500" onClick={() => setZoom(z => Math.max(1, z - 0.1))} />
                        <input 
                            type="range" 
                            min="1" 
                            max="3" 
                            step="0.1" 
                            value={zoom}
                            onChange={(e) => setZoom(parseFloat(e.target.value))}
                            className="flex-1 h-2 bg-slate-300 dark:bg-slate-600 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                        />
                        <Plus size={18} className="text-slate-500 cursor-pointer hover:text-emerald-500" onClick={() => setZoom(z => Math.min(3, z + 0.1))} />
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                        <button 
                            type="button"
                            onClick={() => setShowPhotoModal(false)}
                            className="px-5 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                        >
                            Cancel
                        </button>
                        <button 
                            type="button"
                            onClick={() => setShowPhotoModal(false)}
                            className="px-8 py-2.5 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-500/20"
                        >
                            Apply
                        </button>
                    </div>
                </div>
            </Modal>
        </form>
    );
};
