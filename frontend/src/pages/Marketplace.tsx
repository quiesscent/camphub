
import React, { useState } from 'react';
import { Search, Filter, Plus, Heart, MessageCircle, Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

const Marketplace = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const items = [
    {
      id: 1,
      title: 'Calculus Textbook - 8th Edition',
      category: 'Textbooks',
      price: 45,
      originalPrice: 250,
      condition: 'Good',
      seller: 'Sarah Johnson',
      sellerRating: 4.8,
      location: 'Campus',
      description: 'Barely used calculus textbook. No highlighting or writing inside.',
      image: '/placeholder.svg',
      isFavorited: false,
      postedDate: '2 days ago'
    },
    {
      id: 2,
      title: 'MacBook Pro 13" - M1',
      category: 'Electronics',
      price: 800,
      originalPrice: 1299,
      condition: 'Excellent',
      seller: 'Mike Chen',
      sellerRating: 4.9,
      location: 'Dorm Building A',
      description: 'Like new MacBook Pro with M1 chip. Perfect for students.',
      image: '/placeholder.svg',
      isFavorited: true,
      postedDate: '1 day ago'
    },
    {
      id: 3,
      title: 'Desk Lamp - Adjustable LED',
      category: 'Furniture',
      price: 15,
      originalPrice: 35,
      condition: 'Good',
      seller: 'Emma Davis',
      sellerRating: 4.6,
      location: 'Off-campus',
      description: 'Great desk lamp for studying. Multiple brightness settings.',
      image: '/placeholder.svg',
      isFavorited: false,
      postedDate: '5 days ago'
    },
    {
      id: 4,
      title: 'Chemistry Lab Coat - Size M',
      category: 'Supplies',
      price: 20,
      originalPrice: 50,
      condition: 'Like New',
      seller: 'Alex Rivera',
      sellerRating: 4.7,
      location: 'Science Building',
      description: 'Barely used lab coat, perfect condition. Required for chem labs.',
      image: '/placeholder.svg',
      isFavorited: false,
      postedDate: '3 days ago'
    }
  ];

  const categories = ['all', 'Textbooks', 'Electronics', 'Furniture', 'Supplies', 'Clothing'];

  const getConditionColor = (condition: string) => {
    switch (condition) {
      case 'Like New': return 'bg-green-100 text-green-800';
      case 'Excellent': return 'bg-blue-100 text-blue-800';
      case 'Good': return 'bg-yellow-100 text-yellow-800';
      case 'Fair': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredItems = items.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Campus Marketplace</h1>
            <p className="text-gray-600">Buy and sell items with fellow students</p>
          </div>
          
          <Button className="mt-4 md:mt-0 bg-blue-600 hover:bg-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            Sell Item
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
                      placeholder="Search items..."
                      className="pl-10"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Category</label>
                  <div className="space-y-2">
                    {categories.map((category) => (
                      <Button
                        key={category}
                        variant={selectedCategory === category ? "default" : "ghost"}
                        className="w-full justify-start"
                        onClick={() => setSelectedCategory(category)}
                      >
                        {category === 'all' ? 'All Categories' : category}
                      </Button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Price Range</label>
                  <div className="space-y-2">
                    <Input type="number" placeholder="Min price" />
                    <Input type="number" placeholder="Max price" />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Condition</label>
                  <div className="space-y-1">
                    {['Like New', 'Excellent', 'Good', 'Fair'].map((condition) => (
                      <label key={condition} className="flex items-center space-x-2">
                        <input type="checkbox" className="rounded" />
                        <span className="text-sm">{condition}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content - Items */}
          <div className="lg:col-span-3">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredItems.map((item) => (
                <Card key={item.id} className="hover:shadow-lg transition-shadow">
                  <div className="relative">
                    <div className="h-48 bg-gray-200 rounded-t-lg overflow-hidden">
                      <img 
                        src={item.image} 
                        alt={item.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className={`absolute top-2 right-2 ${
                        item.isFavorited ? 'text-red-500' : 'text-gray-500'
                      } hover:text-red-500`}
                    >
                      <Heart className={`w-4 h-4 ${item.isFavorited ? 'fill-current' : ''}`} />
                    </Button>
                    <Badge className={getConditionColor(item.condition)} style={{position: 'absolute', top: '8px', left: '8px'}}>
                      {item.condition}
                    </Badge>
                  </div>
                  
                  <CardContent className="p-4 space-y-3">
                    <div>
                      <h3 className="font-semibold text-lg truncate">{item.title}</h3>
                      <Badge variant="outline" className="text-xs mt-1">{item.category}</Badge>
                    </div>
                    
                    <p className="text-gray-600 text-sm line-clamp-2">{item.description}</p>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-2xl font-bold text-blue-600">${item.price}</span>
                        {item.originalPrice && (
                          <span className="text-sm text-gray-500 line-through ml-2">
                            ${item.originalPrice}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <div className="flex items-center space-x-1">
                        <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                        <span>{item.sellerRating}</span>
                        <span>• {item.seller}</span>
                      </div>
                      <span>{item.postedDate}</span>
                    </div>

                    <div className="flex space-x-2">
                      <Link to={`/marketplace/${item.id}`} className="flex-1">
                        <Button variant="outline" className="w-full">
                          View Details
                        </Button>
                      </Link>
                      <Button size="sm" variant="ghost">
                        <MessageCircle className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {filteredItems.length === 0 && (
              <Card>
                <CardContent className="p-12 text-center">
                  <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No items found</h3>
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

export default Marketplace;
