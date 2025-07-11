
import React, { useState } from 'react';
import { Search, MapPin, Users, Star, Filter, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

const Institutions = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');

  const institutions = [
    {
      id: 1,
      name: 'University of Technology',
      type: 'University',
      location: 'San Francisco, CA',
      students: 25000,
      rating: 4.8,
      description: 'Leading technological university with cutting-edge research facilities and innovative programs.',
      programs: ['Computer Science', 'Engineering', 'Data Science', 'AI & Machine Learning'],
      image: '/placeholder.svg',
      verified: true
    },
    {
      id: 2,
      name: 'Metro Community College',
      type: 'Community College',
      location: 'Los Angeles, CA',
      students: 12000,
      rating: 4.5,
      description: 'Comprehensive community college offering affordable education and career preparation.',
      programs: ['Business', 'Nursing', 'Liberal Arts', 'Trade Programs'],
      image: '/placeholder.svg',
      verified: true
    },
    {
      id: 3,
      name: 'State Medical University',
      type: 'Medical School',
      location: 'Boston, MA',
      students: 3500,
      rating: 4.9,
      description: 'Premier medical institution known for excellence in healthcare education and research.',
      programs: ['Medicine', 'Nursing', 'Pharmacy', 'Public Health'],
      image: '/placeholder.svg',
      verified: true
    },
    {
      id: 4,
      name: 'Liberal Arts College',
      type: 'College',
      location: 'Portland, OR',
      students: 8000,
      rating: 4.6,
      description: 'Small liberal arts college focused on personalized education and critical thinking.',
      programs: ['Literature', 'Philosophy', 'History', 'Psychology'],
      image: '/placeholder.svg',
      verified: false
    }
  ];

  const institutionTypes = ['all', 'University', 'College', 'Community College', 'Medical School'];

  const filteredInstitutions = institutions.filter(institution => {
    const matchesSearch = institution.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         institution.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         institution.programs.some(program => program.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = selectedType === 'all' || institution.type === selectedType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Educational Institutions</h1>
            <p className="text-gray-600">Discover and connect with universities and colleges</p>
          </div>
          
          <Button className="mt-4 md:mt-0 bg-blue-600 hover:bg-blue-700">
            Add Institution
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar - Filters */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Filter className="w-5 h-5" />
                  <span>Filters</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Search</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      type="text"
                      placeholder="Search institutions..."
                      className="pl-10"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Institution Type</label>
                  <div className="space-y-2">
                    {institutionTypes.map((type) => (
                      <Button
                        key={type}
                        variant={selectedType === type ? "default" : "ghost"}
                        className="w-full justify-start"
                        onClick={() => setSelectedType(type)}
                      >
                        {type === 'all' ? 'All Types' : type}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Total Institutions</span>
                  <span className="font-semibold">{institutions.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Universities</span>
                  <span className="font-semibold">{institutions.filter(i => i.type === 'University').length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Verified</span>
                  <span className="font-semibold">{institutions.filter(i => i.verified).length}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content - Institutions */}
          <div className="lg:col-span-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredInstitutions.map((institution) => (
                <Card key={institution.id} className="hover:shadow-lg transition-shadow">
                  <div className="h-48 bg-gradient-to-br from-blue-500 to-purple-600 relative rounded-t-lg">
                    <div className="absolute inset-0 bg-black bg-opacity-20 rounded-t-lg" />
                    <div className="absolute top-4 left-4 flex space-x-2">
                      <Badge variant="secondary">{institution.type}</Badge>
                      {institution.verified && (
                        <Badge className="bg-green-500 text-white">Verified</Badge>
                      )}
                    </div>
                    <div className="absolute bottom-4 left-4 text-white">
                      <h3 className="text-xl font-bold mb-1">{institution.name}</h3>
                      <div className="flex items-center space-x-2 text-sm opacity-90">
                        <MapPin className="w-4 h-4" />
                        <span>{institution.location}</span>
                      </div>
                    </div>
                  </div>
                  
                  <CardContent className="p-6 space-y-4">
                    <p className="text-gray-600 text-sm">{institution.description}</p>
                    
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <div className="flex items-center space-x-2">
                        <Users className="w-4 h-4" />
                        <span>{institution.students.toLocaleString()} students</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                        <span>{institution.rating}</span>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Popular Programs</h4>
                      <div className="flex flex-wrap gap-1">
                        {institution.programs.slice(0, 3).map((program) => (
                          <Badge key={program} variant="outline" className="text-xs">
                            {program}
                          </Badge>
                        ))}
                        {institution.programs.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{institution.programs.length - 3} more
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      <Link to={`/institutions/${institution.id}`} className="flex-1">
                        <Button variant="outline" className="w-full">
                          View Details
                        </Button>
                      </Link>
                      <Button className="flex-1 bg-blue-600 hover:bg-blue-700">
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Visit
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {filteredInstitutions.length === 0 && (
              <Card>
                <CardContent className="p-12 text-center">
                  <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No institutions found</h3>
                  <p className="text-gray-600">Try adjusting your search criteria</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Institutions;
