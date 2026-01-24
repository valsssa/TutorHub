'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronLeft, Search, Mail, MessageCircle, AlertCircle, HelpCircle, CheckCircle, ChevronDown, ChevronUp, Book, CreditCard, Shield, User, Send, X } from 'lucide-react'
import ProtectedRoute from '@/components/ProtectedRoute'

type FaqCategory = 'General' | 'Booking & Lessons' | 'Payments' | 'For Tutors'

interface FAQ {
    question: string;
    answer: string;
    category: FaqCategory;
}

const FAQS: FAQ[] = [
    {
        category: 'General',
        question: "How does EduConnect work?",
        answer: "EduConnect connects students with elite educators for 1-on-1 online lessons. You can browse tutor profiles, book a time slot that fits your schedule, and meet in our integrated video classroom. There are no monthly subscription fees for students; you simply pay per lesson."
    },
    {
        category: 'General',
        question: "Is EduConnect safe to use?",
        answer: "Yes. We take safety seriously. We verify our tutors' identities and qualifications before they can list on the platform. All payments are processed through secure, encrypted channels (Stripe), and personal contact details are kept private until a booking is confirmed."
    },
    {
        category: 'Booking & Lessons',
        question: "How do I reschedule or cancel a lesson?",
        answer: "Go to your Dashboard > My Lessons. You can reschedule or cancel for free up to 24 hours before the scheduled start time. Cancellations made within 24 hours of the lesson may be subject to a fee to compensate the tutor for their reserved time."
    },
    {
        category: 'Booking & Lessons',
        question: "How do I join my video lesson?",
        answer: "Once your lesson is confirmed, a 'Join Classroom' button will appear in your Dashboard and in the lesson details 10 minutes before the start time. Simply click it to enter the secure video room directly in your browser—no extra software downloads required."
    },
    {
        category: 'Booking & Lessons',
        question: "What if I'm not satisfied with my lesson?",
        answer: "We offer a 'Good Fit Guarantee'. If your first lesson with a new tutor doesn't go well, let us know within 24 hours. We will issue a full refund or provide a free credit so you can try another tutor who might be a better match."
    },
    {
        category: 'Payments',
        question: "When am I charged for a lesson?",
        answer: "You are charged at the time of booking to reserve the tutor's time. The funds are held securely in escrow and are only released to the tutor after the lesson is successfully completed."
    },
    {
        category: 'Payments',
        question: "What payment methods do you accept?",
        answer: "We accept all major credit and debit cards (Visa, Mastercard, American Express) as well as digital wallets like Apple Pay and Google Pay. In some regions, PayPal is also supported."
    },
    {
        category: 'For Tutors',
        question: "How do I get paid?",
        answer: "Tutors receive payouts via Stripe Connect or PayPal. Earnings from a lesson become available for withdrawal 72 hours after the lesson is completed to account for any dispute window. You can set up automatic weekly payouts in your Tutor Dashboard."
    },
    {
        category: 'For Tutors',
        question: "How do I become a verified tutor?",
        answer: "Navigate to your Profile Settings and click 'Get Verified'. You'll need to upload a government-issued photo ID and proof of your qualifications (such as a degree or teaching certificate). Our team reviews these documents typically within 24-48 hours."
    }
];

export default function SupportPage() {
    return (
        <ProtectedRoute>
            <SupportContent />
        </ProtectedRoute>
    )
}

