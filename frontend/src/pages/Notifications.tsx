
import React, { useState } from 'react';
import { Bell, Heart, MessageCircle, Users, Calendar, Settings, Check } from 'lucide-react';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const Notifications = () => {
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'like',
      title: 'Sarah Johnson liked your post',
      description: 'Linear Algebra study notes',
      timestamp: '2 minutes ago',
      isRead: false,
      avatar: '/placeholder.svg'
    },
    {
      id: 2,
      type: 'comment',
      title: 'Mike Chen commented on your post',
      description: '"This is really helpful! Thanks for sharing."',
      timestamp: '1 hour ago',
      isRead: false,
      avatar: '/placeholder.svg'
    },
    {
      id: 3,
      type: 'follow',
      title: 'Emma Davis started following you',
      description: 'Connect and share your academic journey',
      timestamp: '3 hours ago',
      isRead: true,
      avatar: '/placeholder.svg'
    },
    {
      id: 4,
      type: 'event',
      title: 'Reminder: Career Fair tomorrow',
      description: 'Spring Career Fair 2024 at Student Union Building',
      timestamp: '1 day ago',
      isRead: false,
      avatar: '/placeholder.svg'
    },
    {
      id: 5,
      type: 'group',
      title: 'New message in Math Study Group',
      description: 'Meeting tomorrow at 6 PM in Library Room 204',
      timestamp: '2 days ago',
      isRead: true,
      avatar: '/placeholder.svg'
    }
  ]);

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'like': return <Heart className="w-4 h-4 text-red-500" />;
      case 'comment': return <MessageCircle className="w-4 h-4 text-blue-500" />;
      case 'follow': return <Users className="w-4 h-4 text-green-500" />;
      case 'event': return <Calendar className="w-4 h-4 text-purple-500" />;
      case 'group': return <Users className="w-4 h-4 text-orange-500" />;
      default: return <Bell className="w-4 h-4 text-gray-500" />;
    }
  };

  const markAsRead = (id: number) => {
    setNotifications(notifications.map(notif => 
      notif.id === id ? { ...notif, isRead: true } : notif
    ));
  };

  const markAllAsRead = () => {
    setNotifications(notifications.map(notif => ({ ...notif, isRead: true })));
  };

  const unreadCount = notifications.filter(notif => !notif.isRead).length;

  return (
    <div className="min-h-screen sided">
      <Navigation />
      
      <div className="shape lg:w-full mt-5 ml-8 bg-gray-50  px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Notifications</h1>
            <p className="text-gray-600">
              {unreadCount > 0 ? `You have ${unreadCount} unread notifications` : 'You\'re all caught up!'}
            </p>
          </div>
          
          <div className="flex space-x-2">
            {unreadCount > 0 && (
              <Button onClick={markAllAsRead}  className=' rounded-md shadow-sm' >
                <Check className="w-4 h-4 mr-2 " />
                Mark all as read
              </Button>
            )}
            <Button variant="outline">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        <Tabs defaultValue="all" className="space-y-6">
          <TabsList>
            <TabsTrigger value="all">
              All
              {unreadCount > 0 && (
                <Badge className="ml-2 bg-blue-500 text-white">{unreadCount}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="unread">Unread</TabsTrigger>
            <TabsTrigger value="mentions">Mentions</TabsTrigger>
            <TabsTrigger value="events">Events</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            {notifications.length === 0 ? (
              <Card>
                <CardContent className="p-12 text-center">
                  <Bell className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No notifications yet</h3>
                  <p className="text-gray-600">When you get notifications, they'll show up here</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-2">
                {notifications.map((notification) => (
                  <Card 
                    key={notification.id} 
                    className={`cursor-pointer hover:shadow-md transition-shadow ${
                      !notification.isRead ? 'border-blue-200 bg-blue-50' : ''
                    }`}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start space-x-4">
                        <div className="flex-shrink-0">
                          <Avatar className="w-10 h-10">
                            <AvatarFallback>
                              {notification.title.split(' ')[0].charAt(0)}
                            </AvatarFallback>
                          </Avatar>
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            {getNotificationIcon(notification.type)}
                            <h4 className={`font-medium ${!notification.isRead ? 'text-gray-900' : 'text-gray-700'}`}>
                              {notification.title}
                            </h4>
                            {!notification.isRead && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                            )}
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-2">{notification.description}</p>
                          <p className="text-xs text-gray-500">{notification.timestamp}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="unread" className="space-y-4">
            <div className="space-y-2">
              {notifications.filter(notif => !notif.isRead).map((notification) => (
                <Card 
                  key={notification.id} 
                  className="cursor-pointer hover:shadow-md transition-shadow border-blue-200 bg-blue-50"
                  onClick={() => markAsRead(notification.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0">
                        <Avatar className="w-10 h-10">
                          <AvatarFallback>
                            {notification.title.split(' ')[0].charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          {getNotificationIcon(notification.type)}
                          <h4 className="font-medium text-gray-900">{notification.title}</h4>
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-2">{notification.description}</p>
                        <p className="text-xs text-gray-500">{notification.timestamp}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="mentions" className="space-y-4">
            <Card>
              <CardContent className="p-12 text-center">
                <MessageCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No mentions yet</h3>
                <p className="text-gray-600">When someone mentions you, it'll appear here</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="events" className="space-y-4">
            <div className="space-y-2">
              {notifications.filter(notif => notif.type === 'event').map((notification) => (
                <Card 
                  key={notification.id} 
                  className={`cursor-pointer hover:shadow-md transition-shadow ${
                    !notification.isRead ? 'border-blue-200 bg-blue-50' : ''
                  }`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0">
                        <Avatar className="w-10 h-10">
                          <AvatarFallback>
                            {notification.title.split(' ')[0].charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          {getNotificationIcon(notification.type)}
                          <h4 className={`font-medium ${!notification.isRead ? 'text-gray-900' : 'text-gray-700'}`}>
                            {notification.title}
                          </h4>
                          {!notification.isRead && (
                            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          )}
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-2">{notification.description}</p>
                        <p className="text-xs text-gray-500">{notification.timestamp}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Notifications;
