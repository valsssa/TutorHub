"use client";

import { FiStar } from "react-icons/fi";

export interface Testimonial {
  quote: string;
  author: string;
  role: string;
  rating: number;
  initials?: string;
}

interface TestimonialCardProps {
  testimonial: Testimonial;
}

export default function TestimonialCard({ testimonial }: TestimonialCardProps) {
  const initials = testimonial.initials || testimonial.author.split(' ').map(n => n[0]).join('').toUpperCase();

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition-shadow">
      {/* Rating Stars */}
      <div className="flex gap-1 mb-4">
        {[...Array(5)].map((_, i) => (
          <FiStar
            key={i}
            className={`w-4 h-4 ${
              i < testimonial.rating
                ? "text-amber-400 fill-amber-400"
                : "text-slate-300 dark:text-slate-600"
            }`}
          />
        ))}
      </div>

      {/* Quote */}
      <p className="text-slate-700 dark:text-slate-300 mb-6 leading-relaxed">
        &ldquo;{testimonial.quote}&rdquo;
      </p>

      {/* Author */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center">
          <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
            {initials}
          </span>
        </div>
        <div>
          <p className="font-semibold text-slate-900 dark:text-white text-sm">
            {testimonial.author}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {testimonial.role}
          </p>
        </div>
      </div>
    </div>
  );
}

