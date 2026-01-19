import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Video, VideoOff, PhoneOff, MessageSquare, PenTool, Share, MoreVertical, Send, User } from 'lucide-react';
import { Session } from '../types';

interface ClassroomProps {
  session: Session;
  onLeave: () => void;
}

export const Classroom: React.FC<ClassroomProps> = ({ session, onLeave }) => {
  const [micOn, setMicOn] = useState(true);
  const [cameraOn, setCameraOn] = useState(true);
  const [messages, setMessages] = useState<{ sender: string, text: string, isMe: boolean }[]>([
    { sender: 'System', text: `Welcome to your session for ${session.subject}.`, isMe: false },
    { sender: session.tutorName, text: 'Hello! I am ready when you are.', isMe: false }
  ]);
  const [newMessage, setNewMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const sendMessage = () => {
    if (!newMessage.trim()) return;
    
    const userMsg = { sender: 'You', text: newMessage, isMe: true };
    setMessages(prev => [...prev, userMsg]);
    setNewMessage('');
    
    // Simulate typing and reply
    setIsTyping(true);
    setTimeout(() => {
        setIsTyping(false);
        const responses = [
            "That's a great question! Let's break it down.",
            "Exactly. Now, can you apply that to the next problem?",
            "Let me draw something on the whiteboard to explain.",
            "Could you clarify what you mean by that?",
            "Yes, you're on the right track!"
        ];
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        
        setMessages(prev => [...prev, { 
            sender: session.tutorName, 
            text: randomResponse, 
            isMe: false 
        }]);
    }, 1500 + Math.random() * 1000); // Random delay between 1.5s and 2.5s
  };

  return (
    <div className="flex h-[calc(100vh-64px)] bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 overflow-hidden transition-colors duration-200">
      {/* Main Content Area (Video + Whiteboard) */}
      <div className="flex-1 flex flex-col p-4 gap-4">
        
        {/* Video Strip */}
        <div className="flex gap-4 h-48">
          {/* Tutor Feed */}
          <div className="flex-1 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 relative overflow-hidden shadow-lg">
             <img src={`https://picsum.photos/seed/${session.tutorId}/800/600`} alt="Tutor" className="w-full h-full object-cover opacity-90" />
             <div className="absolute bottom-3 left-3 bg-white/60 dark:bg-slate-950/60 px-3 py-1 rounded-full text-sm font-medium backdrop-blur-sm text-slate-900 dark:text-white flex items-center gap-2">
               <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
               {session.tutorName} (Tutor)
             </div>
          </div>

          {/* Student Feed (Self) */}
          <div className="flex-1 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 relative overflow-hidden shadow-lg group">
             {cameraOn ? (
               <img src="https://picsum.photos/seed/me/800/600" alt="Me" className="w-full h-full object-cover" />
             ) : (
               <div className="w-full h-full flex items-center justify-center bg-slate-100 dark:bg-slate-800">
                 <div className="w-20 h-20 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-2xl font-bold text-slate-500 dark:text-slate-400">ME</div>
               </div>
             )}
             <div className="absolute bottom-3 left-3 bg-white/60 dark:bg-slate-950/60 px-3 py-1 rounded-full text-sm font-medium backdrop-blur-sm text-slate-900 dark:text-white">
               You
             </div>
             <div className="absolute bottom-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => setMicOn(!micOn)} className={`p-2 rounded-full ${micOn ? 'bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-900 dark:text-white' : 'bg-red-500 hover:bg-red-600 text-white'}`}>
                    {micOn ? <Mic size={16} /> : <MicOff size={16} />}
                </button>
             </div>
          </div>
        </div>

        {/* Interactive Whiteboard Placeholder */}
        <div className="flex-1 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 relative overflow-hidden p-6 shadow-inner">
            <div className="absolute top-4 left-4 flex gap-2 bg-slate-100 dark:bg-slate-800 p-2 rounded-lg border border-slate-200 dark:border-slate-700 z-10">
                <button className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-emerald-600 dark:text-emerald-400"><PenTool size={20} /></button>
                <button className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-400"><Share size={20} /></button>
                <button className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-400"><MoreVertical size={20} /></button>
            </div>
            <div className="w-full h-full flex items-center justify-center text-slate-400 dark:text-slate-500 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-lg bg-grid-slate-100 dark:bg-grid-slate-900/[0.05]">
                <div className="text-center">
                    <p className="text-lg font-medium text-slate-600 dark:text-slate-400">Interactive Whiteboard</p>
                    <p className="text-sm">Collaboration space active</p>
                </div>
            </div>
        </div>

        {/* Controls Bar */}
        <div className="h-16 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center justify-center gap-6 px-8 shadow-lg">
            <button 
                onClick={() => setMicOn(!micOn)}
                className={`p-4 rounded-full transition-all ${micOn ? 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700' : 'bg-red-500/10 text-red-500 border border-red-500/50'}`}
            >
                {micOn ? <Mic size={24} /> : <MicOff size={24} />}
            </button>
            <button 
                onClick={() => setCameraOn(!cameraOn)}
                className={`p-4 rounded-full transition-all ${cameraOn ? 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700' : 'bg-red-500/10 text-red-500 border border-red-500/50'}`}
            >
                {cameraOn ? <Video size={24} /> : <VideoOff size={24} />}
            </button>
            <button 
                onClick={onLeave}
                className="px-8 py-3 bg-red-600 hover:bg-red-700 text-white rounded-full font-semibold flex items-center gap-2 transition-colors ml-4 shadow-lg shadow-red-500/20"
            >
                <PhoneOff size={20} />
                End Session
            </button>
        </div>
      </div>

      {/* Sidebar Chat */}
      <div className="w-80 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 flex flex-col shadow-xl">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-white dark:bg-slate-900 z-10">
            <h3 className="font-semibold flex items-center gap-2 text-slate-900 dark:text-white"><MessageSquare size={18} className="text-emerald-500"/> Session Chat</h3>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-950/50">
            {messages.map((msg, i) => (
                <div key={i} className={`flex flex-col ${msg.isMe ? 'items-end' : 'items-start'} animate-in slide-in-from-bottom-2 duration-300`}>
                    <span className="text-[10px] text-slate-400 mb-1 px-1 flex items-center gap-1">
                        {!msg.isMe && <User size={10} />}
                        {msg.sender}
                    </span>
                    <div className={`p-3 rounded-2xl max-w-[85%] text-sm shadow-sm ${
                        msg.isMe 
                            ? 'bg-emerald-600 text-white rounded-br-sm' 
                            : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-bl-sm'
                    }`}>
                        {msg.text}
                    </div>
                </div>
            ))}
            
            {/* Typing Indicator */}
            {isTyping && (
                <div className="flex flex-col items-start animate-in fade-in duration-200">
                    <span className="text-[10px] text-slate-400 mb-1 px-1 ml-1">{session.tutorName} is typing...</span>
                    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-3 rounded-2xl rounded-bl-sm shadow-sm flex gap-1.5 items-center h-[44px]">
                        <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                        <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                        <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
                    </div>
                </div>
            )}
            
            <div ref={chatEndRef} />
        </div>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
            <div className="relative">
                <input 
                    type="text" 
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Type a message..."
                    className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full py-3 pl-4 pr-12 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 transition-all"
                />
                <button 
                    onClick={sendMessage} 
                    disabled={!newMessage.trim()}
                    className="absolute right-1.5 top-1.5 p-1.5 bg-emerald-600 rounded-full text-white hover:bg-emerald-500 disabled:opacity-50 disabled:hover:bg-emerald-600 transition-colors"
                >
                    <Send size={16} />
                </button>
            </div>
        </div>
      </div>
    </div>
  );
};