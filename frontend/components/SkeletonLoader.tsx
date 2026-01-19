interface SkeletonLoaderProps {
  className?: string;
  variant?: 'text' | 'circle' | 'rectangular';
  width?: string;
  height?: string;
  lines?: number;
}

export default function SkeletonLoader({
  className = '',
  variant = 'rectangular',
  width = '100%',
  height = '20px',
  lines = 1,
}: SkeletonLoaderProps) {
  const baseClass = 'animate-pulse bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%]';
  
  const variantClass = {
    text: 'rounded',
    circle: 'rounded-full',
    rectangular: 'rounded-lg',
  }[variant];

  if (lines > 1) {
    return (
      <div className={`space-y-3 ${className}`}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`${baseClass} ${variantClass}`}
            style={{
              width: i === lines - 1 ? '80%' : width,
              height,
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`${baseClass} ${variantClass} ${className}`}
      style={{ width, height }}
    />
  );
}

export function TutorCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl shadow-soft border border-gray-100 p-6 animate-pulse">
      <div className="mb-4">
        <SkeletonLoader height="24px" width="70%" className="mb-2" />
        <SkeletonLoader height="16px" width="90%" lines={2} />
      </div>

      <div className="flex items-center gap-2 mb-4">
        <SkeletonLoader variant="circle" width="20px" height="20px" />
        <SkeletonLoader height="20px" width="100px" />
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-2">
            <SkeletonLoader variant="rectangular" width="40px" height="40px" />
            <div className="flex-1">
              <SkeletonLoader height="12px" width="60%" className="mb-1" />
              <SkeletonLoader height="16px" width="80%" />
            </div>
          </div>
        ))}
      </div>

      <div className="mb-4">
        <SkeletonLoader height="14px" width="80px" className="mb-2" />
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3].map((i) => (
            <SkeletonLoader
              key={i}
              height="28px"
              width="80px"
              className="rounded-full"
            />
          ))}
        </div>
      </div>

      <SkeletonLoader height="40px" width="100%" />
    </div>
  );
}

export function TutorProfileSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
        <div className="flex flex-col md:flex-row gap-6">
          <SkeletonLoader variant="circle" width="128px" height="128px" />
          <div className="flex-1">
            <SkeletonLoader height="32px" width="60%" className="mb-2" />
            <SkeletonLoader height="20px" width="80%" className="mb-4" />
            <div className="flex flex-wrap gap-4 mb-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center gap-2">
                  <SkeletonLoader variant="rectangular" width="40px" height="40px" />
                  <div>
                    <SkeletonLoader height="12px" width="60px" className="mb-1" />
                    <SkeletonLoader height="16px" width="80px" />
                  </div>
                </div>
              ))}
            </div>
            <SkeletonLoader height="48px" width="200px" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {[1, 2].map((i) => (
            <div key={i} className="bg-white rounded-lg shadow-sm p-6">
              <SkeletonLoader height="28px" width="40%" className="mb-4" />
              <SkeletonLoader height="16px" lines={5} />
            </div>
          ))}
        </div>
        <div className="space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-lg shadow-sm p-6">
              <SkeletonLoader height="20px" width="50%" className="mb-4" />
              <SkeletonLoader height="16px" lines={3} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
