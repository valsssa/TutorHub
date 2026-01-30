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
import Avatar from "@/components/Avatar";
import { MessageThread, User, Message } from "@/types";
import { useToast } from "@/components/ToastContainer";
import LoadingSpinner from "@/components/LoadingSpinner";
import { useMessaging } from "@/hooks/useMessaging";
import { useWebSocket } from "@/hooks/useWebSocket";
import Input from "@/components/Input";
import { createLogger } from "@/lib/logger";

const logger = createLogger('Messages');

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
  const [messageError, setMessageError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messageInputRef = useRef<HTMLTextAreaElement>(null);
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
        // Fetch user information and create a new thread
        const fetchUserAndCreateThread = async () => {
          try {
            const userInfo = await messages.getUserBasicInfo(targetUserId);
            const tempThread: MessageThread = {
              other_user_id: targetUserId,
              other_user_email: userInfo.email,
              other_user_first_name: userInfo.first_name || null,
              other_user_last_name: userInfo.last_name || null,
              other_user_avatar_url: userInfo.avatar_url || null,
              other_user_role: userInfo.role,
              booking_id: undefined,
              last_message: "Start a new conversation",
              last_message_time: new Date().toISOString(),
              total_messages: 0,
              unread_count: 0,
            };
            setSelectedThread(tempThread);
            setMessages([]);
          } catch (error) {
            showError("Failed to load user information");
            logger.error("Error fetching user info", error);
          }
        };
        fetchUserAndCreateThread();
      }
    }
  }, [searchParams, currentUser, threads, selectThread, setMessages, showError]);

  const sendMessage = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const messageText = newMessage.trim();
      if (!messageText || !selectedThread || !currentUser) return;

      // Validate message before sending
      const validationError = validateMessage(newMessage);
      if (validationError) {
        setMessageError(validationError);
        return;
      }

      // Additional validation: min length
      if (messageText.length < MESSAGE_MIN_LENGTH) {
        setMessageError(`Message must be at least ${MESSAGE_MIN_LENGTH} character`);
        return;
      }

      setSendingMessage(true);
      setMessageError(null);
      try {
        const sentMessage = await messages.send(
          selectedThread.other_user_id,
          messageText,
          selectedThread.booking_id || undefined
        );

        setMessages((prevMessages) => [...prevMessages, sentMessage]);
        setNewMessage("");
        setMessageError(null);
        // Reset textarea height
        if (messageInputRef.current) {
          messageInputRef.current.style.height = 'auto';
        }

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
    const timeouts = messageTimeoutsRef.current;
    return () => {
      Object.values(timeouts).forEach(clearTimeout);
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

  // Message validation following textarea rules
  const MESSAGE_MAX_LENGTH = 2000;
  const MESSAGE_MIN_LENGTH = 1;
  const MESSAGE_WARNING_THRESHOLD = 0.8; // 80%

  const validateMessage = (text: string): string | null => {
    const trimmed = text.trim();
    
    // Min length check
    if (trimmed.length < MESSAGE_MIN_LENGTH) {
      return null; // Empty is allowed (just can't send)
    }

    // Max length check
    if (text.length > MESSAGE_MAX_LENGTH) {
      return `Message must not exceed ${MESSAGE_MAX_LENGTH} characters`;
    }

    // No ALL CAPS messages over 10 characters
    if (trimmed.length > 10 && trimmed === trimmed.toUpperCase() && /[A-Z]/.test(trimmed)) {
      return "Please avoid typing in all capital letters";
    }

    // No repeated characters (more than 5 of same char in a row)
    if (/(.)\1{5,}/.test(trimmed)) {
      return "Please avoid excessive repeated characters";
    }

    return null;
  };

  // Auto-resize textarea
  const adjustTextareaHeight = useCallback(() => {
    const textarea = messageInputRef.current;
    if (!textarea) return;

    // Reset height to get correct scrollHeight
    textarea.style.height = 'auto';
    
    // Calculate min and max heights (3-10 lines)
    const lineHeight = 24; // Approximate line height
    const padding = 20; // py-2.5 = 10px top + 10px bottom
    const minHeight = (lineHeight * 3) + padding;
    const maxHeight = (lineHeight * 10) + padding;
    
    const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);
    textarea.style.height = `${newHeight}px`;
  }, []);

  // Handle message input change
  const handleMessageChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    
    // Enforce maxLength
    if (value.length > MESSAGE_MAX_LENGTH) {
      return;
    }

    setNewMessage(value);
    setMessageError(validateMessage(value));
    adjustTextareaHeight();
    handleTyping();
  };

  // Adjust height when message changes
  useEffect(() => {
    adjustTextareaHeight();
  }, [newMessage, adjustTextareaHeight]);

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
      
      {/* Mobile: Full width, Tablet: 90% max-width, Desktop: Fixed 900px */}
      <div className="relative w-full sm:w-[90%] md:w-[800px] lg:w-[900px] xl:w-[1000px] h-full bg-white dark:bg-slate-900 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        {/* Connection status banner */}
        {!isConnected && (
          <div className="bg-yellow-100 dark:bg-yellow-900/30 border-b border-yellow-200 dark:border-yellow-800 px-3 sm:px-4 py-2 text-xs sm:text-sm text-yellow-800 dark:text-yellow-300 flex items-center justify-center">
            Reconnecting to chat server...
          </div>
        )}

        <div className="flex flex-1 overflow-hidden min-h-0">
          {/* Sidebar (List of threads) */}
          {/* Mobile: Full width when no thread selected, hidden when thread selected */}
          {/* Tablet: 40% width, always visible */}
          {/* Desktop: 35% width, always visible */}
          <div className={`${
            selectedThread 
              ? 'hidden sm:flex' 
              : 'flex'
          } w-full sm:w-[40%] lg:w-[35%] flex-col border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 min-h-0`}>
            <div className="flex-shrink-0 p-3 sm:p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white flex items-center gap-2">
                <FiMessageSquare className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-500" /> 
                <span className="hidden xs:inline">Messages</span>
              </h2>
              <button 
                onClick={() => window.history.back()} 
                className="sm:hidden p-2 -mr-2 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 active:scale-95 transition-transform touch-manipulation"
                aria-label="Close messages"
              >
                <FiX size={20} />
              </button>
            </div>
            
            <div className="flex-shrink-0 p-3 sm:p-4">
              <div className="relative">
                <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                <input 
                  type="text" 
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 sm:py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all text-slate-900 dark:text-white placeholder:text-slate-400"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto overscroll-contain min-h-0">
              {filteredThreads.length === 0 ? (
                <div className="p-6 sm:p-8 flex flex-col items-center justify-center text-center">
                  {searchQuery ? (
                    <>
                      <div className="w-14 h-14 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                        <FiSearch className="w-6 h-6 text-slate-400" />
                      </div>
                      <p className="font-medium text-slate-700 dark:text-slate-300 mb-1">No conversations found</p>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">Try a different search term</p>
                      <button
                        onClick={() => setSearchQuery("")}
                        className="text-sm font-medium text-emerald-600 hover:text-emerald-500 dark:text-emerald-400"
                      >
                        Clear search
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="w-14 h-14 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mb-4">
                        <FiMessageSquare className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                      </div>
                      <p className="font-medium text-slate-700 dark:text-slate-300 mb-1">No messages yet</p>
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        Start a conversation with a tutor or student
                      </p>
                    </>
                  )}
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
                      className={`w-full p-3 sm:p-4 flex items-start gap-2 sm:gap-3 text-left border-b border-slate-100 dark:border-slate-800/50 transition-colors active:bg-slate-100 dark:active:bg-slate-800 touch-manipulation min-h-[72px] sm:min-h-[80px] ${
                        isActive
                          ? 'bg-emerald-50 dark:bg-emerald-900/10'
                          : isUnread
                            ? 'bg-emerald-50/60 dark:bg-emerald-900/5'
                            : 'hover:bg-slate-100 dark:hover:bg-slate-800'
                      }`}
                    >
                      <Avatar
                        name={getThreadDisplayName(thread)}
                        avatarUrl={thread.other_user_avatar_url}
                        variant="gradient"
                        size="sm"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-baseline mb-1 gap-2">
                          <h4 className={`text-sm sm:text-base truncate ${
                            isActive
                              ? 'font-semibold text-emerald-700 dark:text-emerald-400'
                              : isUnread
                                ? 'font-semibold text-slate-900 dark:text-white'
                                : 'font-medium text-slate-800 dark:text-slate-100'
                          }`}>
                            {getThreadDisplayName(thread)}
                          </h4>
                          <span className="text-[10px] sm:text-xs text-slate-400 flex-shrink-0">
                            {formatTime(thread.last_message_time)}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 sm:gap-2 mb-1 flex-wrap">
                          {thread.other_user_role && (
                            <span className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded ${getRoleBadgeColor(thread.other_user_role)}`}>
                              {thread.other_user_role}
                            </span>
                          )}
                          {isUnread && (
                            <span className="inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold leading-none text-white bg-gradient-to-br from-red-500 to-red-600 rounded-full min-w-[20px] h-5 shadow-lg shadow-red-500/50 ring-2 ring-white dark:ring-slate-950">
                              {thread.unread_count > 99 ? '99+' : thread.unread_count}
                            </span>
                          )}
                        </div>
                        <p className={`text-xs sm:text-sm leading-snug line-clamp-2 ${
                          isUnread
                            ? 'font-semibold text-slate-700 dark:text-slate-200'
                            : 'text-slate-500 dark:text-slate-400'
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
          {/* Mobile: Full width when thread selected, hidden when no thread */}
          {/* Tablet/Desktop: 60-65% width, always visible */}
          <div className={`${!selectedThread ? 'hidden sm:flex' : 'flex'} w-full sm:w-[60%] lg:w-[65%] flex-col bg-white dark:bg-slate-900 min-h-0`}>
            {selectedThread ? (
              <>
                <div className="flex-shrink-0 p-3 sm:p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between gap-2 sm:gap-3">
                  <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                    <button 
                      onClick={() => setSelectedThread(null)} 
                      className="sm:hidden p-2 -ml-2 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 active:scale-95 transition-transform touch-manipulation flex-shrink-0"
                      aria-label="Back to conversations"
                    >
                      <FiChevronLeft size={20} />
                    </button>
                    <Avatar
                      name={getThreadDisplayName(selectedThread)}
                      avatarUrl={selectedThread.other_user_avatar_url}
                      variant="gradient"
                      size="sm"
                    />
                    <div className="min-w-0 flex-1">
                      <h3 className="font-bold text-sm sm:text-base text-slate-900 dark:text-white truncate">
                        {getThreadDisplayName(selectedThread)}
                      </h3>
                      <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                        {selectedThread.other_user_role && (
                          <span className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded ${getRoleBadgeColor(selectedThread.other_user_role)}`}>
                            {selectedThread.other_user_role}
                          </span>
                        )}
                        {isConnected && (
                          <span className="text-[10px] sm:text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span> 
                            <span className="hidden sm:inline">Online</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <button 
                    onClick={() => window.history.back()} 
                    className="hidden sm:block p-2 text-slate-400 hover:text-slate-600 dark:hover:text-white active:scale-95 transition-transform touch-manipulation flex-shrink-0"
                    aria-label="Close messages"
                  >
                    <FiX size={20} />
                  </button>
                </div>

                <div className="relative flex-1 min-h-0 bg-slate-50 dark:bg-slate-950/30 flex flex-col">
                  <div ref={messagesContainerRef} className="flex-1 overflow-y-auto overscroll-contain p-3 sm:p-4 space-y-3 sm:space-y-4 min-h-0">
                    {orderedMessages.map((msg, index) => {
                      const isMe = msg.sender_id === currentUser.id;
                      const isRecentMessage = recentMessageIds.includes(msg.id);
                      const showDivider = unreadStartIndex === index;
                      // For sent messages: is_read means recipient has read it
                      // For received messages: is_read means current user has read it
                      const isRead = msg.is_read || msg.delivery_state === "read";

                      return (
                        <div key={msg.id}>
                          {showDivider && (
                            <div className="flex items-center gap-2 sm:gap-3 py-1">
                              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800"></div>
                              <span className="text-[10px] uppercase tracking-wide text-emerald-600/70 dark:text-emerald-400/70">New messages</span>
                              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800"></div>
                            </div>
                          )}
                          <div className={`group flex ${isMe ? 'justify-end' : 'justify-start'} ${isRecentMessage ? 'animate-in slide-in-from-bottom-1 duration-150 ease-out' : ''}`}>
                            <div className={`max-w-[85%] sm:max-w-[75%] lg:max-w-[70%] rounded-2xl px-3 sm:px-4 py-2.5 sm:py-3 text-sm sm:text-base ${
                              isMe
                                ? 'bg-emerald-600 text-white rounded-br-sm'
                                : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 rounded-bl-sm'
                            }`}>
                              <p className="leading-relaxed break-words">{msg.message}</p>
                              <div className={`mt-1.5 sm:mt-1 flex items-center gap-1 text-[10px] sm:text-[11px] ${
                                isMe ? 'justify-end text-emerald-100' : 'justify-start text-slate-400 dark:text-slate-500'
                              }`}>
                                <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                {isMe && (
                                  <span className="flex items-center gap-0.5">
                                    <FiCheck size={11} className="opacity-80" />
                                    {isRead && <FiCheck size={11} className="opacity-80 -ml-2" />}
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
                      className="absolute bottom-3 sm:bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-white/90 dark:bg-slate-900/90 px-3 sm:px-4 py-2 text-xs font-medium text-slate-700 dark:text-slate-200 shadow-md border border-slate-200 dark:border-slate-800 backdrop-blur-sm transition-colors active:scale-95 touch-manipulation hover:bg-white dark:hover:bg-slate-800 z-10"
                    >
                      New messages ↓
                    </button>
                  )}
                </div>

                {/* Typing indicator */}
                {typingUsers.size > 0 && (
                  <div className="flex-shrink-0 px-3 sm:px-4 py-2 opacity-100">
                    <div className="inline-flex items-center gap-1 rounded-full bg-slate-100 dark:bg-slate-800 px-3 py-1.5">
                      <span className="typing-dot"></span>
                      <span className="typing-dot"></span>
                      <span className="typing-dot"></span>
                    </div>
                  </div>
                )}

                <div className="flex-shrink-0 p-3 sm:p-4 border-t border-slate-200 dark:border-slate-800 safe-area-inset-bottom bg-white dark:bg-slate-900">
                  <form onSubmit={sendMessage} className="space-y-2">
                    <div className="flex gap-2 sm:gap-3 items-end">
                      <div className="flex-1 relative">
                        <textarea
                          ref={messageInputRef}
                          value={newMessage}
                          onChange={handleMessageChange}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              sendMessage(e);
                            } else {
                              handleTyping();
                            }
                          }}
                          placeholder="Write your message here (press Enter to send, Shift+Enter for new line)"
                          maxLength={MESSAGE_MAX_LENGTH}
                          rows={3}
                          className={`
                            w-full bg-slate-100 dark:bg-slate-800 border-none rounded-2xl px-4 sm:px-5 py-2.5 sm:py-3 
                            text-sm sm:text-base leading-relaxed
                            focus:ring-2 focus:ring-emerald-500 focus:outline-none 
                            text-slate-900 dark:text-white placeholder-slate-400
                            resize-none overflow-y-auto
                            ${messageError ? 'ring-2 ring-red-500 dark:ring-red-500' : ''}
                            ${newMessage.length >= MESSAGE_MAX_LENGTH * MESSAGE_WARNING_THRESHOLD && !messageError 
                              ? 'ring-2 ring-amber-500 dark:ring-amber-500' 
                              : ''}
                          `}
                          style={{ minHeight: '72px', maxHeight: '240px' }}
                          aria-label="Message input (visible to the recipient)"
                          aria-describedby={messageError ? "message-error" : newMessage.length > 0 ? "message-counter" : undefined}
                        />
                        {/* Character counter */}
                        {newMessage.length > 0 && (
                          <div 
                            id="message-counter"
                            className={`absolute bottom-2 right-3 text-[10px] sm:text-xs ${
                              newMessage.length >= MESSAGE_MAX_LENGTH 
                                ? 'text-red-600 dark:text-red-400 font-medium' 
                                : newMessage.length >= MESSAGE_MAX_LENGTH * MESSAGE_WARNING_THRESHOLD
                                  ? 'text-amber-600 dark:text-amber-400'
                                  : 'text-slate-400 dark:text-slate-500'
                            }`}
                            aria-live="polite"
                          >
                            {newMessage.length}/{MESSAGE_MAX_LENGTH}
                            {newMessage.length >= MESSAGE_MAX_LENGTH && ' (limit reached)'}
                          </div>
                        )}
                      </div>
                      <button 
                        type="submit"
                        disabled={!newMessage.trim() || sendingMessage || !!messageError || newMessage.length > MESSAGE_MAX_LENGTH}
                        className="p-2.5 sm:p-3 bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white rounded-full disabled:opacity-50 disabled:cursor-not-allowed transition-all touch-manipulation active:scale-95 min-w-[44px] min-h-[44px] flex items-center justify-center flex-shrink-0"
                        aria-label="Send message"
                      >
                        <FiSend size={18} className="sm:w-5 sm:h-5" />
                      </button>
                    </div>
                    {/* Error message */}
                    {messageError && (
                      <p
                        id="message-error"
                        className="text-xs sm:text-sm text-red-600 dark:text-red-400 px-1"
                        role="alert"
                      >
                        {messageError}
                      </p>
                    )}
                  </form>
                </div>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-6 sm:p-8">
                <div className="w-16 h-16 sm:w-20 sm:h-20 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                  <FiMessageSquare size={32} className="sm:w-10 sm:h-10 text-slate-300 dark:text-slate-600" />
                </div>
                <p className="text-base sm:text-lg font-medium text-slate-600 dark:text-slate-300 mb-1">Your Messages</p>
                <p className="text-sm sm:text-base text-center px-4">Select a conversation to start chatting.</p>
                <button 
                  onClick={() => window.history.back()} 
                  className="sm:hidden mt-6 px-4 py-2 text-emerald-600 font-medium active:scale-95 transition-transform touch-manipulation"
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
