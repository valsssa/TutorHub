"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  FiMail,
  FiMessageSquare,
  FiUser,
  FiClock,
  FiSearch,
} from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import { messages, auth, tutors } from "@/lib/api";
import { MessageThread, User } from "@/types";
import { useToast } from "@/components/ToastContainer";
import LoadingSpinner from "@/components/LoadingSpinner";
import {
  MessageList,
  MessageInput,
  EmptyState,
  ConnectionStatus,
} from "@/components/messaging";
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

  // Handle tutor/user parameter from URL for starting new conversation
  useEffect(() => {
    const tutorParam = searchParams?.get("tutor");
    const userParam = searchParams?.get("user");
    const targetUserId = tutorParam ? parseInt(tutorParam) : userParam ? parseInt(userParam) : null;
    
    if (targetUserId && currentUser && threads.length >= 0) {
      // Check if we already have a thread with this user
      const existingThread = threads.find((t) => t.other_user_id === targetUserId);

      if (existingThread) {
        // Select existing thread
        selectThread(existingThread);
      } else {
        // For tutors, try to load profile info. For other users, load basic user info
        if (tutorParam) {
          tutors
            .get(targetUserId)
            .then((tutor) => {
              const displayName = tutor.title || `Tutor #${targetUserId}`;

              // Create a temporary thread-like object
              const tempThread: MessageThread = {
                other_user_id: targetUserId,
                other_user_email: displayName,
                other_user_role: "tutor",
                booking_id: undefined,
                last_message: "Start a new conversation",
                last_message_time: new Date().toISOString(),
                total_messages: 0,
                unread_count: 0,
              };
              setSelectedThread(tempThread);
              setMessages([]);
            })
            .catch(() => {
              showError("Failed to load tutor information");
            });
        } else if (userParam) {
          // Load basic user info for admin messaging any user
          auth.getCurrentUser()
            .then(() => {
              // Create a temporary thread for any user type
              const tempThread: MessageThread = {
                other_user_id: targetUserId,
                other_user_email: `User #${targetUserId}`,
                other_user_role: "student", // Will be updated when messages load
                booking_id: undefined,
                last_message: "Start a new conversation",
                last_message_time: new Date().toISOString(),
                total_messages: 0,
                unread_count: 0,
              };
              setSelectedThread(tempThread);
              setMessages([]);
            })
            .catch(() => {
              showError("Failed to start conversation");
            });
        }
      }
    }
  }, [searchParams, currentUser, threads, selectThread, showError, setMessages]);

  const sendMessage = useCallback(
    async (messageText: string) => {
      if (!messageText.trim() || !selectedThread || !currentUser) return;

      setSendingMessage(true);
      try {
        const sentMessage = await messages.send(
          selectedThread.other_user_id,
          messageText,
          selectedThread.booking_id || undefined
        );

        setMessages((prevMessages) => [...prevMessages, sentMessage]);

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
    [currentUser, selectedThread, threads, loadThreads, showError, showSuccess, setMessages]
  );

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
        return "bg-blue-100 text-blue-800";
      case "student":
        return "bg-green-100 text-green-800";
      case "admin":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              Messages
              {getTotalUnread() > 0 && (
                <span className="bg-primary-600 text-white text-sm px-3 py-1 rounded-full">
                  {getTotalUnread()} unread
                </span>
              )}
            </h1>
            <p className="text-gray-600 mt-2">
              Chat with tutors and students in real-time
            </p>
          </div>
          <ConnectionStatus isConnected={isConnected} />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-3 h-[700px]">
          {/* Thread List */}
          <div className="border-r border-gray-200 overflow-y-auto flex flex-col">
            <div className="p-4 bg-gray-50 border-b border-gray-200 flex-shrink-0">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <FiMessageSquare className="w-5 h-5" />
                Conversations ({filteredThreads.length})
              </h2>
              
              {/* Search */}
              <div className="relative">
                <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {filteredThreads.length === 0 && (
              <div className="p-8 text-center">
                <FiMail className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 text-sm">
                  {searchQuery ? "No conversations found" : "No messages yet"}
                </p>
              </div>
            )}

            <div className="divide-y divide-gray-200 flex-1 overflow-y-auto">
              {filteredThreads.map((thread) => (
                <div
                  key={`${thread.other_user_id}-${thread.booking_id || "general"}`}
                  className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                    selectedThread?.other_user_id === thread.other_user_id &&
                    selectedThread?.booking_id === thread.booking_id
                      ? "bg-primary-50 border-l-4 border-primary-600"
                      : ""
                  }`}
                  onClick={() => selectThread(thread)}
                >
                  <div className="flex items-start gap-3">
                    <div className="bg-gray-200 rounded-full p-2 flex-shrink-0">
                      <FiUser className="w-4 h-4 text-gray-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <p className="font-medium text-gray-900 truncate text-sm">
                            {thread.other_user_email}
                          </p>
                          {thread.other_user_role && (
                            <span
                              className={`text-xs px-2 py-0.5 rounded ${getRoleBadgeColor(
                                thread.other_user_role
                              )}`}
                            >
                              {thread.other_user_role}
                            </span>
                          )}
                        </div>
                        {thread.unread_count > 0 && (
                          <span className="bg-primary-600 text-white text-xs px-2 py-0.5 rounded-full font-medium ml-2 flex-shrink-0">
                            {thread.unread_count}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 truncate mb-1">
                        {thread.last_sender_id === currentUser.id && "You: "}
                        {thread.last_message}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <FiClock className="w-3 h-3" />
                        {formatTime(thread.last_message_time)}
                        {thread.booking_id && (
                          <>
                            <span className="text-gray-400">•</span>
                            <span>Booking #{thread.booking_id}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Message View */}
          <div className="lg:col-span-2 flex flex-col">
            {selectedThread ? (
              <>
                {/* Thread Header */}
                <div className="p-4 bg-gray-50 border-b border-gray-200 flex-shrink-0">
                  <div className="flex items-center gap-3">
                    <div className="bg-gray-200 rounded-full p-2">
                      <FiUser className="w-5 h-5 text-gray-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-gray-900">
                          {selectedThread.other_user_email}
                        </p>
                        {selectedThread.other_user_role && (
                          <span
                            className={`text-xs px-2 py-0.5 rounded ${getRoleBadgeColor(
                              selectedThread.other_user_role
                            )}`}
                          >
                            {selectedThread.other_user_role}
                          </span>
                        )}
                      </div>
                      {selectedThread.booking_id && (
                        <p className="text-xs text-gray-600">
                          Booking #{selectedThread.booking_id}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <MessageList
                  messages={threadMessages}
                  currentUserId={currentUser.id}
                  showTyping={typingUsers.size > 0}
                />

                {/* Message Input */}
                <MessageInput
                  onSend={sendMessage}
                  onTyping={handleTyping}
                  disabled={false}
                  isLoading={sendingMessage}
                />
              </>
            ) : (
              <EmptyState />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
