
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import Navigation from "@/components/Navigation";
import { Search, Book, MessageCircle, Phone, Mail, HelpCircle } from "lucide-react";

const HelpCenter = () => {
  const [searchQuery, setSearchQuery] = useState("");

  const faqCategories = [
    {
      title: "Getting Started",
      icon: Book,
      questions: [
        {
          question: "How do I create an account?",
          answer: "To create an account, click the 'Sign Up' button on our homepage and fill in your details. You'll receive a confirmation email to verify your account."
        },
        {
          question: "What information do I need to provide?",
          answer: "You'll need to provide your name, email address, and create a secure password. Additional information may be required depending on your account type."
        },
        {
          question: "Is there a mobile app available?",
          answer: "Yes! Our mobile app is available for both iOS and Android devices. You can download it from the App Store or Google Play Store."
        }
      ]
    },
    {
      title: "Account & Billing",
      icon: MessageCircle,
      questions: [
        {
          question: "How do I update my payment method?",
          answer: "Go to Account Settings > Billing > Payment Methods. You can add, edit, or remove payment methods from there."
        },
        {
          question: "Can I cancel my subscription anytime?",
          answer: "Yes, you can cancel your subscription at any time from your account settings. You'll continue to have access until the end of your billing period."
        },
        {
          question: "How do I download my invoice?",
          answer: "Visit your Account Settings > Billing > Invoices to view and download all your past invoices."
        }
      ]
    },
    {
      title: "Technical Support",
      icon: HelpCircle,
      questions: [
        {
          question: "I'm experiencing technical issues. What should I do?",
          answer: "First, try refreshing your browser or restarting the app. If the issue persists, check our status page or contact our support team."
        },
        {
          question: "How do I reset my password?",
          answer: "Click 'Forgot Password' on the login page and enter your email address. You'll receive instructions to reset your password."
        },
        {
          question: "Why is the service running slowly?",
          answer: "Slow performance can be caused by various factors. Try clearing your browser cache, checking your internet connection, or using a different browser."
        }
      ]
    }
  ];

  const filteredCategories = faqCategories.map(category => ({
    ...category,
    questions: category.questions.filter(
      q => 
        q.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.answer.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.questions.length > 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Help Center
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
            Find answers to frequently asked questions and get the help you need.
          </p>
          
          <div className="max-w-md mx-auto relative">
            <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search for help..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8 mb-12">
          <Card className="text-center hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Phone className="w-6 h-6 text-blue-600" />
              </div>
              <CardTitle>Phone Support</CardTitle>
              <CardDescription>Talk to our support team directly</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">Available Mon-Fri, 9 AM - 6 PM</p>
              <Button variant="outline" className="w-full">
                Call +1 (555) 123-4567
              </Button>
            </CardContent>
          </Card>

          <Card className="text-center hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <MessageCircle className="w-6 h-6 text-green-600" />
              </div>
              <CardTitle>Live Chat</CardTitle>
              <CardDescription>Get instant help from our chat support</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">Average response time: 2 minutes</p>
              <Button variant="outline" className="w-full">
                Start Live Chat
              </Button>
            </CardContent>
          </Card>

          <Card className="text-center hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Mail className="w-6 h-6 text-purple-600" />
              </div>
              <CardTitle>Email Support</CardTitle>
              <CardDescription>Send us a detailed message</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">Response within 24 hours</p>
              <Button variant="outline" className="w-full">
                Send Email
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Frequently Asked Questions
            </h2>
            <p className="text-gray-600">
              Find quick answers to the most common questions.
            </p>
          </div>

          {filteredCategories.length > 0 ? (
            filteredCategories.map((category, categoryIndex) => (
              <Card key={categoryIndex}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                      <category.icon className="w-4 h-4 text-blue-600" />
                    </div>
                    {category.title}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Accordion type="single" collapsible className="space-y-2">
                    {category.questions.map((faq, index) => (
                      <AccordionItem key={index} value={`item-${categoryIndex}-${index}`}>
                        <AccordionTrigger className="text-left">
                          {faq.question}
                        </AccordionTrigger>
                        <AccordionContent className="text-gray-600">
                          {faq.answer}
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </CardContent>
              </Card>
            ))
          ) : searchQuery ? (
            <Card>
              <CardContent className="text-center py-12">
                <HelpCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No results found
                </h3>
                <p className="text-gray-600 mb-4">
                  We couldn't find any articles matching your search.
                </p>
                <Button variant="outline" onClick={() => setSearchQuery("")}>
                  Clear Search
                </Button>
              </CardContent>
            </Card>
          ) : null}
        </div>

        <Card className="mt-12">
          <CardHeader className="text-center">
            <CardTitle>Still need help?</CardTitle>
            <CardDescription>
              If you can't find what you're looking for, our support team is here to help.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button>Contact Support</Button>
              <Button variant="outline">Submit a Ticket</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default HelpCenter;