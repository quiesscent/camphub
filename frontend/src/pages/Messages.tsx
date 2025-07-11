
import React, { useState } from 'react';
import { Search, Send, Phone, Video, MoreVertical, Smile, Paperclip, MessageCircle, ArrowLeft } from 'lucide-react';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';

const Messages = () => {
  const [selectedChat, setSelectedChat] = useState<number | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [showChatRoom, setShowChatRoom] = useState(false);

  const chats = [
    {
      id: 1,
      name: 'Sarah Johnson',
      lastMessage: 'Thanks for the study notes!',
      timestamp: '2m ago',
      unread: 2,
      avatar: '/placeholder.svg',
      online: true
    },
    {
      id: 2,
      name: 'Study Group - Math',
      lastMessage: 'Meeting tomorrow at 6 PM',
      timestamp: '1h ago',
      unread: 0,
      avatar: '/placeholder.svg',
      online: false,
      isGroup: true
    },
    {
      id: 3,
      name: 'Mike Chen',
      lastMessage: 'See you in class!',
      timestamp: '3h ago',
      unread: 1,
      avatar: '/placeholder.svg',
      online: true
    },
    {
      id: 4,
      name: 'Emma Davis',
      lastMessage: 'Can you help with the assignment?',
      timestamp: '1d ago',
      unread: 0,
      avatar: '/placeholder.svg',
      online: false
    }
  ];

  const messages = [
    {
      id: 1,
      sender: 'Sarah Johnson',
      content: 'Hey! How did your exam go?',
      timestamp: '10:30 AM',
      isOwn: false
    },
    {
      id: 2,
      sender: 'You',
      content: 'It went pretty well! Thanks for asking. Your study notes really helped.',
      timestamp: '10:32 AM',
      isOwn: true
    },
    {
      id: 3,
      sender: 'Sarah Johnson',
      content: 'That\'s awesome! I\'m so glad they were helpful.',
      timestamp: '10:33 AM',
      isOwn: false
    },
    {
      id: 4,
      sender: 'Sarah Johnson',
      content: 'Do you want to study together for the next one?',
      timestamp: '10:34 AM',
      isOwn: false
    },
    {
      id: 5,
      sender: 'You',
      content: 'Absolutely! When works best for you?',
      timestamp: '10:35 AM',
      isOwn: true
    }
  ];

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (newMessage.trim()) {
      console.log('Sending message:', newMessage);
      setNewMessage('');
    }
  };

  const handleChatSelect = (chatId: number) => {
    setSelectedChat(chatId);
    setShowChatRoom(true);
  };

  const handleBackToList = () => {
    setShowChatRoom(false);
    setSelectedChat(null);
  };

  const currentChat = chats.find(chat => chat.id === selectedChat);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navigation />
      
      <div className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        {/* Desktop Layout */}
        <div className="hidden lg:grid grid-cols-3 gap-4 h-[calc(100vh-12rem)]">
          {/* Chat List */}
          <Card className="col-span-1">
            <CardContent className="p-0 h-full flex flex-col">
              {/* Header */}
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-xl font-bold mb-3">Messages</h2>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Search conversations..."
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Chat List */}
              <div className="flex-1 overflow-y-auto">
                {chats.map((chat) => (
                  <div
                    key={chat.id}
                    onClick={() => setSelectedChat(chat.id)}
                    className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedChat === chat.id ? 'bg-blue-50 border-blue-200' : ''
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="relative">
                        <Avatar>
                          <AvatarFallback>{chat.name.charAt(0)}</AvatarFallback>
                        </Avatar>
                        {chat.online && !chat.isGroup && (
                          <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h3 className="font-medium truncate">{chat.name}</h3>
                          <span className="text-xs text-gray-500">{chat.timestamp}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <p className="text-sm text-gray-600 truncate">{chat.lastMessage}</p>
                          {chat.unread > 0 && (
                            <Badge className="bg-blue-500 text-white text-xs">
                              {chat.unread}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Chat Room */}
          <Card className="col-span-2">
            <CardContent className="p-0 h-full flex flex-col">
              {currentChat ? (
                <>
                  {/* Chat Header */}
                  <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="relative">
                        <Avatar>
                          <AvatarFallback>{currentChat.name.charAt(0)}</AvatarFallback>
                        </Avatar>
                        {currentChat.online && !currentChat.isGroup && (
                          <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
                        )}
                      </div>
                      <div>
                        <h3 className="font-semibold">{currentChat.name}</h3>
                        <p className="text-sm text-gray-500">
                          {currentChat.isGroup ? `${chats.length} members` : currentChat.online ? 'Online' : 'Last seen 2h ago'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Button variant="ghost" size="sm">
                        <Phone className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Video className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.isOwn ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          message.isOwn 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-gray-100 text-gray-900'
                        }`}>
                          <p className="text-sm">{message.content}</p>
                          <p className={`text-xs mt-1 ${
                            message.isOwn ? 'text-blue-100' : 'text-gray-500'
                          }`}>
                            {message.timestamp}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Message Input */}
                  <div className="p-4 border-t border-gray-200">
                    <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
                      <Button type="button" variant="ghost" size="sm">
                        <Paperclip className="w-4 h-4" />
                      </Button>
                      <Input
                        placeholder="Type a message..."
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        className="flex-1"
                      />
                      <Button type="button" variant="ghost" size="sm">
                        <Smile className="w-4 h-4" />
                      </Button>
                      <Button type="submit" size="sm" disabled={!newMessage.trim()}>
                        <Send className="w-4 h-4" />
                      </Button>
                    </form>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                      <MessageCircle className="w-8 h-8 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Select a conversation</h3>
                    <p className="text-gray-500">Choose a chat from the sidebar to start messaging</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Mobile Layout */}
        <div className="lg:hidden h-[calc(100vh-12rem)]">
          {!showChatRoom ? (
            /* Chat List Mobile */
            <Card className="h-full">
              <CardContent className="p-0 h-full flex flex-col">
                {/* Header */}
                <div className="p-4 border-b border-gray-200">
                  <h2 className="text-xl font-bold mb-3">Messages</h2>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="Search conversations..."
                      className="pl-10"
                    />
                  </div>
                </div>

                {/* Chat List */}
                <div className="flex-1 overflow-y-auto">
                  {chats.map((chat) => (
                    <div
                      key={chat.id}
                      onClick={() => handleChatSelect(chat.id)}
                      className="p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors active:bg-gray-100"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="relative">
                          <Avatar>
                            <AvatarFallback>{chat.name.charAt(0)}</AvatarFallback>
                          </Avatar>
                          {chat.online && !chat.isGroup && (
                            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
                          )}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <h3 className="font-medium truncate">{chat.name}</h3>
                            <span className="text-xs text-gray-500">{chat.timestamp}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <p className="text-sm text-gray-600 truncate">{chat.lastMessage}</p>
                            {chat.unread > 0 && (
                              <Badge className="bg-blue-500 text-white text-xs">
                                {chat.unread}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : (
            /* Chat Room Mobile */
            <Card className="h-full">
              <CardContent className="p-0 h-full flex flex-col">
                {currentChat && (
                  <>
                    {/* Chat Header with Back Button */}
                    <div className="p-4 border-b border-gray-200 flex items-center space-x-3">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={handleBackToList}
                        className="p-1"
                      >
                        <ArrowLeft className="w-5 h-5" />
                      </Button>
                      
                      <div className="flex items-center space-x-3 flex-1">
                        <div className="relative">
                          <Avatar>
                            <AvatarFallback>{currentChat.name.charAt(0)}</AvatarFallback>
                          </Avatar>
                          {currentChat.online && !currentChat.isGroup && (
                            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
                          )}
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold">{currentChat.name}</h3>
                          <p className="text-sm text-gray-500">
                            {currentChat.isGroup ? `${chats.length} members` : currentChat.online ? 'Online' : 'Last seen 2h ago'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Button variant="ghost" size="sm">
                          <Phone className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Video className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                      {messages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${message.isOwn ? 'justify-end' : 'justify-start'}`}
                        >
                          <div className={`max-w-xs px-4 py-2 rounded-lg ${
                            message.isOwn 
                              ? 'bg-blue-500 text-white' 
                              : 'bg-gray-100 text-gray-900'
                          }`}>
                            <p className="text-sm">{message.content}</p>
                            <p className={`text-xs mt-1 ${
                              message.isOwn ? 'text-blue-100' : 'text-gray-500'
                            }`}>
                              {message.timestamp}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Message Input */}
                    <div className="p-4 border-t border-gray-200">
                      <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
                        <Button type="button" variant="ghost" size="sm">
                          <Paperclip className="w-4 h-4" />
                        </Button>
                        <Input
                          placeholder="Type a message..."
                          value={newMessage}
                          onChange={(e) => setNewMessage(e.target.value)}
                          className="flex-1"
                        />
                        <Button type="button" variant="ghost" size="sm">
                          <Smile className="w-4 h-4" />
                        </Button>
                        <Button type="submit" size="sm" disabled={!newMessage.trim()}>
                          <Send className="w-4 h-4" />
                        </Button>
                      </form>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Messages;
