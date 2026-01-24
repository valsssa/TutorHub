"use client";

import { useCallback, useEffect, useState, useRef, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import {
  FiMessageSquare,
  FiUser,
  FiSearch,
  FiX,
  FiChevronLeft,
  FiSend,
  FiCheck,
} from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import { messages, auth } from "@/lib/api";
import { MessageThread, User, Message } from "@/types";
import { useToast } from "@/components/ToastContainer";
import LoadingSpinner from "@/components/LoadingSpinner";
import { useMessaging } from "@/hooks/useMessaging";
import { useWebSocket } from "@/hooks/useWebSocket";
import Input from "@/components/Input";

export default function MessagesPage() {
  return (
    <ProtectedRoute>
      <MessagesContent />
    </ProtectedRoute>
  );
}

function MessagesContent() {
  const searchParams = useSearchParams();
  const { showError, showSuccess } = useToast();
  const { isConnected } = useWebSocket();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [threads, setThreads] = useState<MessageThread[]>([]);
  const [filteredThreads, setFilteredThreads] = useState<MessageThread[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedThread, setSelectedThread] = useState<MessageThread | null>(null);
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [newMessage, setNewMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [showNewMessagePill, setShowNewMessagePill] = useState(false);
  const [lastReadByThread, setLastReadByThread] = useState<Record<number, number | null>>({});
  const [recentMessageIds, setRecentMessageIds] = useState<number[]>([]);
  const messageTimeoutsRef = useRef<Record<number, ReturnType<typeof setTimeout>>>({});
  const prevMessageIdsRef = useRef<Record<number, number[]>>({});

  const getThreadDisplayName = (thread: MessageThread): string => {
    if (thread.other_user_first_name && thread.other_user_last_name) {
      return `${thread.other_user_first_name} ${thread.other_user_last_name}`;
    }
    return thread.other_user_email;
  };

  const {
    messages: threadMessages,
    setMessages,
    clearMessages,
    typingUsers,
    handleTyping,
  } = useMessaging({
    currentUserId: currentUser?.id || null,
    selectedThreadId: selectedThread?.other_user_id,
  });

  // Sort messages chronologically
  const orderedMessages = useMemo<Message[]>(() => {
    if (!threadMessages) return [];
    return [...threadMessages].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
  }, [threadMessages]);

  const loadThreads = useCallback(async () => {
    try {
      const threadList = await messages.listThreads();
      setThreads(threadList);
      setFilteredThreads(threadList);
    } catch (error) {
      showError("Failed to load message threads");
    }
  }, [showError]);

  const loadData = useCallback(async () => {
    try {
      const user = await auth.getCurrentUser();
      setCurrentUser(user);
      await loadThreads();
    } catch (error) {
      showError("Failed to load messages");
    } finally {
      setLoading(false);
    }
  }, [loadThreads, showError]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Filter threads based on search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredThreads(threads);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = threads.filter(
      (thread) =>
        thread.other_user_email.toLowerCase().includes(query) ||
        thread.last_message.toLowerCase().includes(query)
    );
    setFilteredThreads(filtered);
  }, [searchQuery, threads]);

  const selectThread = useCallback(
    async (thread: MessageThread) => {
      setSelectedThread(thread);
      clearMessages();

      try {
        const msgs = await messages.getThreadMessages(
          thread.other_user_id,
          thread.booking_id
        );
        setMessages(msgs);

        // Mark thread as read
        if (thread.unread_count > 0) {
          await messages.markThreadRead(
            thread.other_user_id,
            thread.booking_id
          );
          setThreads((prevThreads) =>
            prevThreads.map((t) =>
              t.other_user_id === thread.other_user_id &&
              t.booking_id === thread.booking_id
                ? { ...t, unread_count: 0 }
                : t
            )
          );
          setFilteredThreads((prevThreads) =>
            prevThreads.map((t) =>
              t.other_user_id === thread.other_user_id &&
              t.booking_id === thread.booking_id
                ? { ...t, unread_count: 0 }
                : t
            )
          );
        }
      } catch (error) {
        showError("Failed to load conversation");
      }
    },
    [showError, setMessages, clearMessages]
  );

  // Handle user parameter from URL for starting new conversation
  useEffect(() => {
    const userParam = searchParams?.get("user");
    const targetUserId = userParam ? parseInt(userParam) : null;

    if (targetUserId && currentUser && threads.length >= 0) {
      // Check if we already have a thread with this user
      const existingThread = threads.find((t) => t.other_user_id === targetUserId);

      if (existingThread) {
        // Select existing thread
        selectThread(existingThread);
      } else {
        // Create a new thread with this user (works for all roles: tutor, student, admin)
        const tempThread: MessageThread = {
          other_user_id: targetUserId,
          other_user_email: `User #${targetUserId}`,
          other_user_role: "student", // Will be updated when first message is sent/received
          booking_id: undefined,
          last_message: "Start a new conversation",
          last_message_time: new Date().toISOString(),
          total_messages: 0,
          unread_count: 0,
        };
        setSelectedThread(tempThread);
        setMessages([]);
      }
    }
  }, [searchParams, currentUser, threads, selectThread, setMessages]);

  const sendMessage = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const messageText = newMessage.trim();
      if (!messageText || !selectedThread || !currentUser) return;

      setSendingMessage(true);
      try {
        const sentMessage = await messages.send(
          selectedThread.other_user_id,
          messageText,
          selectedThread.booking_id || undefined
        );

        setMessages((prevMessages) => [...prevMessages, sentMessage]);
        setNewMessage("");

        // Check if this was a new thread
        const existingThread = threads.find(
          (t) =>
            t.other_user_id === selectedThread.other_user_id &&
            t.booking_id === selectedThread.booking_id
        );

        if (!existingThread) {
          // Reload threads to get the new thread
          await loadThreads();
        } else {
          // Update existing thread
          setThreads((prevThreads) =>
            prevThreads.map((t) =>
              t.other_user_id === selectedThread.other_user_id &&
              t.booking_id === selectedThread.booking_id
                ? {
                    ...t,
                    last_message: messageText,
                    last_message_time: sentMessage.created_at,
                    last_sender_id: currentUser.id,
                    total_messages: (t.total_messages || 0) + 1,
                  }
                : t
            )
          );
        }

        showSuccess("Message sent!");
      } catch (error) {
        showError("Failed to send message");
      } finally {
        setSendingMessage(false);
      }
    },
    [currentUser, selectedThread, threads, loadThreads, showError, showSuccess, setMessages, newMessage]
  );

  // Scroll to bottom helper
  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior, block: 'end' });
  }, []);

  // Update read state
  const updateReadState = useCallback((thread: MessageThread | undefined, msgs: Message[]) => {
    if (!thread || msgs.length === 0) return;
    const lastMessageId = msgs[msgs.length - 1]?.id;
    if (!lastMessageId) return;
    setLastReadByThread(prev => {
      if (prev[thread.other_user_id] === lastMessageId) return prev;
      return { ...prev, [thread.other_user_id]: lastMessageId };
    });
  }, []);

  // Handle jump to latest messages
  const handleJumpToLatest = useCallback(() => {
    if (!selectedThread) return;
    scrollToBottom('smooth');
    setShowNewMessagePill(false);
    updateReadState(selectedThread, orderedMessages);
  }, [selectedThread, orderedMessages, scrollToBottom, updateReadState]);

  // Calculate seen message IDs (messages that have been seen by other user)
  const seenMessageIds = useMemo(() => {
    if (!selectedThread || orderedMessages.length === 0) return new Set<number>();
    let otherAfter = false;
    const seen = new Set<number>();
    for (let i = orderedMessages.length - 1; i >= 0; i -= 1) {
      const msg = orderedMessages[i];
      if (msg.sender_id !== currentUser?.id) {
        otherAfter = true;
        continue;
      }
      if (otherAfter) {
        seen.add(msg.id);
      }
    }
    return seen;
  }, [selectedThread, currentUser?.id, orderedMessages]);

  // Calculate unread start index
  const unreadStartIndex = useMemo(() => {
    if (!selectedThread || orderedMessages.length === 0) return -1;
    const lastReadId = lastReadByThread[selectedThread.other_user_id] || null;
    if (!lastReadId) return -1;
    const lastReadIndex = orderedMessages.findIndex(message => message.id === lastReadId);
    if (lastReadIndex < 0 || lastReadIndex >= orderedMessages.length - 1) return -1;
    return lastReadIndex + 1;
  }, [selectedThread, lastReadByThread, orderedMessages]);

  // Scroll monitoring
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container || !selectedThread) return;

    const handleScroll = () => {
      const distance = container.scrollHeight - container.scrollTop - container.clientHeight;
      const atBottom = distance < 80;
      setIsAtBottom(atBottom);

      if (atBottom) {
        setShowNewMessagePill(false);
        updateReadState(selectedThread, orderedMessages);
      }
    };

    handleScroll();
    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, [selectedThread, orderedMessages, updateReadState]);

  // Auto-scroll on new messages
  useEffect(() => {
    if (!selectedThread) return;
    const lastMessage = orderedMessages[orderedMessages.length - 1];
    if (!lastMessage) return;

    if (isAtBottom) {
      scrollToBottom('smooth');
      updateReadState(selectedThread, orderedMessages);
      setShowNewMessagePill(false);
      return;
    }

    if (lastMessage.sender_id !== currentUser?.id) {
      setShowNewMessagePill(true);
    }
  }, [orderedMessages.length, selectedThread, currentUser?.id, isAtBottom, scrollToBottom, updateReadState, orderedMessages]);

  // Track new messages with animation
  useEffect(() => {
    if (!selectedThread) return;
    const previousIds = prevMessageIdsRef.current[selectedThread.other_user_id];
    const currentIds = orderedMessages.map(message => message.id);
    if (!previousIds) {
      prevMessageIdsRef.current[selectedThread.other_user_id] = currentIds;
      return;
    }
    const newIds = currentIds.filter(id => !previousIds.includes(id));
    if (newIds.length > 0) {
      setRecentMessageIds(prev => Array.from(new Set([...prev, ...newIds])));
      newIds.forEach(id => {
        if (messageTimeoutsRef.current[id]) {
          clearTimeout(messageTimeoutsRef.current[id]);
        }
        messageTimeoutsRef.current[id] = setTimeout(() => {
          setRecentMessageIds(prev => prev.filter(prevId => prevId !== id));
          delete messageTimeoutsRef.current[id];
        }, 180);
      });
    }
    prevMessageIdsRef.current[selectedThread.other_user_id] = currentIds;
  }, [selectedThread, orderedMessages]);

  // Cleanup timeouts
  useEffect(() => {
    return () => {
      Object.values(messageTimeoutsRef.current).forEach(clearTimeout);
    };
  }, []);

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  const getTotalUnread = () => {
    return threads.reduce((sum, thread) => sum + thread.unread_count, 0);
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case "tutor":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300";
      case "student":
        return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300";
      case "admin":
        return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300";
    }
  };

  if (loading || !currentUser) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div 
        className="absolute inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm transition-opacity" 
        onClick={() => window.history.back()}
      />
      
      <div className="relative w-full md:w-[800px] h-full bg-white dark:bg-slate-900 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        {/* Connection status banner */}
        {!isConnected && (
          <div className="bg-yellow-100 dark:bg-yellow-900/30 border-b border-yellow-200 dark:border-yellow-800 px-4 py-2 text-sm text-yellow-800 dark:text-yellow-300 flex items-center justify-center">
            Reconnecting to chat server...
          </div>
        )}

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar (List of threads) */}
          <div className={`${selectedThread ? 'hidden md:flex' : 'flex'} w-full md:w-1/3 flex-col border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50`}>
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
                <FiMessageSquare className="w-5 h-5 text-emerald-500" /> Messages
              </h2>
              <button 
                onClick={() => window.history.back()} 
                className="md:hidden text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              >
                <FiX size={24} />
              </button>
            </div>
            
            <div className="p-4">
              <div className="relative">
                <FiSearch className="absolute left-3 top-3 text-slate-400" size={16} />
                <input 
                  type="text" 
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:border-emerald-500 transition-colors text-slate-900 dark:text-white"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto">
              {filteredThreads.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-sm">
                  {searchQuery ? "No conversations found" : "No messages yet"}
                </div>
              ) : (
                filteredThreads.map(thread => {
                  const isActive = selectedThread?.other_user_id === thread.other_user_id &&
                                  selectedThread?.booking_id === thread.booking_id;
                  const isUnread = thread.unread_count > 0;
                  return (
                    <button
                      key={`${thread.other_user_id}-${thread.booking_id || "general"}`}
                      onClick={() => selectThread(thread)}
                      className={`w-full p-4 flex items-start gap-3 text-left border-b border-slate-100 dark:border-slate-800/50 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800 ${
                        isActive
                          ? 'bg-emerald-50 dark:bg-emerald-900/10'
                          : isUnread
                            ? 'bg-emerald-50/60 dark:bg-emerald-900/5'
                            : ''
                      }`}
                    >
                      <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center flex-shrink-0">
                        <FiUser className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-baseline mb-1">
                          <h4 className={`text-sm truncate ${
                            isActive
                              ? 'font-semibold text-emerald-700 dark:text-emerald-400'
                              : isUnread
                                ? 'font-semibold text-slate-900 dark:text-white'
                                : 'font-medium text-slate-800 dark:text-slate-100'
                          }`}>
                            {getThreadDisplayName(thread)}
                          </h4>
                          <span className="text-[10px] text-slate-400">
                            {formatTime(thread.last_message_time)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mb-1">
                          {thread.other_user_role && (
                            <span className={`text-xs px-2 py-0.5 rounded ${getRoleBadgeColor(thread.other_user_role)}`}>
                              {thread.other_user_role}
                            </span>
                          )}
                          {isUnread && (
                            <span className="bg-emerald-600 text-white text-xs px-2 py-0.5 rounded-full font-medium">
                              {thread.unread_count}
                            </span>
                          )}
                        </div>
                        <p className={`text-xs leading-snug line-clamp-2 ${
                          isUnread
                            ? 'font-semibold text-slate-700 dark:text-slate-200'
                            : 'text-slate-500'
                        }`}>
                          {thread.last_sender_id === currentUser.id && "You: "}
                          {thread.last_message || 'No messages yet.'}
                        </p>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Chat Area */}
          <div className={`${!selectedThread ? 'hidden md:flex' : 'flex'} w-full md:w-2/3 flex-col bg-white dark:bg-slate-900`}>
            {selectedThread ? (
              <>
                <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <button 
                      onClick={() => setSelectedThread(null)} 
                      className="md:hidden text-slate-500"
                    >
                      <FiChevronLeft size={24} />
                    </button>
                    <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center">
                      <FiUser className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 dark:text-white">
                        {getThreadDisplayName(selectedThread)}
                      </h3>
                      <div className="flex items-center gap-2">
                        {selectedThread.other_user_role && (
                          <span className={`text-xs px-2 py-0.5 rounded ${getRoleBadgeColor(selectedThread.other_user_role)}`}>
                            {selectedThread.other_user_role}
                          </span>
                        )}
                        {isConnected && (
                          <span className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span> Online
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <button 
                    onClick={() => window.history.back()} 
                    className="hidden md:block text-slate-400 hover:text-slate-600 dark:hover:text-white"
                  >
                    <FiX size={24} />
                  </button>
                </div>

                <div className="relative flex-1 bg-slate-50 dark:bg-slate-950/30">
                  <div ref={messagesContainerRef} className="h-full overflow-y-auto p-4 space-y-4">
                    {orderedMessages.map((msg, index) => {
                      const isMe = msg.sender_id === currentUser.id;
                      const isRecentMessage = recentMessageIds.includes(msg.id);
                      const showDivider = unreadStartIndex === index;
                      const isSeen = isMe && seenMessageIds.has(msg.id);

                      return (
                        <div key={msg.id}>
                          {showDivider && (
                            <div className="flex items-center gap-3 py-1">
                              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800"></div>
                              <span className="text-[10px] uppercase tracking-wide text-emerald-600/70 dark:text-emerald-400/70">New messages</span>
                              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800"></div>
                            </div>
                          )}
                          <div className={`group flex ${isMe ? 'justify-end' : 'justify-start'} ${isRecentMessage ? 'animate-in slide-in-from-bottom-1 duration-150 ease-out' : ''}`}>
                            <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm ${
                              isMe
                                ? 'bg-emerald-600 text-white rounded-br-sm'
                                : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-bl-sm'
                            }`}>
                              <p className="leading-relaxed">{msg.message}</p>
                              <div className={`mt-1 flex items-center gap-1 text-[10px] transition-opacity opacity-0 group-hover:opacity-100 ${
                                isMe ? 'justify-end text-emerald-100' : 'justify-start text-slate-400'
                              }`}>
                                <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                {isMe && (
                                  <span className="flex items-center gap-1">
                                    <FiCheck size={12} className="opacity-80" />
                                    {isSeen && <FiCheck size={12} className="opacity-80 -ml-2" />}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    <div ref={messagesEndRef} />
                  </div>

                  {showNewMessagePill && (
                    <button
                      type="button"
                      onClick={handleJumpToLatest}
                      className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-white/90 dark:bg-slate-900/90 px-4 py-2 text-xs font-medium text-slate-700 dark:text-slate-200 shadow-md border border-slate-200 dark:border-slate-800 backdrop-blur-sm transition-colors hover:bg-white"
                    >
                      New messages ↓
                    </button>
                  )}
                </div>

                {/* Typing indicator */}
                {typingUsers.size > 0 && (
                  <div className="px-4 py-2 opacity-100 max-h-10">
                    <div className="inline-flex items-center gap-1 rounded-full bg-slate-100 dark:bg-slate-800 px-3 py-1">
                      <span className="typing-dot"></span>
                      <span className="typing-dot"></span>
                      <span className="typing-dot"></span>
                    </div>
                  </div>
                )}

                <div className="p-4 border-t border-slate-200 dark:border-slate-800">
                  <form onSubmit={sendMessage} className="flex gap-2">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyDown={() => handleTyping()}
                      placeholder="Type a message..."
                      className="flex-1 bg-slate-100 dark:bg-slate-800 border-none rounded-full px-4 py-3 text-sm focus:ring-1 focus:ring-emerald-500 text-slate-900 dark:text-white placeholder-slate-400"
                    />
                    <button 
                      type="submit"
                      disabled={!newMessage.trim() || sendingMessage}
                      className="p-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-full disabled:opacity-50 transition-colors"
                    >
                      <FiSend size={18} />
                    </button>
                  </form>
                </div>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-8">
                <div className="w-20 h-20 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                  <FiMessageSquare size={40} className="text-slate-300 dark:text-slate-600" />
                </div>
                <p className="text-lg font-medium text-slate-600 dark:text-slate-300">Your Messages</p>
                <p className="text-sm">Select a conversation to start chatting.</p>
                <button 
                  onClick={() => window.history.back()} 
                  className="md:hidden mt-8 text-emerald-600 font-medium"
                >
                  Close
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
