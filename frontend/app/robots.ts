import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'

  return {
    rules: [
      {
        userAgent: '*',
        allow: [
          '/',
          '/login',
          '/register',
          '/tutors',
          '/subjects',
          '/about',
          '/contact',
        ],
        disallow: [
          '/admin/*',
          '/dashboard/*',
          '/api/*',
          '/student/*',
          '/tutor/*',
          '/messages/*',
          '/bookings/*',
          '/settings/*',
        ],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  }
}
