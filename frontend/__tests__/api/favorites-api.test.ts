import { favorites } from '@/lib/api'

// Use the global mockAxiosInstance from jest.setup.js
const mockAxiosInstance = (globalThis as any).mockAxiosInstance

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
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const result = await favorites.getFavorites()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/v1/favorites')
      expect(result).toEqual(mockResponse)
    })

    it('should handle API errors', async () => {
      const errorMessage = 'Failed to fetch favorites'
      mockAxiosInstance.get.mockRejectedValue(new Error(errorMessage))

      await expect(favorites.getFavorites()).rejects.toThrow(errorMessage)
    })

    it('should return empty array when no favorites', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] })

      const result = await favorites.getFavorites()

      expect(result).toEqual([])
    })
  })

  describe('addFavorite', () => {
    it('should add tutor to favorites successfully', async () => {
      const tutorProfileId = 2
      mockAxiosInstance.post.mockResolvedValue({ data: mockFavorite })

      const result = await favorites.addFavorite(tutorProfileId)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/favorites', {
        tutor_profile_id: tutorProfileId,
      })
      expect(result).toEqual(mockFavorite)
    })

    it('should handle API errors when adding favorite', async () => {
      const errorMessage = 'Tutor not found'
      mockAxiosInstance.post.mockRejectedValue(new Error(errorMessage))

      await expect(favorites.addFavorite(999)).rejects.toThrow(errorMessage)
    })
  })

  describe('removeFavorite', () => {
    it('should remove tutor from favorites successfully', async () => {
      const tutorProfileId = 2
      mockAxiosInstance.delete.mockResolvedValue({ data: { message: 'Removed successfully' } })

      await expect(favorites.removeFavorite(tutorProfileId)).resolves.toBeUndefined()

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(`/api/v1/favorites/${tutorProfileId}`)
    })

    it('should handle API errors when removing favorite', async () => {
      const errorMessage = 'Favorite not found'
      mockAxiosInstance.delete.mockRejectedValue(new Error(errorMessage))

      await expect(favorites.removeFavorite(999)).rejects.toThrow(errorMessage)
    })
  })

  describe('checkFavorite', () => {
    it('should check favorite status successfully', async () => {
      const tutorProfileId = 2
      mockAxiosInstance.get.mockResolvedValue({ status: 200, data: mockFavorite })

      const result = await favorites.checkFavorite(tutorProfileId)

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(`/api/v1/favorites/${tutorProfileId}`, {
        suppressErrorLog: true,
        validateStatus: expect.any(Function),
      })
      expect(result).toEqual(mockFavorite)
    })

    it('should return null when tutor is not in favorites', async () => {
      mockAxiosInstance.get.mockResolvedValue({ status: 404, data: { detail: 'Tutor is not in favorites' } })

      await expect(favorites.checkFavorite(999)).resolves.toBeNull()
    })
  })

  describe('error handling', () => {
    it('should handle network errors', async () => {
      mockAxiosInstance.get.mockRejectedValue(new Error('Network Error'))

      await expect(favorites.getFavorites()).rejects.toThrow('Network Error')
    })

    it('should handle 401 unauthorized errors', async () => {
      const error = {
        response: { status: 401, data: { detail: 'Unauthorized' } },
      }
      mockAxiosInstance.get.mockRejectedValue(error)

      await expect(favorites.getFavorites()).rejects.toThrow()
    })

    it('should handle 403 forbidden errors', async () => {
      const error = {
        response: { status: 403, data: { detail: 'Forbidden' } },
      }
      mockAxiosInstance.post.mockRejectedValue(error)

      await expect(favorites.addFavorite(1)).rejects.toThrow()
    })

    it('should handle 404 not found errors', async () => {
      const error = {
        response: { status: 404, data: { detail: 'Not found' } },
      }
      mockAxiosInstance.delete.mockRejectedValue(error)

      await expect(favorites.removeFavorite(999)).rejects.toThrow()
    })
  })

  describe('API payload structure', () => {
    it('should send correct payload for adding favorites', async () => {
      const tutorProfileId = 123
      mockAxiosInstance.post.mockResolvedValue({ data: mockFavorite })

      await favorites.addFavorite(tutorProfileId)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/favorites', {
        tutor_profile_id: tutorProfileId,
      })
    })

    it('should use correct endpoints', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] })
      mockAxiosInstance.post.mockResolvedValue({ data: mockFavorite })
      mockAxiosInstance.delete.mockResolvedValue({ data: {} })

      await favorites.getFavorites()
      await favorites.addFavorite(1)
      await favorites.removeFavorite(1)
      await favorites.checkFavorite(1)

      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2)
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(1)
      expect(mockAxiosInstance.delete).toHaveBeenCalledTimes(1)

      expect(mockAxiosInstance.get).toHaveBeenNthCalledWith(1, '/api/v1/favorites')
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/favorites', { tutor_profile_id: 1 })
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/api/v1/favorites/1')
      expect(mockAxiosInstance.get).toHaveBeenNthCalledWith(2, '/api/v1/favorites/1', {
        suppressErrorLog: true,
        validateStatus: expect.any(Function),
      })
    })
  })
})
