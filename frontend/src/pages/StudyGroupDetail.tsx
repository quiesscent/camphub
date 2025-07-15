
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Users, Calendar, MapPin, MessageCircle, Bell, Settings } from 'lucide-react';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const StudyGroupDetail = () => {
  const { id } = useParams();
  const [isJoined, setIsJoined] = useState(false);

  const group = {
    id: 1,
    name: 'Advanced Mathematics Study Group',
    subject: 'Mathematics',
    description: 'Weekly study sessions for Calculus III and Linear Algebra students. We focus on problem-solving techniques and exam preparation.',
    members: 12,
    maxMembers: 15,
    meetingTime: 'Tuesdays 6:00 PM',
    location: 'Library Room 204',
    difficulty: 'Advanced',
    organizer: 'Sarah Johnson',
    createdDate: 'January 15, 2024'
  };

  const members = [
    { name: 'Sarah Johnson', role: 'Organizer', avatar: '/placeholder.svg', year: 'Senior' },
    { name: 'Mike Chen', role: 'Member', avatar: '/placeholder.svg', year: 'Junior' },
    { name: 'Emma Davis', role: 'Member', avatar: '/placeholder.svg', year: 'Sophomore' },
    { name: 'Alex Rivera', role: 'Member', avatar: '/placeholder.svg', year: 'Senior' }
  ];

  const meetings = [
    {
      date: 'March 26, 2024',
      time: '6:00 PM - 8:00 PM',
      topic: 'Vector Spaces and Linear Transformations',
      location: 'Library Room 204',
      status: 'upcoming'
    },
    {
      date: 'March 19, 2024',
      time: '6:00 PM - 8:00 PM',
      topic: 'Integration Techniques Review',
      location: 'Library Room 204',
      status: 'completed'
    }
  ];

  const resources = [
    { name: 'Calculus III Problem Set 1', type: 'PDF', uploadedBy: 'Sarah Johnson' },
    { name: 'Linear Algebra Notes', type: 'DOC', uploadedBy: 'Mike Chen' },
    { name: 'Practice Exam Solutions', type: 'PDF', uploadedBy: 'Emma Davis' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Group Header */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:justify-between md:items-start space-y-4 md:space-y-0">
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <h1 className="text-3xl font-bold text-gray-900">{group.name}</h1>
                  <Badge variant="outline">{group.subject}</Badge>
                  <Badge className="bg-red-100 text-red-800">{group.difficulty}</Badge>
                </div>
                
                <p className="text-gray-600 mb-4">{group.description}</p>
                
                <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                  <div className="flex items-center">
                    <Users className="w-4 h-4 mr-2" />
                    {group.members} / {group.maxMembers} members
                  </div>
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-2" />
                    {group.meetingTime}
                  </div>
                  <div className="flex items-center">
                    <MapPin className="w-4 h-4 mr-2" />
                    {group.location}
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col space-y-2">
                <Button 
                  onClick={() => setIsJoined(!isJoined)}
                  className={isJoined ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'}
                >
                  {isJoined ? 'Joined ✓' : 'Join Group'}
                </Button>
                <Button variant="outline">
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Message
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="members">Members</TabsTrigger>
            <TabsTrigger value="meetings">Meetings</TabsTrigger>
            <TabsTrigger value="resources">Resources</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>About this Group</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700">{group.description}</p>
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Organizer:</span>
                        <p>{group.organizer}</p>
                      </div>
                      <div>
                        <span className="font-medium">Created:</span>
                        <p>{group.createdDate}</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Next Meeting</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                    <div>
                      <h4 className="font-medium">{meetings[0].topic}</h4>
                      <p className="text-sm text-gray-600">{meetings[0].date} • {meetings[0].time}</p>
                      <p className="text-sm text-gray-600">{meetings[0].location}</p>
                    </div>
                    <Button size="sm">
                      <Bell className="w-4 h-4 mr-2" />
                      Remind Me
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Members ({group.members})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {members.slice(0, 4).map((member, index) => (
                      <div key={index} className="flex items-center space-x-3">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback>{member.name.charAt(0)}</AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{member.name}</p>
                          <p className="text-xs text-gray-500">{member.year}</p>
                        </div>
                        {member.role === 'Organizer' && (
                          <Badge variant="secondary" className="text-xs">Admin</Badge>
                        )}
                      </div>
                    ))}
                    <Button variant="ghost" className="w-full text-sm">
                      View All Members
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="members" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>All Members ({group.members})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {members.map((member, index) => (
                    <div key={index} className="flex items-center space-x-3 p-3 border rounded-lg">
                      <Avatar>
                        <AvatarFallback>{member.name.charAt(0)}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <p className="font-medium">{member.name}</p>
                        <p className="text-sm text-gray-500">{member.year}</p>
                        {member.role === 'Organizer' && (
                          <Badge variant="secondary" className="text-xs mt-1">Organizer</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="meetings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Meeting Schedule</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {meetings.map((meeting, index) => (
                    <div key={index} className={`p-4 rounded-lg border ${
                      meeting.status === 'upcoming' ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'
                    }`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-medium">{meeting.topic}</h4>
                          <p className="text-sm text-gray-600">{meeting.date} • {meeting.time}</p>
                          <p className="text-sm text-gray-600">{meeting.location}</p>
                        </div>
                        <Badge variant={meeting.status === 'upcoming' ? 'default' : 'secondary'}>
                          {meeting.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="resources" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Shared Resources</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {resources.map((resource, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">{resource.name}</p>
                        <p className="text-sm text-gray-500">Uploaded by {resource.uploadedBy}</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline">{resource.type}</Badge>
                        <Button size="sm" variant="ghost">Download</Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default StudyGroupDetail;
