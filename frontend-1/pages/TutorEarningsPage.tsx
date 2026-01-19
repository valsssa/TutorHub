
import React from 'react';
import { ChevronLeft, BarChart2, DollarSign, ArrowRight, Download, CreditCard, HelpCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { User } from '../domain/types';

interface TutorEarningsPageProps {
    currentUser: User;
    onBack: () => void;
    theme: 'dark' | 'light';
}

export const TutorEarningsPage: React.FC<TutorEarningsPageProps> = ({ currentUser, onBack, theme }) => {
    
    // Mock data for the chart
    const data = [
        { name: 'Jan', earnings: 400 },
        { name: 'Feb', earnings: 300 },
        { name: 'Mar', earnings: 600 },
        { name: 'Apr', earnings: 800 },
        { name: 'May', earnings: 500 },
        { name: 'Jun', earnings: 850 },
    ];

    const transactions = [
        { id: 'tx1', date: '2024-06-25', description: 'Lesson with Luis P.', amount: 85.00, status: 'Completed' },
        { id: 'tx2', date: '2024-06-23', description: 'Lesson with Elodie C.', amount: 85.00, status: 'Completed' },
        { id: 'tx3', date: '2024-06-20', description: 'Payout to Bank Account', amount: -1200.00, status: 'Processing' },
        { id: 'tx4', date: '2024-06-18', description: 'Lesson with Sarah M.', amount: 85.00, status: 'Completed' },
    ];

    return (
        <div className="container mx-auto px-4 py-8 max-w-6xl">
            <button 
                onClick={onBack}
                className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-6 group"
            >
                <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                Back to Dashboard
            </button>

            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Earnings & Payouts</h1>
            <p className="text-slate-600 dark:text-slate-400 mb-8">Manage your income, view analytics, and configure payout methods.</p>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Analytics & Summary */}
                <div className="lg:col-span-2 space-y-8">
                    
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                            <div className="text-sm text-slate-500 dark:text-slate-400 font-medium mb-1">Available Balance</div>
                            <div className="text-3xl font-bold text-slate-900 dark:text-white mb-4">$450.00</div>
                            <button className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-colors shadow-sm">
                                Withdraw Funds
                            </button>
                        </div>
                        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                            <div className="text-sm text-slate-500 dark:text-slate-400 font-medium mb-1">Total Earnings (Lifetime)</div>
                            <div className="text-3xl font-bold text-slate-900 dark:text-white mb-4">${currentUser.earnings?.toLocaleString()}</div>
                            <div className="text-sm text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
                                <ArrowRight size={14} className="rotate-[-45deg]"/> +12% vs last month
                            </div>
                        </div>
                    </div>

                    {/* Revenue Analytics Chart */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
                                <BarChart2 size={20} className="text-emerald-500"/> Revenue Analytics
                            </h3>
                            <select className="bg-slate-100 dark:bg-slate-800 border-none rounded-lg text-sm px-3 py-1 text-slate-600 dark:text-slate-300 focus:ring-0">
                                <option>Last 6 Months</option>
                                <option>Last Year</option>
                            </select>
                        </div>
                        <div className="h-80 w-full">
                            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                                <BarChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.1} vertical={false} />
                                    <XAxis dataKey="name" stroke="#64748b" axisLine={false} tickLine={false} dy={10} fontSize={12} />
                                    <YAxis stroke="#64748b" axisLine={false} tickLine={false} tickFormatter={(value) => `$${value}`} fontSize={12} />
                                    <RechartsTooltip 
                                        cursor={{fill: theme === 'dark' ? '#1e293b' : '#f1f5f9'}}
                                        contentStyle={{ backgroundColor: theme === 'dark' ? '#0f172a' : '#ffffff', borderColor: theme === 'dark' ? '#1e293b' : '#e2e8f0', borderRadius: '0.5rem', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Bar dataKey="earnings" fill="#10b981" radius={[4, 4, 0, 0]} barSize={40} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Transaction History */}
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                        <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
                            <h3 className="font-bold text-lg text-slate-900 dark:text-white">Recent Transactions</h3>
                            <button className="text-sm font-medium text-emerald-600 hover:text-emerald-500 transition-colors flex items-center gap-1">
                                <Download size={16} /> Export CSV
                            </button>
                        </div>
                        <div className="divide-y divide-slate-100 dark:divide-slate-800">
                            {transactions.map(tx => (
                                <div key={tx.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${tx.amount > 0 ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}`}>
                                            <DollarSign size={18} />
                                        </div>
                                        <div>
                                            <div className="font-medium text-slate-900 dark:text-white text-sm">{tx.description}</div>
                                            <div className="text-xs text-slate-500">{new Date(tx.date).toLocaleDateString()}</div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className={`font-bold text-sm ${tx.amount > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-900 dark:text-white'}`}>
                                            {tx.amount > 0 ? '+' : ''}${Math.abs(tx.amount).toFixed(2)}
                                        </div>
                                        <div className="text-xs text-slate-500">{tx.status}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="p-4 border-t border-slate-200 dark:border-slate-800 text-center">
                            <button className="text-sm font-bold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors">
                                View All Transactions
                            </button>
                        </div>
                    </div>
                </div>

                {/* Right Column: Settings & Info */}
                <div className="space-y-6">
                    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                        <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-4">Payout Method</h3>
                        <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 mb-4">
                            <div className="w-10 h-10 bg-white dark:bg-slate-900 rounded-lg flex items-center justify-center border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200">
                                <CreditCard size={20} />
                            </div>
                            <div className="flex-1">
                                <div className="text-sm font-bold text-slate-900 dark:text-white">Visa ending in 4242</div>
                                <div className="text-xs text-slate-500">Instant payout available</div>
                            </div>
                            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded">Primary</span>
                        </div>
                        <button className="w-full py-2.5 border border-slate-300 dark:border-slate-600 rounded-xl text-sm font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                            Manage Payout Methods
                        </button>
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-2xl border border-blue-100 dark:border-blue-800/50">
                        <h3 className="font-bold text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-2">
                            <HelpCircle size={18} /> Tax Information
                        </h3>
                        <p className="text-sm text-blue-800 dark:text-blue-200 mb-4 leading-relaxed">
                            Ensure your tax information is up to date to avoid payout delays. You may need to submit a W-9 form if your earnings exceed $600 this year.
                        </p>
                        <button className="text-sm font-bold text-blue-700 dark:text-blue-300 hover:underline">
                            Update Tax Info
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
