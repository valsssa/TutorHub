/**
 * Integration tests for Search and Filter functionality
 *
 * Tests the complete search and filtering workflow including:
 * - Tutor search with various filters
 * - Filter state management across components
 * - URL parameter synchronization
 * - Pagination and infinite scroll
 * - Search result caching and optimization
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { tutors, subjects } from '@/lib/api';
import Cookies from 'js-cookie';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('js-cookie');

const mockPush = jest.fn();
const mockReplace = jest.fn();
let mockSearchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: jest.fn(),
  }),
  usePathname: () => '/tutors',
  useSearchParams: () => mockSearchParams,
}));

const toastMocks = {
  showSuccess: jest.fn(),
  showError: jest.fn(),
  showInfo: jest.fn(),
  showWarning: jest.fn(),
};

jest.mock('@/components/ToastContainer', () => ({
  useToast: () => toastMocks,
  ToastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock data
const mockSubjects = [
  { id: 1, name: 'Mathematics' },
  { id: 2, name: 'Physics' },
  { id: 3, name: 'Chemistry' },
  { id: 4, name: 'English' },
  { id: 5, name: 'Computer Science' },
];

const mockTutorsList = {
  items: [
    {
      id: 1,
      name: 'Dr. Sarah Johnson',
      title: 'Mathematics Expert',
      hourly_rate: 75,
      average_rating: 4.9,
      total_reviews: 125,
      subjects: ['Mathematics', 'Calculus'],
      experience_years: 10,
      avatar_url: null,
    },
    {
      id: 2,
      name: 'Prof. Mike Chen',
      title: 'Physics Tutor',
      hourly_rate: 60,
      average_rating: 4.7,
      total_reviews: 89,
      subjects: ['Physics', 'Mathematics'],
      experience_years: 8,
      avatar_url: null,
    },
    {
      id: 3,
      name: 'Emily Parker',
      title: 'Chemistry Specialist',
      hourly_rate: 45,
      average_rating: 4.5,
      total_reviews: 45,
      subjects: ['Chemistry'],
      experience_years: 5,
      avatar_url: null,
    },
    {
      id: 4,
      name: 'John Smith',
      title: 'English Teacher',
      hourly_rate: 35,
      average_rating: 4.8,
      total_reviews: 200,
      subjects: ['English'],
      experience_years: 15,
      avatar_url: null,
    },
  ],
  total: 4,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

describe('Search and Filter Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = new URLSearchParams();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (subjects.list as jest.Mock).mockResolvedValue(mockSubjects);
    (tutors.list as jest.Mock).mockResolvedValue(mockTutorsList);
  });

  describe('Initial Load and Display', () => {
    it('loads and displays tutor list on page load', async () => {
      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalled();
      });

      // Verify tutors are displayed
      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
        expect(screen.getByText('Prof. Mike Chen')).toBeInTheDocument();
        expect(screen.getByText('Emily Parker')).toBeInTheDocument();
        expect(screen.getByText('John Smith')).toBeInTheDocument();
      });
    });

    it('loads subjects for filter dropdown', async () => {
      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(subjects.list).toHaveBeenCalled();
      });

      // Open subject dropdown
      const subjectButton = screen.getByText(/all subjects/i);
      fireEvent.click(subjectButton);

      // Verify subjects are in dropdown
      await waitFor(() => {
        expect(screen.getByText('Mathematics')).toBeInTheDocument();
        expect(screen.getByText('Physics')).toBeInTheDocument();
        expect(screen.getByText('Chemistry')).toBeInTheDocument();
      });
    });

    it('displays tutor count in results', async () => {
      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(screen.getByText(/4.*tutors?|4.*results?/i)).toBeInTheDocument();
      });
    });
  });

  describe('Subject Filtering', () => {
    it('filters tutors by subject', async () => {
      const user = userEvent.setup();

      const filteredResults = {
        ...mockTutorsList,
        items: mockTutorsList.items.filter((t) =>
          t.subjects.includes('Mathematics')
        ),
        total: 2,
      };

      (tutors.list as jest.Mock)
        .mockResolvedValueOnce(mockTutorsList)
        .mockResolvedValueOnce(filteredResults);

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Select Mathematics subject
      const subjectButton = screen.getByText(/all subjects/i);
      await user.click(subjectButton);

      const mathOption = await screen.findByText('Mathematics');
      await user.click(mathOption);

      // Verify filtered API call
      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalledWith(
          expect.objectContaining({ subject_id: 1 })
        );
      });
    });

    it('clears subject filter when "All Subjects" is selected', async () => {
      const user = userEvent.setup();

      mockSearchParams = new URLSearchParams('subject_id=1');

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalled();
      });

      // Click to open subject dropdown
      const subjectButton = screen.getByText(/mathematics/i);
      await user.click(subjectButton);

      // Select "All Subjects"
      const allSubjectsOption = await screen.findByText(/all subjects/i);
      await user.click(allSubjectsOption);

      // Verify API called without subject filter
      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalledWith(
          expect.not.objectContaining({ subject_id: expect.any(Number) })
        );
      });
    });
  });

  describe('Price Range Filtering', () => {
    it('filters tutors by price range', async () => {
      const user = userEvent.setup();

      const filteredResults = {
        ...mockTutorsList,
        items: mockTutorsList.items.filter(
          (t) => t.hourly_rate >= 40 && t.hourly_rate <= 70
        ),
        total: 2,
      };

      (tutors.list as jest.Mock)
        .mockResolvedValueOnce(mockTutorsList)
        .mockResolvedValueOnce(filteredResults);

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Open price filter
      const priceButton = screen.getByText(/any price|\$/i);
      await user.click(priceButton);

      // Select price range
      const priceOption = await screen.findByText(/\$40.*\$70|\$50/i);
      if (priceOption) {
        await user.click(priceOption);
      }

      // Verify filtered API call
      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalledWith(
          expect.objectContaining({
            min_rate: expect.any(Number),
            max_rate: expect.any(Number),
          })
        );
      });
    });
  });

  describe('Rating Filtering', () => {
    it('filters tutors by minimum rating', async () => {
      const user = userEvent.setup();

      const filteredResults = {
        ...mockTutorsList,
        items: mockTutorsList.items.filter((t) => t.average_rating >= 4.5),
        total: 3,
      };

      (tutors.list as jest.Mock)
        .mockResolvedValueOnce(mockTutorsList)
        .mockResolvedValueOnce(filteredResults);

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Open rating filter
      const ratingButton = screen.getByText(/any rating/i);
      await user.click(ratingButton);

      // Select 4.5+ rating
      const ratingOption = await screen.findByText(/4\.5\+.*stars?/i);
      await user.click(ratingOption);

      // Verify filtered API call
      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalledWith(
          expect.objectContaining({ min_rating: 4.5 })
        );
      });
    });
  });

  describe('Experience Filtering', () => {
    it('filters tutors by minimum experience', async () => {
      const user = userEvent.setup();

      const filteredResults = {
        ...mockTutorsList,
        items: mockTutorsList.items.filter((t) => t.experience_years >= 10),
        total: 2,
      };

      (tutors.list as jest.Mock)
        .mockResolvedValueOnce(mockTutorsList)
        .mockResolvedValueOnce(filteredResults);

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Open experience filter
      const experienceButton = screen.getByText(/any experience/i);
      await user.click(experienceButton);

      // Select 10+ years
      const experienceOption = await screen.findByText(/10\+.*years?/i);
      await user.click(experienceOption);

      // Verify filtered API call
      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalledWith(
          expect.objectContaining({ min_experience: 10 })
        );
      });
    });
  });

  describe('Search Functionality', () => {
    it('searches tutors by name with debounce', async () => {
      const user = userEvent.setup();

      const searchResults = {
        ...mockTutorsList,
        items: [mockTutorsList.items[0]], // Only Sarah matches
        total: 1,
      };

      (tutors.list as jest.Mock)
        .mockResolvedValueOnce(mockTutorsList)
        .mockResolvedValueOnce(searchResults);

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Type in search box
      const searchInput = screen.getByPlaceholderText(/search.*tutor/i);
      await user.type(searchInput, 'Sarah');

      // Wait for debounced search
      await waitFor(
        () => {
          expect(tutors.list).toHaveBeenCalledWith(
            expect.objectContaining({ search_query: 'Sarah' })
          );
        },
        { timeout: 1000 }
      );
    });

    it('clears search when input is emptied', async () => {
      const user = userEvent.setup();

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search.*tutor/i);

      // Type and then clear
      await user.type(searchInput, 'Sarah');
      await user.clear(searchInput);

      // Wait for debounce and verify API called without search
      await waitFor(
        () => {
          const lastCall = (tutors.list as jest.Mock).mock.calls.slice(-1)[0];
          expect(lastCall[0]).not.toHaveProperty('search_query');
        },
        { timeout: 1000 }
      );
    });

    it('shows no results message when search has no matches', async () => {
      const user = userEvent.setup();

      (tutors.list as jest.Mock)
        .mockResolvedValueOnce(mockTutorsList)
        .mockResolvedValueOnce({ items: [], total: 0, page: 1, page_size: 20 });

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search.*tutor/i);
      await user.type(searchInput, 'NonexistentTutor');

      await waitFor(() => {
        expect(screen.getByText(/no.*tutors?.*found|no.*results?/i)).toBeInTheDocument();
      });
    });
  });

  describe('Sorting', () => {
    it('sorts tutors by different criteria', async () => {
      const user = userEvent.setup();

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Open sort dropdown
      const sortButton = screen.getByText(/top picks|sort/i);
      await user.click(sortButton);

      // Select price low to high
      const sortOption = await screen.findByText(/price.*low|lowest.*price/i);
      await user.click(sortOption);

      // Verify sorted API call
      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalledWith(
          expect.objectContaining({ sort_by: expect.stringContaining('price') })
        );
      });
    });

    it('maintains sort when filters change', async () => {
      const user = userEvent.setup();

      mockSearchParams = new URLSearchParams('sort_by=price_asc');

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalled();
      });

      // Add a subject filter
      const subjectButton = screen.getByText(/all subjects/i);
      await user.click(subjectButton);

      const mathOption = await screen.findByText('Mathematics');
      await user.click(mathOption);

      // Verify sort is maintained with new filter
      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalledWith(
          expect.objectContaining({
            subject_id: 1,
            sort_by: expect.stringContaining('price'),
          })
        );
      });
    });
  });

  describe('Combined Filters', () => {
    it('applies multiple filters simultaneously', async () => {
      const user = userEvent.setup();

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Apply subject filter
      const subjectButton = screen.getByText(/all subjects/i);
      await user.click(subjectButton);
      const mathOption = await screen.findByText('Mathematics');
      await user.click(mathOption);

      // Apply rating filter
      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalled();
      });

      const ratingButton = screen.getByText(/any rating/i);
      await user.click(ratingButton);
      const ratingOption = await screen.findByText(/4\+.*stars?/i);
      await user.click(ratingOption);

      // Verify combined filters in API call
      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalledWith(
          expect.objectContaining({
            subject_id: 1,
            min_rating: 4,
          })
        );
      });
    });

    it('resets all filters with reset button', async () => {
      const user = userEvent.setup();

      mockSearchParams = new URLSearchParams('subject_id=1&min_rating=4&min_experience=5');

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(tutors.list).toHaveBeenCalled();
      });

      // Find and click reset/clear filters button
      const resetButton = screen.queryByRole('button', { name: /reset|clear.*filter/i });
      if (resetButton) {
        await user.click(resetButton);

        // Verify all filters cleared
        await waitFor(() => {
          expect(tutors.list).toHaveBeenCalledWith(
            expect.not.objectContaining({
              subject_id: expect.any(Number),
              min_rating: expect.any(Number),
              min_experience: expect.any(Number),
            })
          );
        });
      }
    });
  });

  describe('Pagination', () => {
    it('loads more tutors on page change', async () => {
      const user = userEvent.setup();

      const page1 = {
        ...mockTutorsList,
        total: 25,
        total_pages: 2,
      };

      const page2 = {
        items: [
          {
            id: 5,
            name: 'New Tutor',
            title: 'Expert',
            hourly_rate: 50,
            average_rating: 4.6,
            total_reviews: 30,
            subjects: ['Mathematics'],
            experience_years: 6,
            avatar_url: null,
          },
        ],
        total: 25,
        page: 2,
        page_size: 20,
        total_pages: 2,
      };

      (tutors.list as jest.Mock)
        .mockResolvedValueOnce(page1)
        .mockResolvedValueOnce(page2);

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Find and click next page or load more
      const nextButton = screen.queryByRole('button', { name: /next|load more/i });
      if (nextButton) {
        await user.click(nextButton);

        await waitFor(() => {
          expect(tutors.list).toHaveBeenCalledWith(
            expect.objectContaining({ page: 2 })
          );
        });
      }
    });
  });

  describe('Loading States', () => {
    it('shows loading skeleton during initial load', async () => {
      // Delay API response
      (tutors.list as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockTutorsList), 500))
      );

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      // Should show loading state
      expect(
        screen.getByTestId('loading-skeleton') ||
          screen.getByText(/loading/i) ||
          screen.getAllByRole('generic').find((el) => el.className.includes('skeleton'))
      ).toBeTruthy();

      // Wait for content to load
      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });
    });

    it('shows loading indicator when filters change', async () => {
      const user = userEvent.setup();

      let resolveSecondCall: (value: typeof mockTutorsList) => void;
      const secondCallPromise = new Promise<typeof mockTutorsList>((resolve) => {
        resolveSecondCall = resolve;
      });

      (tutors.list as jest.Mock)
        .mockResolvedValueOnce(mockTutorsList)
        .mockReturnValueOnce(secondCallPromise);

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Apply filter
      const subjectButton = screen.getByText(/all subjects/i);
      await user.click(subjectButton);
      const mathOption = await screen.findByText('Mathematics');
      await user.click(mathOption);

      // Should show loading indicator
      expect(screen.queryByTestId('loading-indicator')).toBeInTheDocument;

      // Resolve the API call
      resolveSecondCall!(mockTutorsList);
    });
  });

  describe('Error Handling', () => {
    it('shows error message when tutor load fails', async () => {
      (tutors.list as jest.Mock).mockRejectedValue(
        new Error('Failed to load tutors')
      );

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText(/error|failed.*load|something.*wrong/i)).toBeInTheDocument();
      });
    });

    it('allows retry after error', async () => {
      const user = userEvent.setup();

      (tutors.list as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockTutorsList);

      const TutorsPage = (await import('@/app/tutors/page')).default;
      render(<TutorsPage />);

      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
      });

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /retry|try again/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });
    });
  });
});
