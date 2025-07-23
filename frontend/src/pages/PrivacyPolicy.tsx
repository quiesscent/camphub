
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Navigation from "@/components/Navigation";
import { Shield, BookOpen, Users, Lock, Eye, FileText } from "lucide-react";

const PrivacyPolicy = () => {
  const sections = [
    {
      id: "information-collection",
      title: "Information We Collect",
      icon: FileText,
      content: [
        {
          subtitle: "Account Information",
          text: "When you create an account, we collect your name, email address, profile picture, and educational background to personalize your learning experience."
        },
        {
          subtitle: "Learning Data",
          text: "We track your course progress, quiz scores, assignment submissions, time spent on lessons, and learning preferences to provide personalized recommendations and track your educational journey."
        },
        {
          subtitle: "Technical Information",
          text: "We collect device information, IP addresses, browser type, and usage analytics to improve platform performance and security."
        },
        {
          subtitle: "Communication Data",
          text: "Messages sent through our platform, discussion forum posts, and interactions with instructors are stored to maintain your learning history."
        }
      ]
    },
    {
      id: "how-we-use",
      title: "How We Use Your Information",
      icon: BookOpen,
      content: [
        {
          subtitle: "Educational Services",
          text: "We use your data to provide courses, track progress, generate certificates, and create personalized learning paths tailored to your goals."
        },
        {
          subtitle: "Learning Analytics",
          text: "Your learning data helps us understand how students learn best, improve course content, and provide insights to instructors about class performance."
        },
        {
          subtitle: "Communication",
          text: "We send course updates, assignment reminders, achievement notifications, and important platform announcements to support your learning journey."
        },
        {
          subtitle: "Platform Improvement",
          text: "Anonymous usage data helps us enhance features, fix bugs, and develop new educational tools and resources."
        }
      ]
    },
    {
      id: "data-sharing",
      title: "Data Sharing and Disclosure",
      icon: Users,
      content: [
        {
          subtitle: "Instructors and Educators",
          text: "Course instructors can see your progress, assignments, grades, and participation in their courses to provide effective teaching and feedback."
        },
        {
          subtitle: "Educational Institutions",
          text: "If you're enrolled through a school or organization, we may share progress reports and completion status with authorized educational administrators."
        },
        {
          subtitle: "Service Providers",
          text: "We work with trusted partners for payment processing, email delivery, video hosting, and analytics services under strict data protection agreements."
        },
        {
          subtitle: "Legal Requirements",
          text: "We may disclose information when required by law, to protect our users' safety, or to investigate potential violations of our terms of service."
        }
      ]
    },
    {
      id: "data-security",
      title: "Data Security and Protection",
      icon: Lock,
      content: [
        {
          subtitle: "Encryption and Security",
          text: "All data is encrypted in transit and at rest. We use industry-standard security measures including secure servers, firewalls, and regular security audits."
        },
        {
          subtitle: "Access Controls",
          text: "Only authorized personnel have access to user data, and all access is logged and monitored. We implement role-based access controls throughout our systems."
        },
        {
          subtitle: "Data Backup",
          text: "Your learning progress and course materials are regularly backed up to prevent data loss and ensure continuity of your educational experience."
        },
        {
          subtitle: "Incident Response",
          text: "We have procedures in place to detect, respond to, and notify users of any security incidents that may affect their personal information."
        }
      ]
    },
    {
      id: "student-rights",
      title: "Student Rights and Control",
      icon: Eye,
      content: [
        {
          subtitle: "Access Your Data",
          text: "You can view, download, and export your learning data, including course progress, certificates, and personal information through your account settings."
        },
        {
          subtitle: "Data Correction",
          text: "You can update your profile information, learning preferences, and contact details at any time through your account dashboard."
        },
        {
          subtitle: "Learning Privacy",
          text: "You can control what information is visible to other students and instructors, and manage your privacy settings for discussions and social features."
        },
        {
          subtitle: "Account Deletion",
          text: "You can delete your account at any time. We will remove your personal information while preserving anonymized learning analytics for educational research."
        }
      ]
    },
    {
      id: "cookies-tracking",
      title: "Cookies and Tracking",
      icon: Shield,
      content: [
        {
          subtitle: "Learning Cookies",
          text: "We use cookies to remember your login status, course progress, and preferences to provide a seamless learning experience across sessions."
        },
        {
          subtitle: "Analytics Cookies",
          text: "These help us understand how students use our platform, which features are most helpful, and where we can improve the learning experience."
        },
        {
          subtitle: "Third-Party Tools",
          text: "We may use educational technology partners for video playback, interactive content, and learning analytics, each with their own privacy practices."
        },
        {
          subtitle: "Cookie Management",
          text: "You can manage cookie preferences through your browser settings, though some features may not work properly with cookies disabled."
        }
      ]
    }
  ];

  return (
    <div className="min-h-screen sided via-white to-purple-50">
      <Navigation  />
      
      <div className=" mt-5 p-7 shape  bg-gray-50 ">
        <div className="text-center  mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Privacy Policy
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            We're committed to protecting your privacy and ensuring your learning data is secure and used responsibly.
          </p>
          <p className="text-sm text-gray-500 mt-4">
            Last updated: January 2024
          </p>
        </div>

        <div className="space-y-8 ">
          <Card className="bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-blue-800">
                <Shield className="w-6 h-6" />
                Our Commitment to Student Privacy
              </CardTitle>
              <CardDescription className="text-blue-700">
                As an educational platform, we understand the importance of protecting student data and maintaining trust in the learning environment. This policy explains how we collect, use, and protect your information to provide the best possible learning experience.
              </CardDescription>
            </CardHeader>
          </Card>

          {sections.map((section) => (
            <Card key={section.id} id={section.id}>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <section.icon className="w-4 h-4 text-blue-600" />
                  </div>
                  {section.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {section.content.map((item, index) => (
                  <div key={index}>
                    <h4 className="font-semibold text-gray-900 mb-2">
                      {item.subtitle}
                    </h4>
                    <p className="text-gray-600 leading-relaxed">
                      {item.text}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}

          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-green-800">FERPA Compliance</CardTitle>
              <CardDescription className="text-green-700">
                For educational institutions in the United States, we maintain compliance with the Family Educational Rights and Privacy Act (FERPA), ensuring that student educational records are properly protected and that students have appropriate rights regarding their educational information.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Contact Us About Privacy</CardTitle>
              <CardDescription>
                If you have questions about this privacy policy or how we handle your learning data, please don't hesitate to reach out.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-2">Privacy Officer</h4>
                  <p className="text-gray-600 mb-1">privacy@learningplatform.com</p>
                  <p className="text-gray-600">1-800-PRIVACY (1-800-774-8229)</p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Student Data Protection</h4>
                  <p className="text-gray-600 mb-1">studentdata@learningplatform.com</p>
                  <p className="text-gray-600">Available Monday-Friday, 9 AM - 6 PM EST</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;