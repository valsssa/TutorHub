interface QuickActionProps {
  title: string
  icon: React.ElementType
  color: string
  onClick: () => void
}

export default function QuickAction({ title, icon: Icon, color, onClick }: QuickActionProps) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center space-y-2 p-4 rounded-lg border border-gray-200 hover:border-pink-300 hover:shadow-md transition-all"
    >
      <div className={`${color} w-12 h-12 rounded-lg flex items-center justify-center`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <span className="text-sm font-medium text-gray-700">{title}</span>
    </button>
  )
}
