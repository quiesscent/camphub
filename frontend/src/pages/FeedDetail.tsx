
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Heart, MessageCircle, Share, Bookmark, MoreHorizontal } from 'lucide-react';
import Navigation from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import CommentsDropdown from '@/components/CommentsDropdown';

const FeedDetail = () => {
  const { id } = useParams();
  const [newComment, setNewComment] = useState('');
  const [comments, setComments] = useState([
    {
      id: 1,
      author: 'Sarah Johnson',
      avatar: '/placeholder.svg',
      content: 'This is really helpful! Thanks for sharing your notes.',
      timestamp: '2 hours ago',
      likes: 3,
      isLiked: false
    },
    {
      id: 2,
      author: 'Mike Chen',
      avatar: '/placeholder.svg',
      content: 'I had the same question about linear algebra. Your explanation is perfect!',
      timestamp: '1 hour ago',
      likes: 1,
      isLiked: true
    },
    {
      id: 3,
      author: 'Emma Davis',
      avatar: '/placeholder.svg',
      content: 'Could you share more examples? I\'m still struggling with this concept.',
      timestamp: '45 minutes ago',
      likes: 2,
      isLiked: false
    }
  ]);

  const post = {
    id: 1,
    author: 'Alex Rivera',
    avatar: '/placeholder.svg',
    timestamp: '3 hours ago',
    content: 'Just finished my Linear Algebra study session! Here are some key concepts that helped me understand vector spaces better. Feel free to ask questions if you need clarification on any of these topics.',
    image: '/placeholder.svg',
    likes: 24,
    isLiked: false,
    shares: 5,
    isBookmarked: false
  };

  const [postState, setPostState] = useState(post);

  const handleLike = () => {
    setPostState(prev => ({
      ...prev,
      isLiked: !prev.isLiked,
      likes: prev.isLiked ? prev.likes - 1 : prev.likes + 1
    }));
  };

  const handleBookmark = () => {
    setPostState(prev => ({
      ...prev,
      isBookmarked: !prev.isBookmarked
    }));
  };

  const handleSubmitComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (newComment.trim()) {
      const comment = {
        id: comments.length + 1,
        author: 'You',
        avatar: '/placeholder.svg',
        content: newComment,
        timestamp: 'Just now',
        likes: 0,
        isLiked: false
      };
      setComments([...comments, comment]);
      setNewComment('');
    }
  };

  const handleLikeComment = (commentId: number) => {
    setComments(comments.map(comment => 
      comment.id === commentId 
        ? { ...comment, isLiked: !comment.isLiked, likes: comment.isLiked ? comment.likes - 1 : comment.likes + 1 }
        : comment
    ));
  };

  return (
    <div className="min-h-screen bg-gray-50">

      <div>

        

      </div>

      <Navigation />
      
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Main Post */}
        <Card className="mb-8">
          <CardContent className="p-6">
            {/* Post Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <Avatar>
                  <AvatarFallback>{postState.author.charAt(0)}</AvatarFallback>
                </Avatar>
                <div>
                  <h3 className="font-semibold text-gray-900">{postState.author}</h3>
                  <p className="text-sm text-gray-500">{postState.timestamp}</p>
                </div>
              </div>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </div>

            {/* Post Content */}
            <div className="mb-4">
              <p className="text-gray-700 mb-4">{postState.content}</p>
              {postState.image && (
                <div className="rounded-lg overflow-hidden">
                  <img 
                    src={postState.image} 
                    alt="Post content" 
                    className="w-full h-64 object-cover"
                  />
                </div>
              )}
            </div>

            {/* Post Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
              <div className="flex items-center space-x-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLike}
                  className={`${postState.isLiked ? 'text-red-500' : 'text-gray-600'} hover:text-red-500`}
                >
                  <Heart className={`w-4 h-4 mr-1 ${postState.isLiked ? 'fill-current' : ''}`} />
                  {postState.likes}
                </Button>
                
                <span className="text-gray-600 flex items-center">
                  <MessageCircle className="w-4 h-4 mr-1" />
                  {comments.length}
                </span>
                
                <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
                  <Share className="w-4 h-4 mr-1" />
                  {postState.shares}
                </Button>
              </div>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBookmark}
                className={`${postState.isBookmarked ? 'text-blue-500' : 'text-gray-600'} hover:text-blue-500`}
              >
                <Bookmark className={`w-4 h-4 ${postState.isBookmarked ? 'fill-current' : ''}`} />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Comments Section */}
        <Card>
          <CardContent className="p-6">
            <h3 className="font-semibold text-lg mb-4">Comments ({comments.length})</h3>
            
            {/* Add Comment Form */}
            <form onSubmit={handleSubmitComment} className="mb-6">
              <div className="flex space-x-3">
                <Avatar className="w-8 h-8">
                  <AvatarFallback>Y</AvatarFallback>
                </Avatar>
                <div className="flex-1 flex space-x-2">
                  <Input
                    placeholder="Write a comment..."
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    className="flex-1"
                  />
                  <Button type="submit" disabled={!newComment.trim()}>
                    Post
                  </Button>
                </div>
              </div>
            </form>

            {/* Comments List */}
            <div className="space-y-6">
              {comments.map((comment) => (
                <div key={comment.id} className="flex space-x-3">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback>{comment.author.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm">{comment.author}</span>
                        <span className="text-xs text-gray-500">{comment.timestamp}</span>
                      </div>
                      <p className="text-gray-700">{comment.content}</p>
                    </div>
                    <div className="flex items-center mt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-xs text-gray-500 hover:text-red-500 p-1"
                        onClick={() => handleLikeComment(comment.id)}
                      >
                        <Heart className={`w-3 h-3 mr-1 ${comment.isLiked ? 'fill-red-500 text-red-500' : ''}`} />
                        {comment.likes}
                      </Button>
                      <Button variant="ghost" size="sm" className="text-xs text-gray-500 p-1 ml-2">
                        Reply
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FeedDetail;
