
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Heart, MessageCircle, Star, MapPin, Calendar, Shield, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const MarketplaceItem = () => {
  const { id } = useParams();
  const [isFavorited, setIsFavorited] = useState(false);
  const [inquiryMessage, setInquiryMessage] = useState('');
  const [showInquiryForm, setShowInquiryForm] = useState(false);

  const item = {
    id: 1,
    title: 'Calculus Textbook - 8th Edition',
    category: 'Textbooks',
    price: 45,
    originalPrice: 250,
    condition: 'Good',
    seller: 'Sarah Johnson',
    sellerRating: 4.8,
    sellerReviews: 24,
    location: 'Campus',
    description: 'Barely used calculus textbook. No highlighting or writing inside. Perfect for Calc I and II courses. Includes access code for online resources (unused). This is the latest edition required for most university courses.',
    images: ['/study.jpg', '/study.jpg', '/study.jpg'],
    postedDate: '2 days ago',
    views: 45,
    specifications: {
      'ISBN': '978-1-285-74621-1',
      'Edition': '8th Edition',
      'Author': 'James Stewart',
      'Publisher': 'Cengage Learning',
      'Year': '2020'
    }
  };

  const relatedItems = [
    {
      id: 2,
      title: 'Linear Algebra Textbook',
      price: 35,
      image: '/study.jpg',
      condition: 'Good'
    },
    {
      id: 3,
      title: 'Scientific Calculator',
      price: 25,
      image: '/study.jpg',
      condition: 'Excellent'
    }
  ];

  const getConditionColor = (condition: string) => {
    switch (condition) {
      case 'Like New': return 'bg-green-100 text-green-800';
      case 'Excellent': return 'bg-blue-100 text-blue-800';
      case 'Good': return 'bg-yellow-100 text-yellow-800';
      case 'Fair': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleInquiry = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Inquiry sent:', inquiryMessage);
    setInquiryMessage('');
    setShowInquiryForm(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Navigation */}
        <div className="mb-6">
          <Link to="/marketplace">
            <Button variant="ghost" className="text-gray-600 hover:text-gray-900">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Marketplace
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Image Gallery */}
            <Card className="mb-6">
              <CardContent className="p-0">
                <div className="aspect-video bg-gray-200 rounded-t-lg overflow-hidden">
                  <img 
                    src={item.images[0]} 
                    alt={item.title}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-4">
                  <div className="flex space-x-2 overflow-x-auto">
                    {item.images.map((image, index) => (
                      <div key={index} className="flex-shrink-0 w-16 h-16 bg-gray-200 rounded-lg overflow-hidden">
                        <img 
                          src={image} 
                          alt={`${item.title} ${index + 1}`}
                          className="w-full h-full object-cover cursor-pointer hover:opacity-80"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Item Details */}
            <Card className="mb-6">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-2xl mb-2">{item.title}</CardTitle>
                    <div className="flex items-center space-x-2 mb-2">
                      <Badge variant="outline">{item.category}</Badge>
                      <Badge className={getConditionColor(item.condition)}>
                        {item.condition}
                      </Badge>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsFavorited(!isFavorited)}
                    className={`${isFavorited ? 'text-red-500' : 'text-gray-500'} hover:text-red-500`}
                  >
                    <Heart className={`w-5 h-5 ${isFavorited ? 'fill-current' : ''}`} />
                  </Button>
                </div>
                
                <div className="flex items-baseline space-x-3">
                  <span className="text-3xl font-bold text-blue-600">${item.price}</span>
                  {item.originalPrice && (
                    <span className="text-lg text-gray-500 line-through">
                      ${item.originalPrice}
                    </span>
                  )}
                  {item.originalPrice && (
                    <Badge className="bg-green-100 text-green-800">
                      Save {Math.round((1 - item.price / item.originalPrice) * 100)}%
                    </Badge>
                  )}
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Description</h3>
                    <p className="text-gray-700">{item.description}</p>
                  </div>

                  {item.specifications && (
                    <div>
                      <h3 className="font-semibold mb-2">Specifications</h3>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        {Object.entries(item.specifications).map(([key, value]) => (
                          <div key={key}>
                            <span className="text-gray-600">{key}:</span>
                            <span className="ml-2 font-medium">{value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center space-x-4 text-sm text-gray-600 pt-4 border-t">
                    <div className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>Posted {item.postedDate}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span>{item.views} views</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Seller Info */}
            <Card>
              <CardHeader>
                <CardTitle>Seller Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-3 mb-4">
                  <Avatar className="w-12 h-12">
                    <AvatarFallback>{item.seller.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <div>
                    <h4 className="font-semibold">{item.seller}</h4>
                    <div className="flex items-center space-x-1 text-sm text-gray-600">
                      <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                      <span>{item.sellerRating}</span>
                      <span>({item.sellerReviews} reviews)</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2 text-sm text-gray-600 mb-4">
                  <MapPin className="w-4 h-4" />
                  <span>{item.location}</span>
                </div>

                <div className="flex items-center space-x-2 text-sm text-green-600 mb-4">
                  <Shield className="w-4 h-4" />
                  <span>Verified Student</span>
                </div>

                <div className="space-y-2">
                  <Button 
                    className="w-full bg-blue-600 hover:bg-blue-700"
                    onClick={() => setShowInquiryForm(!showInquiryForm)}
                  >
                    <MessageCircle className="w-4 h-4 mr-2" />
                    Send Inquiry
                  </Button>
                  <Button variant="outline" className="w-full">
                    View Profile
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Inquiry Form */}
            {showInquiryForm && (
              <Card>
                <CardHeader>
                  <CardTitle>Send Inquiry</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleInquiry} className="space-y-4">
                    <div>
                      <Label htmlFor="message">Message</Label>
                      <textarea
                        id="message"
                        className="w-full p-3 border border-gray-300 rounded-md"
                        rows={4}
                        placeholder="Hi! I'm interested in your textbook. Is it still available?"
                        value={inquiryMessage}
                        onChange={(e) => setInquiryMessage(e.target.value)}
                        required
                      />
                    </div>
                    <Button type="submit" className="w-full">
                      Send Message
                    </Button>
                  </form>
                </CardContent>
              </Card>
            )}

            {/* Safety Tips */}
            <Card>
              <CardHeader>
                <CardTitle>Safety Tips</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-gray-600 space-y-2">
                <p>• Meet in a public place on campus</p>
                <p>• Inspect the item before purchasing</p>
                <p>• Use secure payment methods</p>
                <p>• Trust your instincts</p>
              </CardContent>
            </Card>

            {/* Related Items */}
            <Card>
              <CardHeader>
                <CardTitle>Related Items</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {relatedItems.map((relatedItem) => (
                    <Link key={relatedItem.id} to={`/marketplace/${relatedItem.id}`}>
                      <div className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                        <div className="w-12 h-12 bg-gray-200 rounded-lg overflow-hidden">
                          <img 
                            src={relatedItem.image} 
                            alt={relatedItem.title}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{relatedItem.title}</p>
                          <p className="text-sm text-blue-600">${relatedItem.price}</p>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketplaceItem;
