"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Cookies from "js-cookie";
import { motion } from "framer-motion";
import { FiSearch, FiStar, FiUsers, FiBookOpen, FiAward, FiTrendingUp, FiCheck, FiArrowRight } from "react-icons/fi";
import { tutors, subjects, auth } from "@/lib/api";
import { TutorPublicSummary, Subject, User } from "@/types";
import TutorCard from "@/components/TutorCard";
import LoadingSpinner from "@/components/LoadingSpinner";
import Button from "@/components/Button";
import PublicHeader from "@/components/PublicHeader";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export default function HomePage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [featuredTutors, setFeaturedTutors] = useState<TutorPublicSummary[]>([]);
  const [subjectsList, setSubjectsList] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const token = Cookies.get("token");
    
    const loadData = async () => {
      try {
        if (token) {
          const user = await auth.getCurrentUser();
          setCurrentUser(user);
        }
        
        const [tutorsList, subjectsData] = await Promise.all([
          tutors.list({ sort_by: "rating", page_size: 6 }),
          subjects.list()
        ]);

        setFeaturedTutors(tutorsList.items);
        setSubjectsList(subjectsData);
      } catch (error) {
        console.error("Error loading homepage data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleSearch = () => {
    if (searchQuery.trim()) {
      router.push(`/tutors?search=${encodeURIComponent(searchQuery)}`);
    } else {
      router.push("/tutors");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-200 flex flex-col">
      {/* Navigation Header */}
      {currentUser ? <Navbar user={currentUser} /> : <PublicHeader />}

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="container mx-auto px-4 py-16 md:py-24 max-w-7xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center lg:text-left relative z-10"
            >
              {/* Gradient Blur Background */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 lg:left-0 lg:translate-x-0 w-[300px] h-[300px] bg-emerald-400/20 rounded-full blur-[80px] -z-10" />
              
              {/* Trust Badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-300 text-xs font-bold mb-6 border border-emerald-200 dark:border-emerald-800">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Over 30,000 trusted tutors
              </div>

              {/* Main Heading */}
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-black text-slate-900 dark:text-white mb-6 tracking-tight leading-[1.1]">
                Find the <span className="text-emerald-600 dark:text-emerald-400">perfect tutor</span> for your goals
              </h1>
              
              {/* Subheading */}
              <p className="text-lg text-slate-600 dark:text-slate-400 max-w-xl mx-auto lg:mx-0 mb-8 leading-relaxed">
                Book 1-on-1 lessons with verified experts. Master any subject from the comfort of your home.
              </p>

              {/* Search Bar */}
              <div className="max-w-xl mx-auto lg:mx-0 mb-8">
                <div className="flex gap-2 bg-white dark:bg-slate-900 rounded-2xl p-2 shadow-xl border border-slate-200 dark:border-slate-800">
                  <input
                    type="text"
                    placeholder="What do you want to learn?"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                    className="flex-1 px-4 py-3 bg-transparent text-slate-900 dark:text-white rounded-xl focus:outline-none placeholder-slate-400 dark:placeholder-slate-500"
                  />
                  <Button
                    onClick={handleSearch}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3 rounded-xl"
                  >
                    <FiSearch className="w-5 h-5" />
                  </Button>
                </div>
              </div>

              {/* Subject Pills */}
              <div className="flex flex-wrap justify-center lg:justify-start gap-2">
                {['English', 'Mathematics', 'Spanish', 'Physics', 'Piano', 'Computer Science'].map((topic) => (
                  <button
                    key={topic}
                    onClick={() => router.push(`/tutors?search=${encodeURIComponent(topic)}`)}
                    className="px-4 py-2 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-sm font-bold hover:border-emerald-500 hover:text-emerald-600 dark:hover:text-emerald-400 dark:hover:border-emerald-500 transition-all shadow-sm active:scale-95"
                  >
                    {topic}
                  </button>
                ))}
              </div>

              {/* CTA Buttons */}
              {!currentUser && (
                <div className="flex flex-wrap gap-4 justify-center lg:justify-start mt-8">
                  <Button
                    onClick={() => router.push("/register")}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-4 rounded-xl font-bold text-lg shadow-lg shadow-emerald-500/20"
                  >
                    Get Started Free
                  </Button>
                  <Button
                    onClick={() => router.push("/tutors")}
                    variant="outline"
                    className="px-8 py-4 rounded-xl font-bold text-lg"
                  >
                    Browse Tutors
                  </Button>
                </div>
              )}
              
              {currentUser && (
                <Button
                  onClick={() => router.push(currentUser.role === 'admin' ? '/admin' : '/dashboard')}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-4 rounded-xl font-bold text-lg mt-8"
                >
                  Go to Dashboard <FiArrowRight className="w-5 h-5" />
                </Button>
              )}
            </motion.div>

            {/* Right Image with Floating Cards */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative hidden lg:block h-[500px]"
            >
              {/* Background Gradient Shape */}
              <div className="absolute inset-0 bg-gradient-to-tr from-emerald-100 to-blue-100 dark:from-emerald-900/20 dark:to-blue-900/20 rounded-[40px] transform rotate-3 scale-95" />
              
              {/* Main Image */}
              <Image 
                src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=1000&auto=format&fit=crop" 
                alt="Students learning together" 
                width={1000}
                height={667}
                className="relative rounded-[40px] shadow-2xl w-full h-full object-cover border-8 border-white dark:border-slate-800 transform -rotate-2 hover:rotate-0 transition-transform duration-700"
                unoptimized
              />
              
              {/* Floating Card - Bottom Left: Satisfaction Guaranteed */}
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 }}
                className="absolute -bottom-8 -left-8 bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700 flex items-center gap-4"
              >
                <div className="bg-emerald-100 dark:bg-emerald-900/30 p-3 rounded-full text-emerald-600 dark:text-emerald-400">
                  <FiCheck className="w-6 h-6" strokeWidth={3} />
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">Satisfaction</p>
                  <p className="text-lg font-black text-slate-900 dark:text-white">Guaranteed</p>
                </div>
              </motion.div>

              {/* Floating Card - Top Right: Average Rating */}
              <motion.div 
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.8 }}
                className="absolute top-12 -right-8 bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700"
              >
                <div className="flex items-center gap-1 text-amber-400 mb-1">
                  {[1,2,3,4,5].map(i => (
                    <FiStar key={i} className="w-4 h-4 fill-current" />
                  ))}
                </div>
                <p className="text-sm font-bold text-slate-900 dark:text-white">4.9/5 Average Rating</p>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white dark:bg-slate-900 border-y border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { icon: FiUsers, label: "Expert Tutors", value: "1,000+" },
              { icon: FiBookOpen, label: "Subjects", value: subjectsList.length.toString() || "50+" },
              { icon: FiStar, label: "Avg Rating", value: "4.9" },
              { icon: FiAward, label: "Sessions", value: "50k+" }
            ].map((stat, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * idx }}
                className="text-center"
              >
                <stat.icon className="w-8 h-8 text-emerald-600 dark:text-emerald-400 mx-auto mb-3" />
                <p className="text-3xl font-bold text-slate-900 dark:text-white mb-1">{stat.value}</p>
                <p className="text-slate-600 dark:text-slate-400">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Tutors */}
      {featuredTutors.length > 0 && (
        <section className="py-16 bg-white dark:bg-slate-900 border-y border-slate-200 dark:border-slate-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-12"
            >
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
                Top-Rated Tutors
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-400">
                Learn from the best in the field
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {featuredTutors.map((tutor) => (
                <TutorCard key={tutor.id} tutor={tutor} />
              ))}
            </div>

            <div className="text-center">
              <Button
                onClick={() => router.push("/tutors")}
                variant="primary"
                size="lg"
                className="shadow-lg shadow-emerald-500/20"
              >
                View All Tutors <FiArrowRight className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <Footer />
    </div>
  );
}
