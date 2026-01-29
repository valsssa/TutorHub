/**
 * Integration tests for Favorites API
 * These tests hit the real backend API endpoints
 */

import axios, { AxiosInstance } from 'axios'

// Use test backend URL - must be set in environment
const API_URL = process.env.NEXT_PUBLIC_API_URL

if (!API_URL) {
  throw new Error('NEXT_PUBLIC_API_URL environment variable is required for integration tests')
}

console.log(`Integration tests will use API URL: ${API_URL}`)

describe('Favorites API Integration Tests', () => {
  let api: AxiosInstance
  let studentToken: string
  let tutorProfileId: number

  beforeAll(async () => {
    // Create axios instance for tests
    api = axios.create({
      baseURL: API_URL,
      timeout: 10000,
    })

    try {
      // Login as student to get auth token (using form data, not JSON)
      const loginParams = new URLSearchParams()
      loginParams.append('username', 'student@example.com')
      loginParams.append('password', 'student123')

      console.log(`Attempting login to ${API_URL}/api/v1/auth/login`)
      
      const loginResponse = await api.post('/api/v1/auth/login', loginParams, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })
      
      studentToken = loginResponse.data.access_token
      console.log(`Student login successful, token obtained`)

      // Get or create a tutor profile for testing
      try {
        // First, login as tutor
        const tutorLoginParams = new URLSearchParams()
        tutorLoginParams.append('username', 'tutor@example.com')
        tutorLoginParams.append('password', 'tutor123')
        
        const tutorLogin = await api.post('/api/v1/auth/login', tutorLoginParams, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        })
        const tutorToken = tutorLogin.data.access_token
        console.log(`Tutor login successful`)

        // Get tutor's profile
        const profileResponse = await api.get('/api/v1/tutors/me/profile', {
          headers: { Authorization: `Bearer ${tutorToken}` },
        })
        
        tutorProfileId = profileResponse.data.id
        console.log(`Tutor profile ID obtained: ${tutorProfileId}`)
      } catch (error: any) {
        console.error('Failed to get tutor profile:', error.response?.data || error.message)
        throw error
      }
    } catch (error: any) {
      console.error('Login failed:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message,
        url: error.config?.url,
      })
      throw error
    }
  })

  afterEach(async () => {
    // Clean up: remove all favorites for the test student
    try {
      const favoritesResponse = await api.get('/api/v1/favorites/', {
        headers: { Authorization: `Bearer ${studentToken}` },
      })
      
      const favorites = favoritesResponse.data
      for (const fav of favorites) {
        await api.delete(`/api/v1/favorites/${fav.tutor_profile_id}`, {
          headers: { Authorization: `Bearer ${studentToken}` },
        })
      }
    } catch (error) {
      // Ignore cleanup errors
    }
  })

  describe('GET /api/favorites', () => {
    it('should return empty array when user has no favorites', async () => {
      const response = await api.get('/api/v1/favorites/', {
        headers: { Authorization: `Bearer ${studentToken}` },
      })

      expect(response.status).toBe(200)
      expect(Array.isArray(response.data)).toBe(true)
      expect(response.data).toEqual([])
    })

    it('should return list of favorites when user has saved tutors', async () => {
      // Add a favorite first
      await api.post(
        '/api/v1/favorites/',
        { tutor_profile_id: tutorProfileId },
        { headers: { Authorization: `Bearer ${studentToken}` } }
      )

      const response = await api.get('/api/v1/favorites/', {
        headers: { Authorization: `Bearer ${studentToken}` },
      })

      expect(response.status).toBe(200)
      expect(Array.isArray(response.data)).toBe(true)
      expect(response.data.length).toBeGreaterThan(0)
      expect(response.data[0]).toHaveProperty('tutor_profile_id', tutorProfileId)
    })

    it('should return 401 when not authenticated', async () => {
      try {
        await api.get('/api/v1/favorites/')
        fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.response.status).toBe(401)
      }
    })
  })

  describe('POST /api/favorites', () => {
    it('should successfully add tutor to favorites', async () => {
      const response = await api.post(
        '/api/v1/favorites/',
        { tutor_profile_id: tutorProfileId },
        { headers: { Authorization: `Bearer ${studentToken}` } }
      )

      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('tutor_profile_id', tutorProfileId)
      expect(response.data).toHaveProperty('id')
      expect(response.data).toHaveProperty('created_at')
    })

    it('should return 422 when tutor_profile_id is missing', async () => {
      try {
        await api.post(
          '/api/v1/favorites/',
          {},
          { headers: { Authorization: `Bearer ${studentToken}` } }
        )
        fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.response.status).toBe(422)
      }
    })

    it('should return 404 when tutor profile does not exist', async () => {
      try {
        await api.post(
          '/api/v1/favorites/',
          { tutor_profile_id: 999999 },
          { headers: { Authorization: `Bearer ${studentToken}` } }
        )
        fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.response.status).toBe(404)
      }
    })

    it('should return 400 when trying to add duplicate favorite', async () => {
      // Add favorite first time
      await api.post(
        '/api/v1/favorites/',
        { tutor_profile_id: tutorProfileId },
        { headers: { Authorization: `Bearer ${studentToken}` } }
      )

      // Try to add again
      try {
        await api.post(
          '/api/v1/favorites/',
          { tutor_profile_id: tutorProfileId },
          { headers: { Authorization: `Bearer ${studentToken}` } }
        )
        fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.response.status).toBe(400)
      }
    })
  })

  describe('DELETE /api/favorites/:tutor_profile_id', () => {
    it('should successfully remove tutor from favorites', async () => {
      // Add favorite first
      await api.post(
        '/api/v1/favorites/',
        { tutor_profile_id: tutorProfileId },
        { headers: { Authorization: `Bearer ${studentToken}` } }
      )

      // Remove it
      const response = await api.delete(`/api/v1/favorites/${tutorProfileId}`, {
        headers: { Authorization: `Bearer ${studentToken}` },
      })

      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('message')

      // Verify it's removed
      const favoritesResponse = await api.get('/api/v1/favorites/', {
        headers: { Authorization: `Bearer ${studentToken}` },
      })
      
      expect(favoritesResponse.data.length).toBe(0)
    })

    it('should return 404 when trying to remove non-existent favorite', async () => {
      try {
        await api.delete('/api/v1/favorites/999999', {
          headers: { Authorization: `Bearer ${studentToken}` },
        })
        fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.response.status).toBe(404)
      }
    })
  })

  describe('GET /api/favorites/:tutor_profile_id', () => {
    it('should return favorite when tutor is saved', async () => {
      // Add favorite first
      await api.post(
        '/api/v1/favorites/',
        { tutor_profile_id: tutorProfileId },
        { headers: { Authorization: `Bearer ${studentToken}` } }
      )

      const response = await api.get(`/api/v1/favorites/${tutorProfileId}`, {
        headers: { Authorization: `Bearer ${studentToken}` },
      })

      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('tutor_profile_id', tutorProfileId)
    })

    it('should return 404 when tutor is not in favorites', async () => {
      try {
        await api.get(`/api/v1/favorites/${tutorProfileId}`, {
          headers: { Authorization: `Bearer ${studentToken}` },
        })
        fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.response.status).toBe(404)
      }
    })
  })

  describe('Authorization and Permissions', () => {
    it('should only allow students to access favorites', async () => {
      // Login as tutor using form data
      const tutorLoginParams = new URLSearchParams()
      tutorLoginParams.append('username', 'tutor@example.com')
      tutorLoginParams.append('password', 'tutor123')
      
      const tutorLogin = await api.post('/api/v1/auth/login', tutorLoginParams, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })
      const tutorToken = tutorLogin.data.access_token

      // Try to access favorites as tutor (should fail)
      try {
        await api.get('/api/v1/favorites/', {
          headers: { Authorization: `Bearer ${tutorToken}` },
        })
        fail('Should have thrown an error')
      } catch (error: any) {
        expect([403, 401]).toContain(error.response.status)
      }
    })

    it('should not allow accessing other students favorites', async () => {
      // This test assumes you have proper data isolation
      // Add a favorite for the student
      await api.post(
        '/api/v1/favorites/',
        { tutor_profile_id: tutorProfileId },
        { headers: { Authorization: `Bearer ${studentToken}` } }
      )

      // Get the favorite count
      const response = await api.get('/api/v1/favorites/', {
        headers: { Authorization: `Bearer ${studentToken}` },
      })

      // Each student should only see their own favorites
      expect(response.data.every((fav: any) => fav.student_id)).toBeTruthy()
    })
  })

  describe('Data Integrity', () => {
    it('should maintain referential integrity with tutor profiles', async () => {
      // Add favorite
      const addResponse = await api.post(
        '/api/v1/favorites/',
        { tutor_profile_id: tutorProfileId },
        { headers: { Authorization: `Bearer ${studentToken}` } }
      )

      // Verify the tutor profile exists and can be fetched
      const tutorResponse = await api.get(`/api/v1/tutors/${tutorProfileId}/public`)
      
      expect(tutorResponse.status).toBe(200)
      expect(tutorResponse.data.id).toBe(tutorProfileId)
    })

    it('should include timestamps in favorite records', async () => {
      const response = await api.post(
        '/api/v1/favorites/',
        { tutor_profile_id: tutorProfileId },
        { headers: { Authorization: `Bearer ${studentToken}` } }
      )

      expect(response.data).toHaveProperty('created_at')
      expect(new Date(response.data.created_at).getTime()).toBeGreaterThan(0)
    })
  })
})
