import Image from "next/image";
import { useRouter } from "next/navigation";
import {
  FiStar,
  FiDollarSign,
  FiBook,
  FiClock,
  FiAward,
  FiHeart,
  FiMessageCircle,
} from "react-icons/fi";
import { TutorPublicSummary } from "@/types";
import { resolveAssetUrl } from "@/lib/media";
import Button from "./Button";
import Badge from "./Badge";

interface TutorCardProps {
  tutor: TutorPublicSummary;
  variant?: "default" | "compact" | "featured";
  isSaved?: boolean;
  onToggleSave?: (e: React.MouseEvent, id: number) => void;
}

export default function TutorCard({
  tutor,
  variant = "default",
  isSaved = false,
  onToggleSave,
}: TutorCardProps) {
  const router = useRouter();

  const displayName = tutor.name || tutor.title;

  const getRatingStars = (rating: number) => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const stars = [];

    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <FiStar key={`full-${i}`} className="w-3 h-3 fill-current" />,
      );
    }
    if (hasHalfStar) {
      stars.push(<FiStar key="half" className="w-3 h-3 fill-current opacity-50" />);
    }
    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(<FiStar key={`empty-${i}`} className="w-3 h-3 opacity-20" />);
    }

    return stars;
  };

  const isVerified = Number(tutor.average_rating) >= 4.5 && tutor.total_reviews >= 10;

  if (variant === "compact") {
    return (
      <div
        className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 hover:shadow-lg transition-all cursor-pointer"
        onClick={() => router.push(`/tutors/${tutor.id}`)}
      >
        <div className="flex items-start gap-4">
          {tutor.profile_photo_url && (
            <Image
              src={resolveAssetUrl(tutor.profile_photo_url)}
              alt={displayName}
              width={64}
              height={64}
              className="w-16 h-16 rounded-full object-cover border-2 border-slate-200 dark:border-slate-700"
              unoptimized
            />
          )}
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-slate-900 dark:text-white truncate">{displayName}</h3>
            {tutor.headline && (
              <p className="text-sm text-slate-500 dark:text-slate-400 truncate">{tutor.headline}</p>
            )}
            <div className="flex items-center gap-3 mt-2">
              <div className="flex items-center gap-1 text-amber-500">
                <FiStar className="w-3 h-3 fill-current" />
                <span className="text-sm font-medium text-slate-900 dark:text-white">
                  {Number(tutor.average_rating).toFixed(1)}
                </span>
              </div>
              <span className="text-sm text-slate-600 dark:text-slate-400">
                ${tutor.hourly_rate}/hr
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (variant === "featured") {
    return (
      <div
        className="bg-white dark:bg-slate-900 rounded-xl border-2 border-emerald-500 overflow-hidden hover:shadow-xl hover:shadow-emerald-500/10 transition-all cursor-pointer"
        onClick={() => router.push(`/tutors/${tutor.id}`)}
      >
        <div className="bg-emerald-600 px-4 py-2">
          <div className="flex items-center gap-2 text-white">
            <FiAward className="w-4 h-4" />
            <span className="text-sm font-medium">Featured Tutor</span>
          </div>
        </div>
        <div className="p-6">
          {/* Tutor Header */}
          <div className="flex items-start gap-4 mb-4">
            {tutor.profile_photo_url && (
              <Image
                src={resolveAssetUrl(tutor.profile_photo_url)}
                alt={displayName}
                width={80}
                height={80}
                className="w-20 h-20 rounded-full object-cover border-4 border-white dark:border-slate-800 shadow-md"
                unoptimized
              />
            )}
            <div className="flex-1">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-1">
                {displayName}
              </h3>
              {tutor.headline && (
                <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">
                  {tutor.headline}
                </p>
              )}
            </div>
          </div>

          {/* Rating */}
          <div className="flex items-center gap-2 mb-4">
            <div className="flex items-center gap-1 text-amber-400">
              {getRatingStars(Number(tutor.average_rating))}
            </div>
            <span className="text-lg font-bold text-slate-900 dark:text-white">
              {Number(tutor.average_rating).toFixed(1)}
            </span>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              ({tutor.total_reviews} reviews)
            </span>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3 text-center">
              <FiDollarSign className="w-5 h-5 text-emerald-600 dark:text-emerald-400 mx-auto mb-1" />
              <p className="text-sm font-bold text-slate-900 dark:text-white">
                ${tutor.hourly_rate}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">per hour</p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3 text-center">
              <FiBook className="w-5 h-5 text-blue-600 dark:text-blue-400 mx-auto mb-1" />
              <p className="text-sm font-bold text-slate-900 dark:text-white">
                {tutor.total_sessions}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">sessions</p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3 text-center">
              <FiClock className="w-5 h-5 text-purple-600 dark:text-purple-400 mx-auto mb-1" />
              <p className="text-sm font-bold text-slate-900 dark:text-white">
                {tutor.experience_years}y
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">experience</p>
            </div>
          </div>

          {/* Subjects */}
          {tutor.subjects && tutor.subjects.length > 0 && (
            <div className="mb-4">
              <div className="flex flex-wrap gap-2">
                {tutor.subjects.slice(0, 4).map((subject, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-full text-xs font-medium border border-slate-200 dark:border-slate-700"
                  >
                    {subject}
                  </span>
                ))}
                {tutor.subjects.length > 4 && (
                  <span className="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-500 rounded-full text-xs font-medium">
                    +{tutor.subjects.length - 4} more
                  </span>
                )}
              </div>
            </div>
          )}

          <Button
            variant="primary"
            className="w-full"
            onClick={(e) => {
              e.stopPropagation();
              router.push(`/tutors/${tutor.id}`);
            }}
          >
            View Profile
          </Button>
        </div>
      </div>
    );
  }

  // Default variant
  return (
    <div
      className="group bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 transition-all hover:shadow-[0_0_20px_rgba(16,185,129,0.1)] cursor-pointer overflow-hidden flex flex-col"
      onClick={() => router.push(`/tutors/${tutor.id}`)}
    >
      <div className="p-5 flex-1 relative flex flex-col">
        {/* Save Button */}
        {onToggleSave && (
          <div className="absolute top-4 right-4 z-10">
            <button
              onClick={(e) => onToggleSave(e, tutor.id)}
              className="p-2 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-all active:scale-90"
              title={isSaved ? "Remove from saved" : "Save tutor"}
            >
              <FiHeart
                className={`w-4 h-4 transition-colors duration-200 ${isSaved ? "fill-emerald-500 text-emerald-500" : "text-slate-400"}`}
              />
            </button>
          </div>
        )}

        {/* Header */}
        <div className="flex gap-4 mb-4">
          {tutor.profile_photo_url && (
            <Image
              src={resolveAssetUrl(tutor.profile_photo_url)}
              alt={displayName}
              width={64}
              height={64}
              className="w-16 h-16 rounded-full object-cover border-2 border-slate-200 dark:border-slate-700 shrink-0 hover:scale-105 transition-transform duration-200"
              unoptimized
            />
          )}
          <div>
            <h3 className="font-bold text-lg text-slate-900 dark:text-white group-hover:text-emerald-500 dark:group-hover:text-emerald-400 transition-colors line-clamp-1">
              {displayName}
            </h3>
            {tutor.headline && (
              <p className="text-slate-500 dark:text-slate-400 text-xs line-clamp-1 mb-1">
                {tutor.headline}
              </p>
            )}
            <div className="flex items-center gap-1 text-amber-500 dark:text-amber-400 text-xs font-bold">
              <FiStar className="w-3 h-3 fill-current" />
              {Number(tutor.average_rating).toFixed(1)}
              <span className="text-slate-400 font-normal">({tutor.total_reviews})</span>
            </div>
          </div>
        </div>

        {/* Verified Badge */}
        {isVerified && (
          <div className="mb-3">
            <Badge variant="verified">Verified Expert</Badge>
          </div>
        )}

        {/* Experience */}
        {tutor.experience_years > 0 && (
          <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 mb-3 bg-slate-50 dark:bg-slate-800/50 p-1.5 rounded-lg">
            <FiAward className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            <span className="truncate">{tutor.experience_years} years of experience</span>
          </div>
        )}

        {/* Subjects */}
        {tutor.subjects && tutor.subjects.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4 mt-auto">
            {tutor.subjects.slice(0, 3).map((subject, idx) => (
              <span
                key={idx}
                className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700"
              >
                {subject}
              </span>
            ))}
            {tutor.subjects.length > 3 && (
              <span className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500 px-2 py-0.5 rounded">
                +{tutor.subjects.length - 3}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 flex items-center justify-between">
        <div className="font-bold text-lg text-slate-900 dark:text-white">
          ${tutor.hourly_rate}
          <span className="text-slate-500 text-xs font-normal">/hr</span>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            router.push(`/tutors/${tutor.id}`);
          }}
        >
          View Profile
        </Button>
      </div>
    </div>
  );
}
