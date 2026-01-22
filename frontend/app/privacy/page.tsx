
'use client'

import React from 'react';
import { useRouter } from 'next/navigation';
import { ChevronLeft, Lock, Shield, Globe, Server, UserCheck } from 'lucide-react';

export default function PrivacyPage() {
  const router = useRouter();
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
                        <Lock size={24} />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Privacy Policy</h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">Last Updated: October 24, 2024</p>
                    </div>
                </div>

                <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-300">
                    <p className="lead text-lg">
                        At EduConnect, we value your privacy and are committed to protecting your personal data. This policy outlines exactly what we collect, why we need it, and your rights regarding your information.
                    </p>

                    <h3>1. Information We Collect</h3>
                    <p>We collect information to provide better services to all our users. The types of data we collect include:</p>
                    <ul className="list-disc pl-5 space-y-2">
                        <li><strong>Personal Identification Data:</strong> Name, email address, phone number, and profile photograph.</li>
                        <li><strong>Financial Data:</strong> Payment card details (processed securely via our payment providers like Stripe), billing address, and transaction history.</li>
                        <li><strong>Usage Data:</strong> Information about how you interact with our platform, such as lessons booked, time spent on the site, and search queries.</li>
                        <li><strong>Technical Data:</strong> IP address, browser type, device information, operating system, and crash logs.</li>
                        <li><strong>Content Data:</strong> Messages sent to tutors/students, reviews, and notes.</li>
                        <li><strong>Verification Data (Tutors):</strong> Government ID, educational certificates, and background check results.</li>
                    </ul>

                    <h3>2. Why We Collect Your Data</h3>
                    <p>We use your data for the following legitimate business purposes:</p>
                    <ul className="list-disc pl-5 space-y-2">
                        <li><strong>Service Delivery:</strong> To create your account, process bookings, facilitate video lessons, and manage payments.</li>
                        <li><strong>Platform Improvement:</strong> To analyze user behavior and improve our website functionality and user experience.</li>
                        <li><strong>Communication:</strong> To send transactional emails (booking confirmations), support responses, and optional marketing newsletters.</li>
                        <li><strong>Security & Safety:</strong> To verify identities, prevent fraud, and ensure a safe environment for students and tutors.</li>
                        <li><strong>Legal Compliance:</strong> To comply with applicable laws, regulations, and legal requests.</li>
                    </ul>

                    <h3>3. How We Store and Protect Your Data</h3>
                    <div className="flex gap-4 items-start bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800 my-6">
                        <Server className="text-emerald-600 dark:text-emerald-400 shrink-0 mt-1" size={20} />
                        <div>
                            <h4 className="font-bold text-slate-900 dark:text-white text-sm m-0 mb-1">Secure Storage</h4>
                            <p className="text-sm m-0">
                                Your data is stored on secure servers located in the US and EU. We use industry-standard encryption (AES-256) for data at rest and TLS 1.3 for data in transit. Payment information is never stored on our servers; it is tokenized by our payment processor.
                            </p>
                        </div>
                    </div>
                    <p>
                        We retain your personal data only for as long as necessary to fulfill the purposes we collected it for, including for the purposes of satisfying any legal, accounting, or reporting requirements.
                    </p>

                    <h3>4. Who We Share Your Information With</h3>
                    <p>We do not sell your personal data. We share data only with:</p>
                    <ul className="list-disc pl-5 space-y-2">
                        <li><strong>Other Users:</strong> Students and Tutors see basic profile information (Name, Photo) to facilitate bookings. Contact details are not shared until a booking is confirmed.</li>
                        <li><strong>Service Providers:</strong> Third-party companies that help us operate (e.g., Stripe for payments, AWS for hosting, SendGrid for emails, Google Analytics for usage tracking).</li>
                        <li><strong>Legal Authorities:</strong> If required by law or to protect our rights and safety.</li>
                    </ul>

                    <h3>5. Your Rights</h3>
                    <p>Regardless of your location, we grant you the following rights:</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 not-prose my-6">
                        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                            <h5 className="font-bold text-slate-900 dark:text-white mb-1">Access & Portability</h5>
                            <p className="text-sm text-slate-500">Request a copy of your data in a machine-readable format.</p>
                        </div>
                        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                            <h5 className="font-bold text-slate-900 dark:text-white mb-1">Correction</h5>
                            <p className="text-sm text-slate-500">Update inaccurate or incomplete personal information.</p>
                        </div>
                        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                            <h5 className="font-bold text-slate-900 dark:text-white mb-1">Deletion</h5>
                            <p className="text-sm text-slate-500">Request the permanent deletion of your account and data ("Right to be forgotten").</p>
                        </div>
                        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                            <h5 className="font-bold text-slate-900 dark:text-white mb-1">Opt-Out</h5>
                            <p className="text-sm text-slate-500">Unsubscribe from marketing communications at any time.</p>
                        </div>
                    </div>

                    <h3>6. International Compliance</h3>
                    
                    <h4 className="flex items-center gap-2 mt-6">
                        <Globe size={20} className="text-blue-600" />
                        GDPR (European Union & UK)
                    </h4>
                    <p>
                        If you are a resident of the European Economic Area (EEA) or the UK, our legal basis for collecting and using your personal information depends on the context. Typically, we process data based on <strong>contractual necessity</strong> (to provide lessons) or <strong>legitimate interests</strong>.
                        You have the right to lodge a complaint with your local Data Protection Authority (DPA).
                    </p>

                    <h4 className="flex items-center gap-2 mt-6">
                        <Shield size={20} className="text-purple-600" />
                        CCPA / CPRA (California, USA)
                    </h4>
                    <p>
                        Under the California Consumer Privacy Act (CCPA), California residents have the right to know what personal information is collected, disclosed, or sold. 
                        <strong>EduConnect does not sell your personal information.</strong> You have the right to request deletion of your data and freedom from discrimination for exercising your privacy rights.
                    </p>

                    <h3>7. Cookies</h3>
                    <p>
                        We use cookies to analyze traffic, remember your preferences, and optimize your experience. For detailed information, please refer to our <a href="#" className="text-emerald-600 hover:underline font-bold">Cookie Policy</a>.
                    </p>

                    <h3>8. Contact Us</h3>
                    <p>
                        If you have questions about this policy or wish to exercise your rights, please contact our Data Protection Officer at:
                    </p>
                    <p className="font-bold text-slate-900 dark:text-white">
                        privacy@valsa.solutions<br />
                        123 Education Lane, Tech City, TC 94043
                    </p>
                </div>
            </div>
        </div>
    );
}