function SupportContent() {
    const router = useRouter()
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedCategory, setSelectedCategory] = useState<FaqCategory | 'All'>('All')
    const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null)
    
    // Email Modal State
    const [isEmailModalOpen, setIsEmailModalOpen] = useState(false)
    const [emailSubject, setEmailSubject] = useState('General Inquiry')
    const [emailMessage, setEmailMessage] = useState('')
    const [isEmailSent, setIsEmailSent] = useState(false)

    const filteredFaqs = FAQS.filter(faq => {
        const matchesSearch = 
            faq.question.toLowerCase().includes(searchQuery.toLowerCase()) || 
            faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
        const matchesCategory = selectedCategory === 'All' || faq.category === selectedCategory
        return matchesSearch && matchesCategory
    })

    const toggleFaq = (index: number) => {
        setOpenFaqIndex(openFaqIndex === index ? null : index)
    }

    const handleEmailSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        // Simulate sending logic
        setIsEmailSent(true)
        setTimeout(() => {
            setIsEmailSent(false)
            setIsEmailModalOpen(false)
            setEmailMessage('')
            setEmailSubject('General Inquiry')
        }, 2000)
    }

    const handleBack = () => {
        router.push('/dashboard')
    }

    const handleStartChat = () => {
        router.push('/messages')
    }

    const categories: (FaqCategory | 'All')[] = ['All', 'General', 'Booking & Lessons', 'Payments', 'For Tutors']

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
            <div className="container mx-auto px-4 py-8 max-w-5xl">
                <button 
                    onClick={handleBack} 
                    className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-6 group"
                >
                    <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                    Back to Dashboard
                </button>

            <div className="text-center py-12 mb-12 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-full bg-grid-slate-100 dark:bg-grid-slate-800/50 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] pointer-events-none"></div>
                <div className="relative z-10 max-w-2xl mx-auto px-4">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-bold mb-4 border border-blue-200 dark:border-blue-800">
                        <HelpCircle size={14} /> Help Center
                    </div>
                    <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">How can we help you today?</h1>
                    <p className="text-slate-600 dark:text-slate-400 mb-8">Search for answers or browse our frequently asked questions.</p>
                    
                    <div className="relative">
                        <Search className="absolute left-4 top-3.5 text-slate-400" size={20} />
                        <input 
                            type="text" 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search for answers (e.g., 'refund', 'booking')..." 
                            className="w-full pl-12 pr-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl text-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all shadow-sm"
                        />
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:border-emerald-500/50 transition-all cursor-pointer group hover:-translate-y-1">
                    <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                        <Book size={24} />
                    </div>
                    <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">Getting Started</h3>
                    <p className="text-slate-500 dark:text-slate-400 text-sm">New to EduConnect? Learn the basics of booking your first lesson and setting up your profile.</p>
                </div>
                <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:border-emerald-500/50 transition-all cursor-pointer group hover:-translate-y-1">
                    <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                        <CreditCard size={24} />
                    </div>
                    <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">Billing & Payments</h3>
                    <p className="text-slate-500 dark:text-slate-400 text-sm">Everything you need to know about payments, pricing, refunds, and payout methods.</p>
                </div>
                <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:border-emerald-500/50 transition-all cursor-pointer group hover:-translate-y-1">
                    <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                        <Shield size={24} />
                    </div>
                    <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">Trust & Safety</h3>
                    <p className="text-slate-500 dark:text-slate-400 text-sm">Learn about our verification process, community guidelines, and how we keep you safe.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                <div className="lg:col-span-2">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Frequently Asked Questions</h2>
                    </div>

                    {/* Category Filter */}
                    <div className="flex flex-wrap gap-2 mb-8">
                        {categories.map(cat => (
                            <button
                                key={cat}
                                onClick={() => { setSelectedCategory(cat); setOpenFaqIndex(null); }}
                                className={`px-4 py-2 rounded-full text-sm font-bold transition-colors ${
                                    selectedCategory === cat 
                                        ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900' 
                                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                                }`}
                            >
                                {cat}
                            </button>
                        ))}
                    </div>

                    <div className="space-y-4">
                        {filteredFaqs.length === 0 ? (
                            <div className="text-center py-12 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
                                <p className="text-slate-500 dark:text-slate-400">No results found for &quot;{searchQuery}&quot;. Try a different keyword.</p>
                            </div>
                        ) : (
                            filteredFaqs.map((faq, i) => (
                                <div key={i} className="group bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden transition-all hover:border-emerald-500/30">
                                    <button 
                                        onClick={() => toggleFaq(i)}
                                        className="w-full flex justify-between items-center p-5 text-left focus:outline-none"
                                    >
                                        <span className="font-bold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors pr-4">
                                            {faq.question}
                                        </span>
                                        <span className={`transform transition-transform duration-200 text-slate-400 ${openFaqIndex === i ? 'rotate-180 text-emerald-500' : ''}`}>
                                            <ChevronDown size={20} />
                                        </span>
                                    </button>
                                    {openFaqIndex === i && (
                                        <div className="px-5 pb-5 text-slate-600 dark:text-slate-300 text-sm leading-relaxed animate-in slide-in-from-top-2 duration-200 border-t border-slate-100 dark:border-slate-800 pt-3">
                                            {faq.answer}
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sticky top-24">
                        <h3 className="font-bold text-slate-900 dark:text-white mb-4">Still need help?</h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">Our support team is available 24/7 to assist you with any questions or issues.</p>
                        
                        <div className="space-y-3">
                            <button 
                                onClick={handleStartChat}
                                className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl transition-colors shadow-lg shadow-emerald-500/20 active:scale-95"
                            >
                                <MessageCircle size={18} /> Start Live Chat
                            </button>
                            <button 
                                onClick={() => setIsEmailModalOpen(true)}
                                className="w-full flex items-center justify-center gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 font-bold py-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors active:scale-95"
                            >
                                <Mail size={18} /> Email Support
                            </button>
                        </div>

                        <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-700">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-full text-emerald-600 dark:text-emerald-400">
                                    <CheckCircle size={16} />
                                </div>
                                <div>
                                    <div className="font-bold text-slate-900 dark:text-white text-sm">System Status</div>
                                    <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">All systems operational</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Email Support Modal */}
            <Modal isOpen={isEmailModalOpen} onClose={() => setIsEmailModalOpen(false)} title="Contact Support">
                {isEmailSent ? (
                    <div className="text-center py-8">
                        <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 animate-in zoom-in duration-300">
                            <CheckCircle size={32} />
                        </div>
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Message Sent!</h3>
                        <p className="text-slate-500 dark:text-slate-400">Our team will get back to you shortly via email.</p>
                    </div>
                ) : (
                    <form onSubmit={handleEmailSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Subject</label>
                            <select 
                                value={emailSubject}
                                onChange={(e) => setEmailSubject(e.target.value)}
                                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all text-slate-900 dark:text-white"
                            >
                                <option>General Inquiry</option>
                                <option>Billing Issue</option>
                                <option>Technical Support</option>
                                <option>Report a User</option>
                                <option>Other</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Message</label>
                            <textarea 
                                value={emailMessage}
                                onChange={(e) => setEmailMessage(e.target.value)}
                                required
                                rows={5}
                                placeholder="Describe your issue or question..."
                                className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all text-slate-900 dark:text-white resize-none"
                            />
                        </div>
                        <div className="flex justify-end gap-3 pt-2">
                            <button 
                                type="button" 
                                onClick={() => setIsEmailModalOpen(false)}
                                className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors font-medium text-sm"
                            >
                                Cancel
                            </button>
                            <button 
                                type="submit"
                                disabled={!emailMessage.trim()}
                                className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-bold text-sm transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            >
                                <Send size={16} /> Send Message
                            </button>
                        </div>
                    </form>
                )}
            </Modal>
            </div>
        </div>
    )
}

// Modal Component
interface ModalProps {
    isOpen: boolean
    onClose: () => void
    title: string
    children: React.ReactNode
}

function Modal({ isOpen, onClose, title, children }: ModalProps) {
    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 dark:border-slate-800 animate-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800">
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white">{title}</h3>
                    <button 
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>
                <div className="p-6">
                    {children}
                </div>
            </div>
        </div>
    )
}
