
import React, { useState } from 'react';
import { ChevronLeft, BarChart2, TrendingUp, DollarSign, Download, Calendar } from 'lucide-react';
import { 
    AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer 
} from 'recharts';

interface AdminRevenuePageProps {
    onBack: () => void;
}

export const AdminRevenuePage: React.FC<AdminRevenuePageProps> = ({ onBack }) => {
    const [dateRange, setDateRange] = useState('Last 7 Days');

    // Mock Data
    const dailyRevenueData = [
        { name: 'Mon', revenue: 120, expenses: 20 },
        { name: 'Tue', revenue: 180, expenses: 30 },
        { name: 'Wed', revenue: 150, expenses: 25 },
        { name: 'Thu', revenue: 240, expenses: 40 },
        { name: 'Fri', revenue: 300, expenses: 50 },
        { name: 'Sat', revenue: 380, expenses: 60 },
        { name: 'Sun', revenue: 210, expenses: 35 },
    ];

    const monthlyRevenueData = [
        { name: 'Jan', revenue: 4500, profit: 1200 },
        { name: 'Feb', revenue: 5200, profit: 1300 },
        { name: 'Mar', revenue: 4800, profit: 1100 },
        { name: 'Apr', revenue: 6100, profit: 1400 },
        { name: 'May', revenue: 5900, profit: 1600 },
        { name: 'Jun', revenue: 7200, profit: 1500 },
    ];

    const transactions = [
        { id: 'TX-1001', date: '2024-10-25', description: 'Payout to Dr. Elena Vance', amount: -1200.00, status: 'Completed', type: 'Payout' },
        { id: 'TX-1002', date: '2024-10-25', description: 'Platform Fee (Session #4421)', amount: 15.00, status: 'Completed', type: 'Fee' },
        { id: 'TX-1003', date: '2024-10-24', description: 'Platform Fee (Session #4420)', amount: 12.50, status: 'Completed', type: 'Fee' },
        { id: 'TX-1004', date: '2024-10-24', description: 'Refund: Session Cancelled', amount: -85.00, status: 'Completed', type: 'Refund' },
        { id: 'TX-1005', date: '2024-10-23', description: 'Payout to James Chen', amount: -950.00, status: 'Processing', type: 'Payout' },
    ];

    return (
        <div className="container mx-auto px-4 py-8 max-w-7xl">
            <button 
                onClick={onBack}
                className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-6 group"
            >
                <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform"/> 
                Back to Dashboard
            </button>

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
                        <DollarSign size={32} className="text-emerald-500" /> Platform Revenue
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Detailed breakdown of earnings, payouts, and platform fees.</p>
                </div>
                <div className="flex gap-3">
                    <select 
                        value={dateRange}
                        onChange={(e) => setDateRange(e.target.value)}
                        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-lg px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    >
                        <option>Last 7 Days</option>
                        <option>Last 30 Days</option>
                        <option>This Year</option>
                    </select>
                    <button className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-bold transition-colors">
                        <Download size={16} /> Export Report
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
                {/* Main Chart */}
                <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
                            <TrendingUp size={20} className="text-emerald-500"/> Revenue Trend
                        </h3>
                    </div>
                    <div className="h-80 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={dailyRevenueData}>
                                <defs>
                                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.1} vertical={false} />
                                <XAxis dataKey="name" stroke="#64748b" axisLine={false} tickLine={false} dy={10} fontSize={12} />
                                <YAxis stroke="#64748b" axisLine={false} tickLine={false} tickFormatter={(value) => `$${value}`} fontSize={12} />
                                <RechartsTooltip 
                                    contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', color: '#fff' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* KPI Cards */}
                <div className="space-y-6">
                    <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Net Income (This Month)</div>
                        <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">$8,124.00</div>
                        <div className="text-emerald-600 dark:text-emerald-400 text-sm font-medium">+15% vs last month</div>
                    </div>
                    
                    <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Pending Payouts</div>
                        <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">$2,450.00</div>
                        <div className="text-slate-500 text-sm">Next payout batch: Oct 31</div>
                    </div>

                    <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h4 className="font-bold text-slate-900 dark:text-white">Profit Margin</h4>
                            <span className="text-emerald-600 font-bold">15%</span>
                        </div>
                        <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 w-[15%]"></div>
                        </div>
                        <p className="text-xs text-slate-500 mt-2">Platform fee is stable.</p>
                    </div>
                </div>
            </div>

            {/* Monthly Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                    <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                        <Calendar size={20} className="text-blue-500"/> Monthly Profit
                    </h3>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={monthlyRevenueData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" strokeOpacity={0.1} vertical={false} />
                                <XAxis dataKey="name" stroke="#64748b" axisLine={false} tickLine={false} dy={10} fontSize={12} />
                                <YAxis stroke="#64748b" axisLine={false} tickLine={false} tickFormatter={(value) => `$${value}`} fontSize={12} />
                                <RechartsTooltip 
                                    cursor={{fill: 'rgba(255,255,255,0.05)'}}
                                    contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', color: '#fff' }}
                                />
                                <Bar dataKey="profit" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                    <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                        <BarChart2 size={20} className="text-purple-500"/> Revenue Sources
                    </h3>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="text-slate-600 dark:text-slate-300">Commission Fees</span>
                            <span className="font-bold text-slate-900 dark:text-white">$7,200 (85%)</span>
                        </div>
                        <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500 w-[85%]"></div>
                        </div>

                        <div className="flex justify-between items-center">
                            <span className="text-slate-600 dark:text-slate-300">Subscription Plans</span>
                            <span className="font-bold text-slate-900 dark:text-white">$850 (10%)</span>
                        </div>
                        <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500 w-[10%]"></div>
                        </div>

                        <div className="flex justify-between items-center">
                            <span className="text-slate-600 dark:text-slate-300">Featured Listings</span>
                            <span className="font-bold text-slate-900 dark:text-white">$420 (5%)</span>
                        </div>
                        <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-amber-500 w-[5%]"></div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Transactions Table */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
                    <h3 className="font-bold text-lg text-slate-900 dark:text-white">Recent Financial Activity</h3>
                    <button className="text-sm font-medium text-emerald-600 hover:text-emerald-500">View All</button>
                </div>
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
                            <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">ID</th>
                            <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Date</th>
                            <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Description</th>
                            <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Type</th>
                            <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">Amount</th>
                            <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">Status</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {transactions.map((tx) => (
                            <tr key={tx.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                <td className="px-6 py-4 text-sm font-mono text-slate-600 dark:text-slate-400">{tx.id}</td>
                                <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">{tx.date}</td>
                                <td className="px-6 py-4 text-sm text-slate-900 dark:text-white font-medium">{tx.description}</td>
                                <td className="px-6 py-4">
                                    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                        tx.type === 'Payout' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                                        tx.type === 'Fee' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' :
                                        'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
                                    }`}>
                                        {tx.type}
                                    </span>
                                </td>
                                <td className={`px-6 py-4 text-sm font-bold text-right ${tx.amount > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-900 dark:text-white'}`}>
                                    {tx.amount > 0 ? '+' : ''}{tx.amount.toFixed(2)}
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <span className={`text-xs font-medium ${
                                        tx.status === 'Completed' ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'
                                    }`}>
                                        {tx.status}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
