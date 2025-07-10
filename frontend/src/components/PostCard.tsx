
import React, { useState } from 'react';
import { Heart, MessageCircle, Share, MoreHorizontal, Pin, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface PostCardProps {
  id: string;
  author: {
    name: string;
    role: 'Student' | 'Faculty' | 'Staff' | 'Admin';
    major?: string;
    year?: string;
  };
  content: string;
  type: 'text' | 'image' | 'video' | 'document' | 'event' | 'marketplace';
  timestamp: string;
  likes: number;
  comments: number;
  shares: number;
  isPinned?: boolean;
  isAnonymous?: boolean;
  imageUrl?: string;
  tags?: string[];
}

const PostCard: React.FC<PostCardProps> = ({
  author,
  content,
  type,
  timestamp,
  likes,
  comments,
  shares,
  isPinned,
  isAnonymous,
  imageUrl,
  tags
}) => {
  const [isLiked, setIsLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(likes);

  const handleLike = () => {
    setIsLiked(!isLiked);
    setLikeCount(isLiked ? likeCount - 1 : likeCount + 1);
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'Student': return 'bg-blue-100 text-blue-800';
      case 'Faculty': return 'bg-green-100 text-green-800';
      case 'Staff': return 'bg-purple-100 text-purple-800';
      case 'Admin': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'event': return '📅';
      case 'marketplace': return '🛍️';
      case 'document': return '📄';
      case 'video': return '🎥';
      case 'image': return '🖼️';
      default: return null;
    }
  };

  return (
    <Card className="mb-4 hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Avatar className="w-10 h-10">
              <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                {isAnonymous ? '?' : author.name.split(' ').map(n => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold text-gray-900">
                  {isAnonymous ? 'Anonymous' : author.name}
                </h3>
                <Badge className={`text-xs px-2 py-1 ${getRoleColor(author.role)}`}>
                  {author.role}
                </Badge>
                {isPinned && (
                  <Pin className="w-4 h-4 text-blue-600" />
                )}
                {isAnonymous && (
                  <Eye className="w-4 h-4 text-gray-500" />
                )}
              </div>
              <p className="text-sm text-gray-500">
                {!isAnonymous && author.major && `${author.major} • `}
                {!isAnonymous && author.year && `Class of ${author.year} • `}
                {timestamp}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {getTypeIcon(type) && (
              <span className="text-lg">{getTypeIcon(type)}</span>
            )}
            <Button variant="ghost" size="sm">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="mb-4">
          <p className="text-gray-800 leading-relaxed mb-3">{content}</p>
          
          {imageUrl && (
            <div className="rounded-lg overflow-hidden mb-3">
              <img 
                src={imageUrl} 
                alt="Post content"
                className="w-full h-auto max-h-96 object-cover hover:scale-105 transition-transform duration-300"
              />
            </div>
          )}

          {tags && tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {tags.map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  #{tag}
                </Badge>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div className="flex items-center space-x-6">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLike}
              className={`flex items-center space-x-2 ${
                isLiked ? 'text-red-600 hover:text-red-700' : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
              <span>{likeCount}</span>
            </Button>
            
            <Button variant="ghost" size="sm" className="flex items-center space-x-2 text-gray-600 hover:text-gray-800">
              <MessageCircle className="w-4 h-4" />
              <span>{comments}</span>
            </Button>
            
            <Button variant="ghost" size="sm" className="flex items-center space-x-2 text-gray-600 hover:text-gray-800">
              <Share className="w-4 h-4" />
              <span>{shares}</span>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PostCard;
