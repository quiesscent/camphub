
import { Card, CardContent } from "@/components/ui/card";
import Navigation from "@/components/Navigation";
import { FileText, Users, Shield, AlertTriangle, Scale, CreditCard } from "lucide-react";

const TermsAndConditions = () => {
  const lastUpdated = "January 1, 2024";

  const sections = [
    {
      icon: Users,
      title: "Acceptance of Terms",
      content: [
        "By accessing and using our services, you accept and agree to be bound by these terms",
        "If you do not agree to these terms, you may not use our services",
        "These terms apply to all visitors, users, and customers",
        "We may modify these terms at any time with notice",
        "Continued use after changes constitutes acceptance of new terms"
      ]
    },
    {
      icon: Shield,
      title: "User Responsibilities",
      content: [
        "You must provide accurate and complete information",
        "You are responsible for maintaining the security of your account",
        "You must not use our services for illegal or unauthorized purposes",
        "You must respect the intellectual property rights of others",
        "You must not attempt to interfere with or disrupt our services"
      ]
    },
    {
      icon: CreditCard,
      title: "Payment Terms",
      content: [
        "All fees are due in advance and non-refundable unless otherwise stated",
        "We reserve the right to change our pricing with 30 days notice",
        "Failed payments may result in service suspension",
        "You are responsible for all taxes related to your use of our services",
        "Refunds are processed according to our refund policy"
      ]
    },
    {
      icon: AlertTriangle,
      title: "Prohibited Uses",
      content: [
        "Violating any applicable laws or regulations",
        "Transmitting harmful, offensive, or inappropriate content",
        "Attempting to gain unauthorized access to our systems",
        "Using our services to spam or send unsolicited communications",
        "Reverse engineering or attempting to extract source code"
      ]
    },
    {
      icon: Scale,
      title: "Limitation of Liability",
      content: [
        "Our services are provided 'as is' without warranties of any kind",
        "We are not liable for any indirect, incidental, or consequential damages",
        "Our total liability is limited to the amount you paid for our services",
        "We do not guarantee uninterrupted or error-free service",
        "You use our services at your own risk"
      ]
    }
  ];

  return (
    <div className="min-h-screen sided via-white to-purple-50">
      <Navigation />
      
      <div className=" shape mt-7 bg-gray-50 ">
        <div className="text-center mb-12">
          <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <FileText className="w-8 h-8 text-orange-600" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Terms & Conditions
          </h1>
          <p className="text-xl text-gray-600 mb-4">
            Please read these terms carefully before using our services. They govern your use of our platform.
          </p>
          <p className="text-sm text-gray-500">
            Last updated: {lastUpdated}
          </p>
        </div>

        <Card className="mb-8">
          <CardContent className="p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Agreement Overview</h2>
            <div className="prose prose-gray max-w-none">
              <p className="text-gray-600 mb-4">
                These Terms and Conditions ("Terms") govern your use of our website and services operated by Your Company. 
                These Terms apply to all visitors, users, and others who access or use our services.
              </p>
              <p className="text-gray-600 mb-4">
                By accessing or using our services, you agree to be bound by these Terms. If you disagree with any part of these terms, 
                then you may not access our services.
              </p>
              <p className="text-gray-600">
                We reserve the right to update or modify these Terms at any time without prior notice. 
                Your continued use of our services following any changes constitutes acceptance of those changes.
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          {sections.map((section, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-8">
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <section.icon className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      {section.title}
                    </h2>
                    <ul className="space-y-3">
                      {section.content.map((item, itemIndex) => (
                        <li key={itemIndex} className="flex items-start gap-3">
                          <div className="w-2 h-2 bg-orange-600 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-gray-600">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="mt-8">
          <CardContent className="p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Intellectual Property</h2>
            <div className="prose prose-gray max-w-none">
              <p className="text-gray-600 mb-4">
                Our services and their original content, features, and functionality are and will remain the exclusive property of Your Company and its licensors. 
                The services are protected by copyright, trademark, and other laws.
              </p>
              <p className="text-gray-600 mb-4">
                You may not duplicate, copy, or reuse any portion of the HTML/CSS, JavaScript, or visual design elements without express written permission from us.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-8">
          <CardContent className="p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Service Availability</h2>
            <div className="prose prose-gray max-w-none">
              <p className="text-gray-600 mb-4">
                We strive to maintain high service availability, but we do not guarantee that our services will be available 100% of the time. 
                Our services may be temporarily unavailable due to maintenance, updates, or technical issues.
              </p>
              <p className="text-gray-600">
                We reserve the right to modify, suspend, or discontinue our services at any time, with or without notice.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-8">
          <CardContent className="p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Account Termination</h2>
            <div className="prose prose-gray max-w-none">
              <p className="text-gray-600 mb-4">
                We may terminate or suspend your account and access to our services immediately, without prior notice or liability, 
                for any reason whatsoever, including but not limited to a breach of these Terms.
              </p>
              <p className="text-gray-600 mb-4">
                Upon termination, your right to use our services will cease immediately. If you wish to terminate your account, 
                you may simply discontinue using our services.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-8">
          <CardContent className="p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Governing Law</h2>
            <div className="prose prose-gray max-w-none">
              <p className="text-gray-600 mb-4">
                These Terms shall be interpreted and governed by the laws of the State/Country, without regard to its conflict of law provisions. 
                Our failure to enforce any right or provision of these Terms will not be considered a waiver of those rights.
              </p>
              <p className="text-gray-600">
                Any disputes arising under these Terms will be resolved through binding arbitration in accordance with the rules of the American Arbitration Association.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-8 bg-orange-50 border-orange-200">
          <CardContent className="p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Questions About These Terms?</h2>
            <p className="text-gray-600 mb-4">
              If you have any questions about these Terms and Conditions, please contact us:
            </p>
            <div className="space-y-2 text-gray-600">
              <p>Email: legal@yourcompany.com</p>
              <p>Phone: +1 (555) 123-4567</p>
              <p>Address: 123 Business Street, Suite 100, City, State 12345</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TermsAndConditions;