import { favorites } from '@/lib/api'
import axios from 'axios'

// Mock axios
jest.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('Favorites API', () => {
  const mockFavorite = {
    id: 1,
    student_id: 1,
    tutor_profile_id: 2,
    created_at: '2024-01-01T00:00:00Z',
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getFavorites', () => {
    it('should fetch user favorites successfully', async () => {
      const mockResponse = [mockFavorite]
      mockedAxios.get.mockResolvedValue({ data: mockResponse })

      const result = await favorites.getFavorites()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/favorites')
      expect(result).toEqual(mockResponse)
    })

    it('should handle API errors', async () => {
      const errorMessage = 'Failed to fetch favorites'
      mockedAxios.get.mockRejectedValue(new Error(errorMessage))

      await expect(favorites.getFavorites()).rejects.toThrow(errorMessage)
    })

    it('should return empty array when no favorites', async () => {
      mockedAxios.get.mockResolvedValue({ data: [] })

      const result = await favorites.getFavorites()

      expect(result).toEqual([])
    })
  })

  describe('addFavorite', () => {
    it('should add tutor to favorites successfully', async () => {
      const tutorProfileId = 2
      mockedAxios.post.mockResolvedValue({ data: mockFavorite })

      const result = await favorites.addFavorite(tutorProfileId)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/favorites', {
        tutor_profile_id: tutorProfileId,
      })
      expect(result).toEqual(mockFavorite)
    })

    it('should handle API errors when adding favorite', async () => {
      const errorMessage = 'Tutor not found'
      mockedAxios.post.mockRejectedValue(new Error(errorMessage))

      await expect(favorites.addFavorite(999)).rejects.toThrow(errorMessage)
    })
  })

  describe('removeFavorite', () => {
    it('should remove tutor from favorites successfully', async () => {
      const tutorProfileId = 2
      mockedAxios.delete.mockResolvedValue({ data: { message: 'Removed successfully' } })

      await expect(favorites.removeFavorite(tutorProfileId)).resolves.toBeUndefined()

      expect(mockedAxios.delete).toHaveBeenCalledWith(`/api/favorites/${tutorProfileId}`)
    })

    it('should handle API errors when removing favorite', async () => {
      const errorMessage = 'Favorite not found'
      mockedAxios.delete.mockRejectedValue(new Error(errorMessage))

      await expect(favorites.removeFavorite(999)).rejects.toThrow(errorMessage)
    })
  })

  describe('checkFavorite', () => {
    it('should check favorite status successfully', async () => {
      const tutorProfileId = 2
      mockedAxios.get.mockResolvedValue({ status: 200, data: mockFavorite })

      const result = await favorites.checkFavorite(tutorProfileId)

      expect(mockedAxios.get).toHaveBeenCalledWith(`/api/favorites/${tutorProfileId}`, {
        suppressErrorLog: true,
        validateStatus: expect.any(Function),
      })
      expect(result).toEqual(mockFavorite)
    })

    it('should return null when tutor is not in favorites', async () => {
      mockedAxios.get.mockResolvedValue({ status: 404, data: { detail: 'Tutor is not in favorites' } })

      await expect(favorites.checkFavorite(999)).resolves.toBeNull()
    })
  })

  describe('error handling', () => {
    it('should handle network errors', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network Error'))

      await expect(favorites.getFavorites()).rejects.toThrow('Network Error')
    })

    it('should handle 401 unauthorized errors', async () => {
      const error = {
        response: { status: 401, data: { detail: 'Unauthorized' } },
      }
      mockedAxios.get.mockRejectedValue(error)

      await expect(favorites.getFavorites()).rejects.toThrow()
    })

    it('should handle 403 forbidden errors', async () => {
      const error = {
        response: { status: 403, data: { detail: 'Forbidden' } },
      }
      mockedAxios.post.mockRejectedValue(error)

      await expect(favorites.addFavorite(1)).rejects.toThrow()
    })

    it('should handle 404 not found errors', async () => {
      const error = {
        response: { status: 404, data: { detail: 'Not found' } },
      }
      mockedAxios.delete.mockRejectedValue(error)

      await expect(favorites.removeFavorite(999)).rejects.toThrow()
    })
  })

  describe('API payload structure', () => {
    it('should send correct payload for adding favorites', async () => {
      const tutorProfileId = 123
      mockedAxios.post.mockResolvedValue({ data: mockFavorite })

      await favorites.addFavorite(tutorProfileId)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/favorites', {
        tutor_profile_id: tutorProfileId,
      })
    })

    it('should use correct endpoints', async () => {
      mockedAxios.get.mockResolvedValue({ data: [] })
      mockedAxios.post.mockResolvedValue({ data: mockFavorite })
      mockedAxios.delete.mockResolvedValue({ data: {} })

      await favorites.getFavorites()
      await favorites.addFavorite(1)
      await favorites.removeFavorite(1)
      await favorites.checkFavorite(1)

      expect(mockedAxios.get).toHaveBeenCalledTimes(2)
      expect(mockedAxios.post).toHaveBeenCalledTimes(1)
      expect(mockedAxios.delete).toHaveBeenCalledTimes(1)

      expect(mockedAxios.get).toHaveBeenNthCalledWith(1, '/api/favorites')
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/favorites', { tutor_profile_id: 1 })
      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/favorites/1')
      expect(mockedAxios.get).toHaveBeenNthCalledWith(2, '/api/favorites/1', {
        suppressErrorLog: true,
        validateStatus: expect.any(Function),
      })
    })
  })
})
