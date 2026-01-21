'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import axios from 'axios'
import ProtectedRoute from '@/components/ProtectedRoute'
import { ChevronLeft, DollarSign, Users, PieChart, ArrowRight, CheckCircle } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function AffiliateProgramPage() {
  return (
    <ProtectedRoute>
      <AffiliateContent />
    </ProtectedRoute>
  )
}

function AffiliateContent() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const token = Cookies.get('token')
      if (!token) {
        router.replace('/login')
        return
      }

      try {
        const response = await axios.get(`${API_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setUser(response.data)
      } catch (error) {
        Cookies.remove('token')
        router.replace('/login')
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [router])

  if (loading) {
    return (
      <div className="min-h-screen bg-white dark:bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    )
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 h-20 flex items-center justify-between">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-300 hover:text-emerald-600 font-medium"
          >
            <ChevronLeft size={20} /> Back
          </button>
          <div className="font-bold text-xl tracking-tight text-slate-900 dark:text-white">
            EduConnect <span className="text-emerald-600">Partners</span>
          </div>
        </div>
      </div>

      {/* Hero */}
      <div className="container mx-auto px-4 py-20 max-w-6xl text-center">
        <span className="inline-block py-1 px-3 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-sm font-bold uppercase tracking-wide mb-6">
          Affiliate Program
        </span>
        <h1 className="text-5xl md:text-7xl font-black text-slate-900 dark:text-white mb-8 tracking-tight">
          Earn money by promoting<br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-teal-500">learning.</span>
        </h1>
        <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Join our affiliate program and earn competitive commissions for every new student or tutor you refer to EduConnect.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <button
            onClick={() => router.push('/register')}
            className="bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-8 py-4 rounded-xl font-bold text-lg hover:opacity-90 transition-opacity"
          >
            Become a Partner
          </button>
          <button
            onClick={() => router.push('/login')}
            className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 px-8 py-4 rounded-xl font-bold text-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
          >
            Log In
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-white dark:bg-slate-900 py-16 border-y border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/50 text-center">
              <div className="w-16 h-16 mx-auto bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center text-emerald-600 mb-4">
                <DollarSign size={32} />
              </div>
              <h3 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">30%</h3>
              <p className="text-slate-500">Commission on first purchase</p>
            </div>
            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/50 text-center">
              <div className="w-16 h-16 mx-auto bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center text-blue-600 mb-4">
                <Users size={32} />
              </div>
              <h3 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">90 Days</h3>
              <p className="text-slate-500">Cookie duration</p>
            </div>
            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/50 text-center">
              <div className="w-16 h-16 mx-auto bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center text-purple-600 mb-4">
                <PieChart size={32} />
              </div>
              <h3 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">$500+</h3>
              <p className="text-slate-500">Average partner monthly earnings</p>
            </div>
          </div>
        </div>
      </div>

      {/* Steps */}
      <div className="container mx-auto px-4 py-20 max-w-5xl">
        <div className="space-y-12">
          <div className="flex flex-col md:flex-row gap-8 items-center">
            <div className="flex-1">
              <div className="text-emerald-600 font-bold text-lg mb-2">01. Join</div>
              <h3 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">Sign up in minutes</h3>
              <p className="text-slate-600 dark:text-slate-400 text-lg">
                Creating an account is free and easy. Get instant access to your unique referral links and marketing dashboard.
              </p>
            </div>
            <div className="flex-1 bg-white dark:bg-slate-800 p-8 rounded-3xl shadow-lg border border-slate-100 dark:border-slate-700">
              {/* Mock Form visual */}
              <div className="space-y-4 opacity-50 pointer-events-none">
                <div className="h-10 bg-slate-100 dark:bg-slate-700 rounded-lg w-full"></div>
                <div className="h-10 bg-slate-100 dark:bg-slate-700 rounded-lg w-full"></div>
                <div className="h-10 bg-emerald-500 rounded-lg w-1/3"></div>
              </div>
            </div>
          </div>

          <div className="flex flex-col md:flex-row-reverse gap-8 items-center">
            <div className="flex-1">
              <div className="text-emerald-600 font-bold text-lg mb-2">02. Promote</div>
              <h3 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">Share with your audience</h3>
              <p className="text-slate-600 dark:text-slate-400 text-lg">
                Use our pre-made banners, landing pages, and links on your blog, social media, or newsletter.
              </p>
            </div>
            <div className="flex-1 bg-white dark:bg-slate-800 p-8 rounded-3xl shadow-lg border border-slate-100 dark:border-slate-700 flex items-center justify-center">
              <div className="text-9xl">📣</div>
            </div>
          </div>

          <div className="flex flex-col md:flex-row gap-8 items-center">
            <div className="flex-1">
              <div className="text-emerald-600 font-bold text-lg mb-2">03. Earn</div>
              <h3 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">Get paid monthly</h3>
              <p className="text-slate-600 dark:text-slate-400 text-lg">
                Track your referrals in real-time. We pay out every month via PayPal or Bank Transfer once you reach $50.
              </p>
            </div>
            <div className="flex-1 bg-white dark:bg-slate-800 p-8 rounded-3xl shadow-lg border border-slate-100 dark:border-slate-700">
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                  <span className="font-bold text-emerald-800 dark:text-emerald-200">Payout Sent</span>
                  <span className="font-bold text-emerald-600">+$450.00</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                  <span className="text-slate-500">Pending</span>
                  <span className="font-bold text-slate-900 dark:text-white">$120.00</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}