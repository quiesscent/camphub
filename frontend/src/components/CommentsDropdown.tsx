
import React, { useState } from 'react';
import { MessageCircle, Send, Heart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';

interface Comment {
  id: number;
  author: string;
  content: string;
  timestamp: string;
  likes: number;
  isLiked: boolean;
}

interface CommentsDropdownProps {
  postId: number;
  commentCount: number;
}

const CommentsDropdown: React.FC<CommentsDropdownProps> = ({ postId, commentCount }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [comments, setComments] = useState<Comment[]>([
    {
      id: 1,
      author: 'Sarah Johnson',
      content: 'This is really helpful! Thanks for sharing.',
      timestamp: '2 hours ago',
      likes: 3,
      isLiked: false
    },
    {
      id: 2,
      author: 'Mike Chen',
      content: 'I had the same question. Great explanation!',
      timestamp: '1 hour ago',
      likes: 1,
      isLiked: true
    }
  ]);

  const handleSubmitComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (newComment.trim()) {
      const comment: Comment = {
        id: comments.length + 1,
        author: 'You',
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
    <div className="relative">
      <Button 
        variant="ghost" 
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="text-gray-600 hover:text-gray-900"
      >
        <MessageCircle className="w-4 h-4 mr-1" />
        {commentCount}
      </Button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">Comments ({comments.length})</h3>
          </div>

          <div className="max-h-64 overflow-y-auto">
            {comments.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                <MessageCircle className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                <p>No comments yet. Be the first to comment!</p>
              </div>
            ) : (
              <div className="space-y-3 p-4">
                {comments.map((comment) => (
                  <div key={comment.id} className="flex space-x-3">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback>{comment.author.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm">{comment.author}</span>
                          <span className="text-xs text-gray-500">{comment.timestamp}</span>
                        </div>
                        <p className="text-sm text-gray-700">{comment.content}</p>
                      </div>
                      <div className="flex items-center mt-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-xs text-gray-500 hover:text-red-500 p-1"
                          onClick={() => handleLikeComment(comment.id)}
                        >
                          <Heart className={`w-3 h-3 mr-1 ${comment.isLiked ? 'fill-red-500 text-red-500' : ''}`} />
                          {comment.likes}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="p-4 border-t border-gray-200">
            <form onSubmit={handleSubmitComment} className="flex space-x-2">
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
                <Button type="submit" size="sm" disabled={!newComment.trim()}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommentsDropdown;
