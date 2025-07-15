
import React from 'react';
import { Link } from 'react-router-dom';
import { Users } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Logo & Description */}
          <div className="col-span-1 md:col-span-2">
            <Link to="/dashboard" className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Users className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl text-gray-900">CampusConnect</span>
            </Link>
            <p className="text-gray-600 text-sm max-w-md">
              Connect with fellow students, join study groups, discover events, and enhance your academic journey.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Quick Links</h3>
            <div className="space-y-2">
              <Link to="/dashboard" className="block text-sm text-gray-600 hover:text-blue-600 transition-colors">
                Feed
              </Link>
              <Link to="/courses" className="block text-sm text-gray-600 hover:text-blue-600 transition-colors">
                Courses
              </Link>
              <Link to="/events" className="block text-sm text-gray-600 hover:text-blue-600 transition-colors">
                Events
              </Link>
              <Link to="/study-groups" className="block text-sm text-gray-600 hover:text-blue-600 transition-colors">
                Study Groups
              </Link>
            </div>
          </div>

          {/* Support */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Support</h3>
            <div className="space-y-2">
              <Link to="/help" className="block text-sm text-gray-600 hover:text-blue-600 transition-colors">
                Help Center
              </Link>
              <Link to="/contact" className="block text-sm text-gray-600 hover:text-blue-600 transition-colors">
                Contact Us
              </Link>
              <Link to="/privacy" className="block text-sm text-gray-600 hover:text-blue-600 transition-colors">
                Privacy Policy
              </Link>
              <Link to="/terms" className="block text-sm text-gray-600 hover:text-blue-600 transition-colors">
                Terms of Service
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200">
          <p className="text-center text-sm text-gray-500">
            © {new Date().getFullYear()} CampusConnect. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
