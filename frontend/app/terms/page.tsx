'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import axios from 'axios'
import { ChevronLeft, FileText, Shield, Scale, Gavel, Globe } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function TermsPage() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const token = Cookies.get('token')
      if (!token) {
        // Allow viewing terms without authentication
        setLoading(false)
        return
      }

      try {
        const response = await axios.get(`${API_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setUser(response.data)
      } catch (error) {
        // Continue without user data for public access
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

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-8 group"
      >
        <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/>
        Back
      </button>

      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 md:p-12 shadow-sm">
        <div className="flex items-center gap-4 mb-8 pb-8 border-b border-slate-100 dark:border-slate-800">
          <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center text-emerald-600 dark:text-emerald-400">
            <FileText size={24} />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Terms of Use</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Last updated: October 24, 2024</p>
          </div>
        </div>

        <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-300">
          <h3>1. Introduction</h3>
          <p>
            This Terms of Use Agreement ("Agreement") constitutes a legally binding contract between EduConnect ("Company," "we," "us," or "our") and you ("User," "you," or "your").
            By accessing or using the EduConnect platform, website, and mobile application (collectively, the "Services"), you agree to be bound by these terms.
          </p>

          <h3>2. Acceptable Use</h3>
          <p>
            You agree to use the Services only for lawful purposes and in accordance with this Agreement. You agree not to:
          </p>
          <ul>
            <li>Use the Services in any way that violates applicable federal, state, local, or international law.</li>
            <li>Engage in conduct that restricts or inhibits anyone's use or enjoyment of the Services, or which may harm the Company or users of the Services.</li>
            <li>Use the Services to impersonate or attempt to impersonate the Company, a Company employee, another user, or any other person or entity.</li>
            <li>Engage in any automated use of the system, such as using scripts to send comments or messages, or using any data mining, robots, or similar data gathering and extraction tools.</li>
            <li>Attempt to bypass any measures of the Site designed to prevent or restrict access to the Site, or any portion of the Site.</li>
          </ul>

          <h3>3. User Generated Content</h3>
          <p>
            The Services may invite you to chat, contribute to, or participate in blogs, message boards, online forums, and other functionality, and may provide you with the opportunity to create, submit, post, display, transmit, perform, publish, distribute, or broadcast content and materials to us or on the Services, including but not limited to text, writings, video, audio, photographs, graphics, comments, suggestions, or personal information or other material (collectively, "Contributions").
          </p>
          <p>
            <strong>Moderation:</strong> We have the right (but not the obligation) to: (1) monitor the Contributions; (2) remove any Contributions that we determine in our sole discretion are unlawful, offensive, threatening, libelous, defamatory, pornographic, obscene, or otherwise objectionable or violates any party's intellectual property or these Terms of Use.
          </p>

          <h3>4. Intellectual Property Rights</h3>
          <div className="flex items-start gap-4 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800 my-4">
            <Shield className="text-emerald-600 dark:text-emerald-400 shrink-0 mt-1" size={20} />
            <div>
              <p className="text-sm m-0">
                The Services and its entire contents, features, and functionality (including but not limited to all information, software, text, displays, images, video, and audio, and the design, selection, and arrangement thereof) are owned by the Company, its licensors, or other providers of such material and are protected by United States and international copyright, trademark, patent, trade secret, and other intellectual property or proprietary rights laws.
              </p>
            </div>
          </div>

          <h3>5. Booking, Cancellations, and Refunds</h3>
          <p>
            <strong>Booking:</strong> Students agree to pay the fees specified by the Tutor. EduConnect collects a service fee for each transaction.
          </p>
          <p>
            <strong>Cancellations:</strong> Lessons can be cancelled or rescheduled up to 24 hours before the scheduled start time for a full refund. Cancellations made within 24 hours are subject to a 100% fee.
          </p>

          <h3>6. Limitation of Liability</h3>
          <p className="uppercase text-xs font-bold text-slate-500 tracking-wider mb-2">Important Legal Notice</p>
          <p>
            TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT WILL THE COMPANY, ITS AFFILIATES, OR THEIR LICENSORS, SERVICE PROVIDERS, EMPLOYEES, AGENTS, OFFICERS, OR DIRECTORS BE LIABLE FOR DAMAGES OF ANY KIND, UNDER ANY LEGAL THEORY, ARISING OUT OF OR IN CONNECTION WITH YOUR USE, OR INABILITY TO USE, THE SERVICES, INCLUDING ANY DIRECT, INDIRECT, SPECIAL, INCIDENTAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO, PERSONAL INJURY, PAIN AND SUFFERING, EMOTIONAL DISTRESS, LOSS OF REVENUE, LOSS OF PROFITS, LOSS OF BUSINESS OR ANTICIPATED SAVINGS, LOSS OF USE, LOSS OF GOODWILL, LOSS OF DATA, AND WHETHER CAUSED BY TORT (INCLUDING NEGLIGENCE), BREACH OF CONTRACT, OR OTHERWISE, EVEN IF FORESEEABLE.
          </p>

          <h3>7. Governing Law and Jurisdiction</h3>
          <div className="flex items-center gap-2 mb-2">
            <Globe size={18} className="text-blue-500" />
            <span className="font-bold text-slate-900 dark:text-white">State of California</span>
          </div>
          <p>
            All matters relating to the Services and these Terms of Use, and any dispute or claim arising therefrom or related thereto (in each case, including non-contractual disputes or claims), shall be governed by and construed in accordance with the internal laws of the State of California without giving effect to any choice or conflict of law provision or rule.
          </p>

          <h3>8. Dispute Resolution</h3>
          <div className="flex items-start gap-4 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800 my-4">
            <Gavel className="text-purple-600 dark:text-purple-400 shrink-0 mt-1" size={20} />
            <div>
              <h4 className="font-bold text-slate-900 dark:text-white text-sm m-0 mb-1">Binding Arbitration</h4>
              <p className="text-sm m-0">
                You agree that any dispute, claim, or controversy arising out of or relating to these Terms or the breach, termination, enforcement, interpretation, or validity thereof or the use of the Services shall be settled by binding arbitration between you and the Company, except that each party retains the right to bring an individual action in small claims court and the right to seek injunctive or other equitable relief in a court of competent jurisdiction.
              </p>
            </div>
          </div>
          <p>
            <strong>Class Action Waiver:</strong> You and the Company agree that each may bring claims against the other only in your or its individual capacity and not as a plaintiff or class member in any purported class or representative proceeding.
          </p>

          <h3>9. Contact Us</h3>
          <p>
            All feedback, comments, requests for technical support, and other communications relating to the Services should be directed to: <span className="font-bold text-slate-900 dark:text-white">legal@educonnect.com</span>.
          </p>
        </div>
      </div>
    </div>
  )
}