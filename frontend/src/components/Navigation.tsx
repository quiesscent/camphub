import React from 'react'
import { ArrowLeft } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bell,
  MessageCircle,
  Search,
  User,
  Calendar,
  MapPin,
  Users,
  Book,
  Menu,
  X,
  
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const Navigation = () => {
  /* const [open, setOpen] = useState(false); */

  
 /*  const location = useLocation(); */
  const [showSecondaryNav, setShowSecondaryNav] = useState(false);

  const isActive = (path) => location.pathname === path;

  const mainNavItems = [
    { path: "/dashboard", label: "Feed", icon: Users },
    { path: "/messages", label: "Messages", icon: MessageCircle },
    { path: "/study-groups", label: "Study Groups", icon: Users },
    { path: "/notifications", label: "Notifications", icon: Bell },
     { path: "/courses", label: "Courses", icon: Book },
    { path: "/events", label: "Events", icon: Calendar },
    { path: "/marketplace", label: "Marketplace", icon: MapPin },
    { path: "/institutions", label: "Institutions", icon: Book },
  ];

 


  return (
    <div  >
      <div className='h-full w-42 mt-10 relative bg-white text-white   '>
      {/*   <ArrowLeft className='absolute cursor-pointer rounded-full -right-3 top-9 w-7 border-2 border-[#082A51] bg-white text-black 
'
onClick={() => setOpen(!open)}
 /> */}
      <div className="p-4  flex justify-between items-center">
          <Link to="/dashboard" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Users className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl text-black">
              CampusConnect
            </span>
          </Link>
          </div > 

          
        <div className="flex flex-col gap-4 mt-15 items-start  space-x-1">
          {mainNavItems.slice(0, 10).map((item) => (
            <Link key={item.path} to={item.path}>
              <Button
                variant={isActive(item.path) ? "default" : "ghost"}
                className={`relative ${
                  isActive(item.path)
                    ? "bg-blue-100 text-blue-700 hover:bg-blue-200"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                <item.icon className="w-4 h-4 " />
                {item.label}
                {item.label === "Messages" && (
                  <Badge className="ml-2 bg-red-500 text-white text-xs px-1.5 py-0.5">
                    3
                  </Badge>
                )}
                

              </Button>
            </Link>
          ))}

         
        </div>

         <div className="border-t border-gray-200 pt-4 mt-39">
          <Link to="/profile">
            <div className="flex items-start ">
              <div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="flex items-center space-x-2"
                >
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                </Button>
              </div>

              <div className="flex justify-center items-center  ml-3">
                <div className="leading-4">
                  <h4 className="font-semibold text-black">John Doe</h4>
                  <span className="text-xs text-gray-600">
                    johndoe.email.com
                  </span>
                </div>
              </div>
            </div>
          </Link>
          </div>

      </div>
  
    </div>
  )
}

export default Navigation