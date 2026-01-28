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

// Placeholder testimonials data (replace with real customer quotes when available)
export const placeholderTestimonials: Testimonial[] = [
  {
    quote: "I improved from a B- to an A+ in calculus in just 8 weeks. My tutor Maria was incredible at breaking down complex concepts!",
    author: "Sarah M.",
    role: "College Student",
    rating: 5,
    initials: "SM",
  },
  {
    quote: "Finally found a Spanish tutor who matches my busy schedule. Flexible, patient, and really understands adult learners.",
    author: "James K.",
    role: "Working Professional",
    rating: 5,
    initials: "JK",
  },
  {
    quote: "My son's confidence in reading has skyrocketed. His tutor makes every session fun and engaging. Worth every penny!",
    author: "Linda T.",
    role: "Parent",
    rating: 5,
    initials: "LT",
  },
  {
    quote: "As a working mom, the flexibility to book lessons anytime is a game-changer. The tutors are always prepared and professional.",
    author: "Rachel P.",
    role: "Parent & Part-time Student",
    rating: 5,
    initials: "RP",
  },
];
