
import React, { useState } from 'react';
import { ChevronLeft, Users, Search, Filter, Trash2, UserPlus, AlertTriangle } from 'lucide-react';
import { AdminProfile } from '../domain/types';
import { Modal } from '../components/shared/UI';

interface AdminManagePageProps {
    admins: AdminProfile[];
    onAddAdmin: (admin: AdminProfile) => void;
    onRemoveAdmin: (id: string) => void;
    onBack: () => void;
}

export const AdminManagePage: React.FC<AdminManagePageProps> = ({ 
    admins, onAddAdmin, onRemoveAdmin, onBack 
}) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [adminToDelete, setAdminToDelete] = useState<string | null>(null);
    
    // Form State
    const [newName, setNewName] = useState('');
    const [newEmail, setNewEmail] = useState('');

    const filteredAdmins = admins.filter(admin => 
        admin.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
        admin.email.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleCreate = (e: React.FormEvent) => {
        e.preventDefault();
        const newAdmin: AdminProfile = {
            id: `a${Date.now()}`,
            name: newName,
            email: newEmail,
            role: 'ADMIN',
            status: 'Active',
            joinedDate: new Date().toISOString().split('T')[0]
        };
        onAddAdmin(newAdmin);
        setIsAddModalOpen(false);
        setNewName('');
        setNewEmail('');
    };

    const handleDelete = () => {
        if (adminToDelete) {
            onRemoveAdmin(adminToDelete);
            setAdminToDelete(null);
        }
    };

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
                        <Users size={32} className="text-purple-500" /> Manage Administrators
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Control access levels and manage platform administrators.</p>
                </div>
                
                <div className="flex gap-3">
                    <div className="relative">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input 
                            type="text" 
                            placeholder="Search admins..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 w-64"
                        />
                    </div>
                    <button 
                        onClick={() => setIsAddModalOpen(true)}
                        className="flex items-center gap-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-4 py-2 rounded-lg font-bold text-sm hover:opacity-90 transition-opacity"
                    >
                        <UserPlus size={16} /> Add Admin
                    </button>
                </div>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Name</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Role</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Status</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Joined Date</th>
                                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {filteredAdmins.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                                        No administrators found.
                                    </td>
                                </tr>
                            ) : (
                                filteredAdmins.map((admin) => (
                                    <tr key={admin.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-700 dark:text-purple-300 font-bold">
                                                    {admin.name.charAt(0)}
                                                </div>
                                                <div>
                                                    <div className="font-bold text-slate-900 dark:text-white text-sm">{admin.name}</div>
                                                    <div className="text-xs text-slate-500">{admin.email}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm font-medium text-slate-600 dark:text-slate-300">
                                            {admin.role}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                                                {admin.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                                            {new Date(admin.joinedDate).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button 
                                                onClick={() => setAdminToDelete(admin.id)}
                                                className="text-slate-400 hover:text-red-600 p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                                title="Remove Admin"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create Modal */}
            <Modal
                isOpen={isAddModalOpen}
                onClose={() => setIsAddModalOpen(false)}
                title="Create New Admin"
            >
                <form onSubmit={handleCreate} className="space-y-4">
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                        Add a new administrator to the platform. They will have full access to user management and moderation tools.
                    </p>
                    
                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Full Name</label>
                        <input 
                            type="text" 
                            required
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            placeholder="e.g. Alex Smith" 
                            className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white" 
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Email Address</label>
                        <input 
                            type="email" 
                            required
                            value={newEmail}
                            onChange={(e) => setNewEmail(e.target.value)}
                            placeholder="admin@edu.com" 
                            className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm dark:text-white" 
                        />
                    </div>

                    <div className="flex justify-end pt-2">
                         <button 
                            type="submit"
                            className="px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg text-sm font-bold"
                        >
                            Create Admin User
                        </button>
                    </div>
                </form>
            </Modal>

            {/* Delete Modal */}
            <Modal
                isOpen={!!adminToDelete}
                onClose={() => setAdminToDelete(null)}
                title="Remove Administrator"
            >
                <div className="space-y-6">
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-xl">
                        <div className="flex gap-3">
                            <AlertTriangle size={24} className="text-red-600 dark:text-red-400 shrink-0" />
                            <div>
                                <h4 className="font-bold text-red-800 dark:text-red-200 mb-1">Are you sure?</h4>
                                <p className="text-sm text-red-700 dark:text-red-300">
                                    This action will immediately remove the administrator from the platform. They will lose all access.
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end gap-3">
                        <button 
                            onClick={() => setAdminToDelete(null)}
                            className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
                        >
                            Cancel
                        </button>
                        <button 
                            onClick={handleDelete}
                            className="px-4 py-2 text-sm font-bold text-white bg-red-600 rounded-lg hover:bg-red-700 shadow-lg shadow-red-500/20 transition-all"
                        >
                            Remove Admin
                        </button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};
