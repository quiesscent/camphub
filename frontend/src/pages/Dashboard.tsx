
import React, { useState } from 'react';
import { Plus, TrendingUp, Users, Calendar, MessageCircle } from 'lucide-react';
import Navigation from '@/components/Navigation';
import PostCard from '@/components/PostCard';
import CreatePostModal from '@/components/CreatePostModal';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const Dashboard = () => {
  const [showCreatePost, setShowCreatePost] = useState(false);

  const mockPosts = [
    {
      id: '1',
      author: {
        name: 'Sarah Johnson',
        role: 'Student' as const,
        major: 'Computer Science',
        year: '2025'
      },
      content: 'Looking for study partners for CS 330 - Data Structures! We could meet at the library every Tuesday and Thursday. DM me if interested! 📚',
      type: 'text' as const,
      timestamp: '2 hours ago',
      likes: 15,
      comments: 8,
      shares: 3,
      tags: ['studygroup', 'cs330', 'datastructures']
    },
    {
      id: '2',
      author: {
        name: 'Dr. Michael Chen',
        role: 'Faculty' as const,
        major: 'Psychology Department'
      },
      content: 'Reminder: Research Methods in Psychology (PSY 201) midterm exam is scheduled for next Friday. Office hours extended this week - Mon/Wed 2-4 PM. Good luck everyone!',
      type: 'text' as const,
      timestamp: '4 hours ago',
      likes: 23,
      comments: 12,
      shares: 7,
      isPinned: true,
      tags: ['psy201', 'midterm', 'officehours']
    },
    {
      id: '3',
      author: {
        name: 'Anonymous',
        role: 'Student' as const
      },
      content: 'Does anyone else feel overwhelmed with the workload this semester? Looking for tips on time management and stress relief. Thanks 🙏',
      type: 'text' as const,
      timestamp: '6 hours ago',
      likes: 45,
      comments: 23,
      shares: 12,
      isAnonymous: true,
      tags: ['mentalhealth', 'timemanagement', 'stress']
    }
  ];

  const campusStats = [
    { title: 'Active Users', value: '2,847', icon: Users, change: '+12%' },
    { title: 'Today\'s Posts', value: '156', icon: MessageCircle, change: '+8%' },
    { title: 'Upcoming Events', value: '12', icon: Calendar, change: '+3%' },
    { title: 'Trending Topics', value: '8', icon: TrendingUp, change: '+15%' }
  ];

  const trendingTopics = [
    '#midterms', '#studygroups', '#campusevents', '#jobfair', '#gradschool', '#mentalhealth'
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Left Sidebar - Campus Stats */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Campus Pulse</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {campusStats.map((stat, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <stat.icon className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">{stat.title}</p>
                        <p className="text-lg font-semibold">{stat.value}</p>
                      </div>
                    </div>
                    <Badge variant="secondary" className="text-xs text-green-600">
                      {stat.change}
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Trending Topics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {trendingTopics.map((topic, index) => (
                    <Badge key={index} variant="outline" className="text-sm cursor-pointer hover:bg-blue-50">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Feed */}
          <div className="lg:col-span-2">
            {/* Create Post */}
            <Card className="mb-6">
              <CardContent className="p-4">
                <Button
                  onClick={() => setShowCreatePost(true)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Share something with your campus
                </Button>
              </CardContent>
            </Card>

            {/* Posts Feed */}
            <div className="space-y-4">
              {mockPosts.map((post) => (
                <PostCard key={post.id} {...post} />
              ))}
            </div>
          </div>

          {/* Right Sidebar - Quick Actions */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="outline" className="w-full justify-start">
                  <Calendar className="w-4 h-4 mr-2" />
                  Create Event
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Users className="w-4 h-4 mr-2" />
                  Find Study Group
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Join Discussion
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Campus Resources</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-900">Library Hours</h4>
                  <p className="text-sm text-blue-700">Mon-Thu: 7AM-11PM</p>
                  <p className="text-sm text-blue-700">Fri-Sun: 9AM-9PM</p>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <h4 className="font-medium text-green-900">Dining Hall</h4>
                  <p className="text-sm text-green-700">Today's Special:</p>
                  <p className="text-sm text-green-700">Grilled Salmon & Rice</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <CreatePostModal 
        isOpen={showCreatePost} 
        onClose={() => setShowCreatePost(false)} 
      />
    </div>
  );
};

export default Dashboard;
