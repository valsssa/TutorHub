export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        {/* Spinner */}
        <div className="inline-flex items-center justify-center w-16 h-16 mb-4">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        </div>

        {/* Loading Text */}
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Loading...</h2>
        <p className="text-gray-500">Please wait while we load your content</p>
      </div>
    </div>
  )
}
