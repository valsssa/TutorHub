'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import axios from 'axios'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { getApiBaseUrl } from '@/shared/utils/url'

const API_URL = getApiBaseUrl(process.env.NEXT_PUBLIC_API_URL)

export default function ReferralPage() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [loading, setLoading] = useState(true)
  const [openFaq, setOpenFaq] = useState<number | null>(0) // Default first open

  const toggleFaq = (index: number) => {
    setOpenFaq(openFaq === index ? null : index)
  }

  useEffect(() => {
    const checkAuth = async () => {
      const token = Cookies.get('token')
      if (token) {
        try {
          const response = await axios.get(`${API_URL}/users/me`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          setUser(response.data)
          setIsLoggedIn(true)
        } catch (error) {
          Cookies.remove('token')
          setIsLoggedIn(false)
        }
      } else {
        setIsLoggedIn(false)
      }
      setLoading(false)
    }

    checkAuth()
  }, [])

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 pb-20">
      {/* Hero Section */}
      <div className="bg-[#4ADE80] dark:bg-emerald-600 relative overflow-hidden">
        <div className="container mx-auto px-6 py-16 md:py-24 max-w-6xl flex flex-col md:flex-row items-center">
          {/* Left Content */}
          <div className="flex-1 z-10 md:pr-12 text-center md:text-left">
            <h1 className="text-4xl md:text-6xl font-black text-slate-900 dark:text-white mb-6 leading-tight">
              Refer a friend, <br />
              get a discount
            </h1>
            <p className="text-lg md:text-xl text-slate-800 dark:text-emerald-50 mb-8 font-medium leading-relaxed max-w-xl mx-auto md:mx-0">
              To give a friend <span className="font-bold">70% off</span> in their trial lesson, book a lesson for yourself, then return to this page to get your referral link.
              If they confirm their first subscription lesson, you'll get <span className="font-bold">$50</span>.
            </p>

            {/* Call to Action Button */}
            <button
              onClick={() => router.push('/tutors')}
              className="bg-slate-900 text-white hover:bg-slate-800 px-8 py-4 rounded-xl font-bold transition-all shadow-xl hover:shadow-2xl hover:-translate-y-1 text-lg"
            >
              Book my first lesson
            </button>
          </div>

          {/* Right Images (Collage) */}
          <div className="flex-1 relative mt-12 md:mt-0 w-full max-w-[500px] h-[400px] hidden md:block">
            {/* Photo 1: Top Left */}
            <div className="absolute top-0 left-0 z-10">
              <div className="relative">
                <img
                  src="https://images.unsplash.com/photo-1580894732444-8ecded7900cd?q=80&w=400&auto=format&fit=crop"
                  className="w-48 h-48 object-cover rounded-2xl shadow-2xl border-4 border-white transform -rotate-3 hover:rotate-0 transition-transform duration-500"
                  alt="Happy Student"
                />
                <div className="absolute -top-4 -right-8 bg-white text-slate-900 px-3 py-1.5 rounded-lg shadow-lg text-sm font-bold animate-bounce" style={{animationDuration: '3s'}}>
                  Thank you!
                  <div className="absolute bottom-0 left-2 w-3 h-3 bg-white transform translate-y-1/2 rotate-45"></div>
                </div>
              </div>
            </div>

            {/* Photo 2: Bottom Right */}
            <div className="absolute bottom-10 right-0 z-20">
              <div className="relative">
                <img
                  src="https://images.unsplash.com/photo-1517048676732-d65bc937f952?q=80&w=400&auto=format&fit=crop"
                  className="w-64 h-52 object-cover rounded-2xl shadow-2xl border-4 border-white transform rotate-3 hover:rotate-0 transition-transform duration-500"
                  alt="Friends Learning"
                />
                <div className="absolute -top-6 -left-4 bg-white text-slate-900 px-4 py-2 rounded-lg shadow-lg text-sm font-bold">
                  Gracias!
                  <div className="absolute bottom-0 right-4 w-3 h-3 bg-white transform translate-y-1/2 rotate-45"></div>
                </div>
              </div>
            </div>

            {/* Decorative Circles */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-white/20 rounded-full blur-3xl -z-10"></div>
          </div>
        </div>
      </div>

      {/* How it Works */}
      <div className="container mx-auto px-6 py-20 max-w-6xl">
        <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-16 text-center md:text-left">How it works</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {/* Step 1 */}
          <div className="flex flex-col gap-6">
            <span className="inline-block px-4 py-1.5 rounded-lg border-2 border-slate-900 dark:border-white font-bold text-sm w-fit dark:text-white">Step 1</span>

            <div className="aspect-[4/3] bg-[#FDE047] rounded-2xl flex items-center justify-center relative overflow-hidden group">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-yellow-200 to-yellow-400 opacity-50"></div>
              {/* Abstract Chat Bubbles */}
              <div className="relative z-10 flex flex-col gap-3 group-hover:scale-105 transition-transform duration-300">
                <div className="bg-blue-500 text-white p-3 rounded-2xl rounded-tl-sm shadow-lg w-32 h-12"></div>
                <div className="bg-green-500 text-white p-3 rounded-2xl rounded-tr-sm shadow-lg w-32 h-12 ml-8"></div>
                <div className="bg-blue-500 text-white p-3 rounded-2xl rounded-bl-sm shadow-lg w-32 h-12"></div>
              </div>
            </div>

            <div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">Share your referral link</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                Send your unique link to friends, colleagues, or anyone who wants to master a new subject.
              </p>
            </div>
          </div>

          {/* Step 2 */}
          <div className="flex flex-col gap-6">
            <span className="inline-block px-4 py-1.5 rounded-lg border-2 border-slate-900 dark:border-white font-bold text-sm w-fit dark:text-white">Step 2</span>

            <div className="aspect-[4/3] bg-[#F9A8D4] rounded-2xl flex items-center justify-center relative overflow-hidden group">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-pink-300 to-pink-500 opacity-50"></div>
              {/* Abstract Heart Coin */}
              <div className="relative z-10 w-32 h-32 rounded-full bg-amber-400 border-4 border-amber-500 shadow-xl flex items-center justify-center group-hover:rotate-12 transition-transform duration-300">
                <div className="text-pink-600">
                  <svg width="60" height="60" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">They get 70% off</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                Your referral gets an exclusive <span className="font-semibold text-emerald-600 dark:text-emerald-400">70% discount</span> on their first trial lesson.
              </p>
            </div>
          </div>

          {/* Step 3 */}
          <div className="flex flex-col gap-6">
            <span className="inline-block px-4 py-1.5 rounded-lg border-2 border-slate-900 dark:border-white font-bold text-sm w-fit dark:text-white">Step 3</span>

            <div className="aspect-[4/3] bg-[#5EEAD4] rounded-2xl flex items-center justify-center relative overflow-hidden group">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-teal-200 to-teal-400 opacity-50"></div>
              {/* Abstract Gift */}
              <div className="relative z-10 group-hover:-translate-y-2 transition-transform duration-300">
                <div className="w-32 h-24 bg-blue-600 rounded-lg shadow-2xl relative">
                  <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-8 bg-yellow-400"></div>
                  <div className="absolute top-1/2 -translate-y-1/2 left-0 right-0 h-8 bg-yellow-400"></div>
                  {/* Lid */}
                  <div className="absolute -top-6 left-1/2 -translate-x-1/2 w-36 h-6 bg-blue-700 rounded-sm">
                    <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-8 bg-yellow-400"></div>
                  </div>
                  {/* Bow */}
                  <div className="absolute -top-12 left-1/2 -translate-x-1/2 text-yellow-400">
                    <svg width="60" height="40" viewBox="0 0 24 24" fill="currentColor"><path d="M12,2C12,2 14,0 16,2C18,4 16,8 12,8C8,8 6,4 8,2C10,0 12,2 12,2M12,8C12,8 16,8 18,10C20,12 18,14 16,14C14,14 12,10 12,10C12,10 10,14 8,14C6,14 4,12 6,10C8,8 12,8 12,8Z"/></svg>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">You get $50</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                You'll receive <span className="font-semibold text-emerald-600 dark:text-emerald-400">$50 in credits</span> automatically when they confirm their first subscription lesson.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="container mx-auto px-6 py-12 max-w-6xl border-t border-slate-200 dark:border-slate-800">
        <div className="flex flex-col md:flex-row gap-12">
          <div className="md:w-1/3">
            <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Got questions <br /> for us?
            </h2>
            <p className="text-slate-500 dark:text-slate-400">
              Check out our most common questions regarding the referral program.
            </p>
          </div>

          <div className="md:w-2/3 space-y-6">
            {[
              {
                question: "When will I get my credit?",
                answer: "You'll get $50 in EduConnect credit 24 hours after your friend confirms their first subscription lesson. It'll be added to your balance automatically and applied at checkout for your future lessons. You can view your credit under Payment Methods."
              },
              {
                question: "How much credit can I earn?",
                answer: "You'll get $50 for each friend who uses your referral link and confirms their first subscription lesson. There's no limit. The more friends you refer, the more credit you earn!"
              },
              {
                question: "Can I refer friends who already have an account?",
                answer: "The referral program is valid for new students only. Your friend must sign up using your unique link to qualify for the discount and for you to receive the credit."
              }
            ].map((faq, idx) => (
              <div key={idx} className="border-b border-slate-200 dark:border-slate-800 pb-6 last:border-0">
                <button
                  onClick={() => toggleFaq(idx)}
                  className="w-full flex justify-between items-center text-left focus:outline-none group"
                >
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-emerald-600 transition-colors">
                    {faq.question}
                  </h3>
                  {openFaq === idx ? (
                    <ChevronUp className="text-emerald-600 flex-shrink-0" />
                  ) : (
                    <ChevronDown className="text-slate-400 flex-shrink-0" />
                  )}
                </button>
                {openFaq === idx && (
                  <div className="mt-4 text-slate-600 dark:text-slate-300 leading-relaxed animate-in slide-in-from-top-2 duration-200">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
