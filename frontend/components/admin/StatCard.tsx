import { TrendingUp } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string
  icon: React.ElementType
  color: string
  trend: string
}

export default function StatCard({ title, value, icon: Icon, color, trend }: StatCardProps) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 bg-gradient-to-r ${color} rounded-lg flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <TrendingUp className="w-5 h-5 text-green-500" />
      </div>
      <h3 className="text-2xl font-bold text-gray-800 mb-1">{value}</h3>
      <p className="text-sm text-gray-600 mb-2">{title}</p>
      <p className="text-xs text-green-600 font-medium">{trend}</p>
    </div>
  )
}
