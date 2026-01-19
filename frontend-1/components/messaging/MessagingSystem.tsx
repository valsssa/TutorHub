
import React, { useState, useEffect, useRef } from 'react';
import { Send, X, MessageSquare, Search, ChevronLeft } from 'lucide-react';
import { ChatThread, ChatMessage, User } from '../../domain/types';

interface MessagingSystemProps {
    currentUser: User;
    threads: ChatThread[];
    activeThreadId: string | null;
    isOpen: boolean;
    onClose: () => void;
    onSelectThread: (threadId: string) => void;
    onSendMessage: (threadId: string, text: string) => void;
}

export const MessagingSystem: React.FC<MessagingSystemProps> = ({ 
    currentUser, threads, activeThreadId, isOpen, onClose, onSelectThread, onSendMessage 
}) => {
    const [newMessage, setNewMessage] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const activeThread = threads.find(t => t.id === activeThreadId);
    
    // Sort threads by date
    const sortedThreads = [...threads].sort((a, b) => 
        new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime()
    );

    const filteredThreads = sortedThreads.filter(t => 
        t.participantName.toLowerCase().includes(searchTerm.toLowerCase())
    );

    useEffect(() => {
        if (activeThread && isOpen) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [activeThread, activeThread?.messages.length, isOpen]);

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault();
        if (!newMessage.trim() || !activeThreadId) return;
        onSendMessage(activeThreadId, newMessage);
        setNewMessage('');
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex justify-end">
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity" onClick={onClose} />
            
            <div className="relative w-full md:w-[800px] h-full bg-white dark:bg-slate-900 shadow-2xl flex animate-in slide-in-from-right duration-300">
                {/* Sidebar (List of threads) */}
                <div className={`${activeThread ? 'hidden md:flex' : 'flex'} w-full md:w-1/3 flex-col border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50`}>
                    <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                        <h2 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
                            <MessageSquare size={20} className="text-emerald-500" /> Messages
                        </h2>
                        <button onClick={onClose} className="md:hidden text-slate-500 hover:text-slate-800">
                            <X size={24} />
                        </button>
                    </div>
                    
                    <div className="p-4">
                        <div className="relative">
                            <Search size={16} className="absolute left-3 top-3 text-slate-400" />
                            <input 
                                type="text" 
                                placeholder="Search conversations..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:border-emerald-500 transition-colors"
                            />
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        {filteredThreads.length === 0 ? (
                            <div className="p-8 text-center text-slate-500 text-sm">
                                No conversations found.
                            </div>
                        ) : (
                            filteredThreads.map(thread => (
                                <button
                                    key={thread.id}
                                    onClick={() => onSelectThread(thread.id)}
                                    className={`w-full p-4 flex items-start gap-3 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left border-b border-slate-100 dark:border-slate-800/50 ${activeThreadId === thread.id ? 'bg-emerald-50 dark:bg-emerald-900/10' : ''}`}
                                >
                                    <img src={thread.participantAvatar} alt={thread.participantName} className="w-10 h-10 rounded-full object-cover" />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex justify-between items-baseline mb-1">
                                            <h4 className={`font-semibold text-sm truncate ${activeThreadId === thread.id ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-900 dark:text-white'}`}>
                                                {thread.participantName}
                                            </h4>
                                            <span className="text-[10px] text-slate-400">
                                                {new Date(thread.lastUpdated).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                            </span>
                                        </div>
                                        <p className={`text-xs truncate ${thread.unreadCount > 0 ? 'font-bold text-slate-800 dark:text-slate-200' : 'text-slate-500'}`}>
                                            {thread.unreadCount > 0 && <span className="inline-block w-2 h-2 bg-emerald-500 rounded-full mr-1.5 align-middle"></span>}
                                            {thread.lastMessage}
                                        </p>
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </div>

                {/* Chat Area */}
                <div className={`${!activeThread ? 'hidden md:flex' : 'flex'} w-full md:w-2/3 flex-col bg-white dark:bg-slate-900`}>
                    {activeThread ? (
                        <>
                            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <button onClick={() => onSelectThread('')} className="md:hidden text-slate-500">
                                        <ChevronLeft size={24} />
                                    </button>
                                    <img src={activeThread.participantAvatar} alt={activeThread.participantName} className="w-10 h-10 rounded-full object-cover" />
                                    <div>
                                        <h3 className="font-bold text-slate-900 dark:text-white">{activeThread.participantName}</h3>
                                        <span className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                                            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span> Online
                                        </span>
                                    </div>
                                </div>
                                <button onClick={onClose} className="hidden md:block text-slate-400 hover:text-slate-600 dark:hover:text-white">
                                    <X size={24} />
                                </button>
                            </div>

                            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-950/30">
                                {activeThread.messages.map(msg => {
                                    const isMe = msg.senderId === currentUser.id;
                                    return (
                                        <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                                            <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm ${
                                                isMe 
                                                ? 'bg-emerald-600 text-white rounded-br-sm' 
                                                : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-bl-sm'
                                            }`}>
                                                <p>{msg.text}</p>
                                                <p className={`text-[10px] mt-1 text-right ${isMe ? 'text-emerald-200' : 'text-slate-400'}`}>
                                                    {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                                </p>
                                            </div>
                                        </div>
                                    );
                                })}
                                <div ref={messagesEndRef} />
                            </div>

                            <div className="p-4 border-t border-slate-200 dark:border-slate-800">
                                <form onSubmit={handleSend} className="flex gap-2">
                                    <input 
                                        type="text" 
                                        value={newMessage}
                                        onChange={(e) => setNewMessage(e.target.value)}
                                        placeholder="Type a message..."
                                        className="flex-1 bg-slate-100 dark:bg-slate-800 border-none rounded-full px-4 py-3 text-sm focus:ring-1 focus:ring-emerald-500 text-slate-900 dark:text-white placeholder-slate-400"
                                    />
                                    <button 
                                        type="submit"
                                        disabled={!newMessage.trim()}
                                        className="p-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-full disabled:opacity-50 transition-colors"
                                    >
                                        <Send size={18} />
                                    </button>
                                </form>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-8">
                            <div className="w-20 h-20 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                                <MessageSquare size={40} className="text-slate-300 dark:text-slate-600" />
                            </div>
                            <p className="text-lg font-medium text-slate-600 dark:text-slate-300">Your Messages</p>
                            <p className="text-sm">Select a conversation to start chatting.</p>
                            <button onClick={onClose} className="md:hidden mt-8 text-emerald-600 font-medium">Close</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
