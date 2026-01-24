
'use client'

import React from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { ChevronLeft, Check, DollarSign, Calendar, Globe, Users } from 'lucide-react';

export default function BecomeTutorPage() {
  const router = useRouter();
    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 pb-16">
            <div className="bg-slate-900 text-white relative overflow-hidden">
                <div className="absolute inset-0 bg-emerald-600/10 pattern-dots"></div>
                <div className="container mx-auto px-4 py-8 relative z-10">
                    <button
                        onClick={() => router.back()}
                        className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors font-medium mb-12 group"
                    >
                        <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                        Back
                    </button>

                    <div className="flex flex-col lg:flex-row items-center gap-12 mb-16">
                        <div className="flex-1 text-center lg:text-left">
                            <h1 className="text-5xl lg:text-6xl font-black mb-6 leading-tight">
                                Share your knowledge.<br/>
                                <span className="text-emerald-400">Earn money.</span>
                            </h1>
                            <p className="text-xl text-slate-300 mb-8 leading-relaxed max-w-2xl mx-auto lg:mx-0">
                                Join over 30,000 tutors teaching 120+ subjects. Set your own rates, manage your own schedule, and teach students globally.
                            </p>
                            <button
                                onClick={() => router.push('/tutor/onboarding')}
                                className="px-8 py-4 bg-emerald-600 hover:bg-emerald-500 text-white text-lg font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-1"
                            >
                                Become a Tutor
                            </button>
                        </div>
                        <div className="flex-1 relative">
                            <div className="relative z-10 bg-white dark:bg-slate-800 p-2 rounded-3xl shadow-2xl rotate-2 hover:rotate-0 transition-transform duration-500">
                                <div className="relative w-full h-[400px]">
                                    <Image 
                                        src="https://images.unsplash.com/photo-1544717305-2782549b5136?q=80&w=1000&auto=format&fit=crop" 
                                        alt="Happy Tutor" 
                                        fill
                                        className="rounded-2xl object-cover object-top"
                                        unoptimized
                                    />
                                </div>
                                <div className="absolute -bottom-6 -left-6 bg-white dark:bg-slate-700 p-4 rounded-xl shadow-xl flex items-center gap-4">
                                    <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center text-emerald-600 dark:text-emerald-400 font-bold text-xl">
                                        $
                                    </div>
                                    <div>
                                        <p className="text-sm text-slate-500 dark:text-slate-300 font-bold uppercase">Average Earnings</p>
                                        <p className="text-xl font-bold text-slate-900 dark:text-white">$1,500/mo</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="container mx-auto px-4 py-16 max-w-6xl">
                <div className="text-center mb-16">
                    <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">Why teach with EduConnect?</h2>
                    <p className="text-slate-600 dark:text-slate-400">Everything you need to build your tutoring business.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {[
                        { icon: DollarSign, title: 'Set your own rates', desc: 'Choose your hourly rate and change it anytime. You keep 85% of your earnings.' },
                        { icon: Calendar, title: 'Flexible schedule', desc: 'You decide when and how many hours you want to teach. No minimum commitment.' },
                        { icon: Globe, title: 'Teach from anywhere', desc: 'Connect with students from over 180 countries from the comfort of your home.' },
                        { icon: Users, title: 'Grow your business', desc: 'We handle marketing, billing, and scheduling so you can focus on teaching.' }
                    ].map((feature, i) => (
                        <div key={i} className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-shadow">
                            <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center text-emerald-600 dark:text-emerald-400 mb-4">
                                <feature.icon size={24} />
                            </div>
                            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">{feature.title}</h3>
                            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">{feature.desc}</p>
                        </div>
                    ))}
                </div>
            </div>

            <div className="bg-slate-100 dark:bg-slate-900 py-16">
                <div className="container mx-auto px-4 max-w-4xl">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">How it works</h2>
                    </div>
                    
                    <div className="space-y-8">
                        {[
                            { step: 1, title: 'Sign up and create your profile', text: 'Upload your photo, describe your experience, and set your availability.' },
                            { step: 2, title: 'Get verified', text: 'Upload your ID and certifications to get the Verified badge and boost your visibility.' },
                            { step: 3, title: 'Start getting students', text: 'Students will find your profile and book lessons. We send you notifications instantly.' },
                            { step: 4, title: 'Get paid securely', text: 'Withdraw your earnings via PayPal, Payoneer, or direct bank transfer.' }
                        ].map((item, i) => (
                            <div key={i} className="flex gap-6 items-start bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm">
                                <div className="w-10 h-10 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-full flex items-center justify-center font-bold shrink-0">
                                    {item.step}
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">{item.title}</h3>
                                    <p className="text-slate-600 dark:text-slate-400">{item.text}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
