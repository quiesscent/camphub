
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import Footer from "./components/Footer";
import Auth from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import Courses from "./pages/Courses";
import Events from "./pages/Events";
import Profile from "./pages/Profile";
import StudyGroups from "./pages/StudyGroups";
import StudyGroupDetail from "./pages/StudyGroupDetail";
import EventDetail from "./pages/EventDetail";
import FeedDetail from "./pages/FeedDetail";
import Messages from "./pages/Messages";
import Notifications from "./pages/Notifications";
import Institutions from "./pages/Institutions";
import Marketplace from "./pages/Marketplace";
import MarketplaceItem from "./pages/MarketplaceItem";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <HashRouter>
        <div className="min-h-screen flex flex-col  ">
          <div className="flex-1 pb-16 lg:pb-0">
            <Routes>
              <Route path="/" element={<Auth />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/courses" element={<Courses />} />
              <Route path="/events" element={<Events />} />
              <Route path="/events/:id" element={<EventDetail />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/study-groups" element={<StudyGroups />} />
              <Route path="/study-groups/:id" element={<StudyGroupDetail />} />
              <Route path="/feed/:id" element={<FeedDetail />} />
              <Route path="/messages" element={<Messages />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/institutions" element={<Institutions />} />
              <Route path="/marketplace" element={<Marketplace />} />
              <Route path="/marketplace/:id" element={<MarketplaceItem />} />
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
          <Footer />
        </div>
      </HashRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
