'use client'

import { Search, Filter, Phone, Video, MoreVertical, Paperclip, Smile, Send, MessageCircle } from 'lucide-react'
import { Conversation, Message } from '@/types/admin'
import Avatar from '@/components/Avatar'

interface MessagingSectionProps {
  conversations: Conversation[]
  messages: Message[]
  selectedConversation: Conversation | null
  setSelectedConversation: (conversation: Conversation | null) => void
  newMessage: string
  setNewMessage: (message: string) => void
  handleSendMessage: (e: React.FormEvent) => void
}

export default function MessagingSection({
  conversations,
  messages,
  selectedConversation,
  setSelectedConversation,
  newMessage,
  setNewMessage,
  handleSendMessage
}: MessagingSectionProps) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-800">Messaging</h3>
        <div className="flex items-center space-x-2">
          <button className="p-2 text-gray-600 hover:text-gray-900">
            <Search className="w-5 h-5" />
          </button>
          <button className="p-2 text-gray-600 hover:text-gray-900">
            <Filter className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="flex h-96">
        {/* Conversations List */}
        <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Recent Conversations</h4>
            <div className="space-y-2">
              {conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  onClick={() => setSelectedConversation(conversation)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedConversation?.id === conversation.id
                      ? 'bg-pink-50 border border-pink-200'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="relative">
                        <Avatar
                          name={conversation.participant}
                          userId={conversation.id}
                          size="sm"
                          showOnline={conversation.status === 'online'}
                        />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-gray-800 truncate">{conversation.participant}</p>
                          <span className="text-xs text-gray-500">{conversation.time}</span>
                        </div>
                        <p className="text-sm text-gray-600 truncate">{conversation.lastMessage}</p>
                      </div>
                    </div>
                    {conversation.unread > 0 && (
                      <div className="bg-pink-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                        {conversation.unread}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {selectedConversation ? (
            <>
              {/* Chat Header */}
              <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <Avatar
                      name={selectedConversation.participant}
                      userId={selectedConversation.id}
                      size="sm"
                      showOnline={selectedConversation.status === 'online'}
                    />
                  <div>
                    <p className="font-medium text-gray-800">{selectedConversation.participant}</p>
                    <p className="text-sm text-gray-600">{selectedConversation.role}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full">
                    <Phone className="w-5 h-5" />
                  </button>
                  <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full">
                    <Video className="w-5 h-5" />
                  </button>
                  <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full">
                    <MoreVertical className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 p-4 overflow-y-auto space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'sent' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.type === 'sent'
                          ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      <p className="text-sm">{message.message}</p>
                      <p className={`text-xs mt-1 ${
                        message.type === 'sent' ? 'text-pink-100' : 'text-gray-500'
                      }`}>
                        {message.time}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Message Input */}
              <div className="p-4 border-t border-gray-200">
                <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
                  <button type="button" className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full">
                    <Paperclip className="w-5 h-5" />
                  </button>
                  <button type="button" className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full">
                    <Smile className="w-5 h-5" />
                  </button>
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type a message..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                  />
                  <button
                    type="submit"
                    disabled={!newMessage.trim()}
                    className="p-2 bg-gradient-to-r from-pink-500 to-purple-600 text-white rounded-full hover:from-pink-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <MessageCircle className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">Select a conversation to start messaging</p>
                <p className="text-sm">Choose a user from the list to view your conversation history</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
