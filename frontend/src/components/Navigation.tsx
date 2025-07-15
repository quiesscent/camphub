
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bell, MessageCircle, Search, User, Calendar, MapPin, Users, Book, Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

const Navigation = () => {
  const location = useLocation();
  const [showSecondaryNav, setShowSecondaryNav] = useState(false);
  
  const isActive = (path: string) => location.pathname === path;
  
  const mainNavItems = [
    { path: '/dashboard', label: 'Feed', icon: Users },
    { path: '/messages', label: 'Messages', icon: MessageCircle },
    { path: '/study-groups', label: 'Study Groups', icon: Users },
    { path: '/notifications', label: 'Notifications', icon: Bell },
  ];

  const secondaryNavItems = [
    { path: '/courses', label: 'Courses', icon: Book },
    { path: '/events', label: 'Events', icon: Calendar },
    { path: '/marketplace', label: 'Marketplace', icon: MapPin },
    { path: '/institutions', label: 'Institutions', icon: Book },
  ];

  return (
    <>
      <nav className="sticky top-0 z-50 bg-white  border-gray-200 s">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Users className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl text-gray-900">CampusConnect</span>
            </Link>

            {/* Search Bar - Desktop Only */}
            <div className="hidden md:flex flex-1 max-w-md mx-8">
              <div className="relative w-full">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  type="text"
                  placeholder="Search students, courses, events..."
                  className="pl-10 bg-white-50 rounded-3xl focus:bg-white"
                />
              </div>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center space-x-1">
              {mainNavItems.slice(0, 3).map((item) => (
                <Link key={item.path} to={item.path}>
                  <Button
                    variant={isActive(item.path) ? "default" : "ghost"}
                    className={`relative ${
                      isActive(item.path) 
                        ? "bg-blue-100 text-blue-700 hover:bg-blue-200" 
                        : "text-gray-600 hover:text-gray-900"
                    }`}
                  >
                    <item.icon className="w-4 h-4 mr-2" />
                    {item.label}
                    {item.label === 'Messages' && (
                      <Badge className="ml-2 bg-red-500 text-white text-xs px-1.5 py-0.5">
                        3
                      </Badge>
                    )}
                  </Button>
                </Link>
              ))}

              {/* Toggle for secondary nav */}
              <Button
                variant="ghost"
                onClick={() => setShowSecondaryNav(!showSecondaryNav)}
                className="text-gray-600 hover:text-gray-900"
              >
                <Menu className="w-4 h-4 mr-2" />
                More
              </Button>
            </div>

            {/* Right Side Actions */}
            <div className="flex items-center space-x-3">
              <Link to="/notifications" className="lg:hidden">
                <Button variant="ghost" size="sm" className="relative">
                  <Bell className="w-5 h-5 text-gray-600" />
                  <Badge className="absolute -top-1 -right-1 bg-red-500 text-white text-xs px-1.5 py-0.5">
                    5
                  </Badge>
                </Button>
              </Link>
              
              <Link to="/profile">
                <Button variant="ghost" size="sm" className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                </Button>
              </Link>
            </div>
          </div>

          {/* Secondary Navigation - Desktop */}
          {showSecondaryNav && (
            <div className="hidden lg:block border-t border-gray-200 py-2">
              <div className="flex items-center space-x-1">
                {secondaryNavItems.map((item) => (
                  <Link key={item.path} to={item.path}>
                    <Button
                      variant={isActive(item.path) ? "default" : "ghost"}
                      size="sm"
                      className={`${
                        isActive(item.path) 
                          ? "bg-blue-100 text-blue-700 hover:bg-blue-200" 
                          : "text-gray-600 hover:text-gray-900"
                      }`}
                    >
                      <item.icon className="w-4 h-4 mr-2" />
                      {item.label}
                    </Button>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Secondary Navigation - Mobile */}
      {showSecondaryNav && (
        <div className="lg:hidden fixed top-16 left-0 right-0 z-40 bg-white border-b border-gray-200 shadow-lg">
          <div className="grid grid-cols-2 gap-2 p-4">
            {secondaryNavItems.map((item) => (
              <Link key={item.path} to={item.path} onClick={() => setShowSecondaryNav(false)}>
                <Button
                  variant={isActive(item.path) ? "default" : "ghost"}
                  className={`w-full justify-start ${
                    isActive(item.path) 
                      ? "bg-blue-100 text-blue-700 hover:bg-blue-200" 
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  <item.icon className="w-4 h-4 mr-2" />
                  {item.label}
                </Button>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Bottom Navigation - Mobile Only */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow-lg">
        <div className="flex justify-around py-2">
          {mainNavItems.map((item) => (
            <Link key={item.path} to={item.path} className="flex-1">
              <Button
                variant="ghost"
                size="sm"
                className={`w-full flex flex-col items-center space-y-1 relative ${
                  isActive(item.path) ? "text-blue-600" : "text-gray-600"
                }`}
              >
                <item.icon className="w-5 h-5" />
                <span className="text-xs">{item.label}</span>
                {item.label === 'Messages' && (
                  <Badge className="absolute -top-1 right-2 bg-red-500 text-white text-xs px-1 py-0.5 min-w-0 h-4 flex items-center justify-center">
                    3
                  </Badge>
                )}
                {item.label === 'Notifications' && (
                  <Badge className="absolute -top-1 right-2 bg-red-500 text-white text-xs px-1 py-0.5 min-w-0 h-4 flex items-center justify-center">
                    5
                  </Badge>
                )}
              </Button>
            </Link>
          ))}
          {/* More button for mobile */}
          <div className="flex-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSecondaryNav(!showSecondaryNav)}
              className={`w-full flex flex-col items-center space-y-1 ${
                showSecondaryNav ? "text-blue-600" : "text-gray-600"
              }`}
            >
              <Menu className="w-5 h-5" />
              <span className="text-xs">More</span>
            </Button>
          </div>
        </div>
      </div>
    </>
  );
};

export default Navigation;
