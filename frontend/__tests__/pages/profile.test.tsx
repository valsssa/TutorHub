/**
 * Page-level tests for Profile pages
 *
 * Tests for user and tutor profile pages including:
 * - Profile information display
 * - Profile editing
 * - Tutor-specific features (reviews, subjects, availability)
 * - Public vs private profile views
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { auth, tutors, reviews, favorites, availability } from '@/lib/api';
import Cookies from 'js-cookie';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('js-cookie');

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: jest.fn(),
  }),
  usePathname: () => '/profile',
  useSearchParams: () => new URLSearchParams(),
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

// Mock user data
const mockStudentUser = {
  id: 1,
  email: 'student@example.com',
  role: 'student',
  is_active: true,
  is_verified: true,
  first_name: 'John',
  last_name: 'Doe',
  timezone: 'America/New_York',
  currency: 'USD',
  avatar_url: 'https://example.com/avatar.jpg',
  bio: 'Learning enthusiast',
  learning_goal: 'Master calculus',
};

const mockTutorUser = {
  id: 2,
  email: 'tutor@example.com',
  role: 'tutor',
  is_active: true,
  is_verified: true,
  first_name: 'Sarah',
  last_name: 'Johnson',
  timezone: 'America/New_York',
  currency: 'USD',
  avatar_url: 'https://example.com/tutor-avatar.jpg',
};

const mockTutorProfile = {
  id: 1,
  user_id: 2,
  title: 'Mathematics Expert',
  headline: 'PhD in Applied Mathematics',
  bio: 'Experienced tutor with 10+ years of teaching experience',
  hourly_rate: 75,
  average_rating: 4.9,
  total_reviews: 125,
  total_sessions: 500,
  experience_years: 10,
  languages: ['English', 'Spanish'],
  subjects: [
    { id: 1, name: 'Mathematics' },
    { id: 2, name: 'Calculus' },
    { id: 3, name: 'Statistics' },
  ],
  education: [
    { id: 1, institution: 'MIT', degree: 'PhD', field: 'Mathematics', year: 2015 },
  ],
  certifications: [
    { id: 1, name: 'Teaching Certificate', issuer: 'State Board', year: 2016 },
  ],
  availability: [
    { day_of_week: 1, start_time: '09:00', end_time: '17:00' },
    { day_of_week: 3, start_time: '09:00', end_time: '17:00' },
    { day_of_week: 5, start_time: '09:00', end_time: '17:00' },
  ],
  video_url: 'https://youtube.com/watch?v=example',
  status: 'approved',
  version: 1,
};

const mockReviews = [
  {
    id: 1,
    reviewer_name: 'Alice Smith',
    rating: 5,
    comment: 'Excellent tutor! Helped me understand complex concepts.',
    created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 2,
    reviewer_name: 'Bob Johnson',
    rating: 4,
    comment: 'Very patient and knowledgeable.',
    created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

describe('Student Profile Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockStudentUser);
  });

  it('renders student profile with user information', async () => {
    const ProfilePage = (await import('@/app/profile/page')).default;
    render(<ProfilePage />);

    await waitFor(() => {
      expect(auth.getCurrentUser).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('student@example.com')).toBeInTheDocument();
      expect(screen.getByText('Learning enthusiast')).toBeInTheDocument();
    });
  });

  it('displays avatar image', async () => {
    const ProfilePage = (await import('@/app/profile/page')).default;
    render(<ProfilePage />);

    await waitFor(() => {
      const avatar = screen.getByRole('img', { name: /avatar|profile/i });
      expect(avatar).toHaveAttribute('src', expect.stringContaining('avatar'));
    });
  });

  it('shows learning goal', async () => {
    const ProfilePage = (await import('@/app/profile/page')).default;
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('Master calculus')).toBeInTheDocument();
    });
  });

  it('links to edit profile settings', async () => {
    const ProfilePage = (await import('@/app/profile/page')).default;
    render(<ProfilePage />);

    await waitFor(() => {
      const editLink = screen.getByRole('link', { name: /edit.*profile|settings/i });
      expect(editLink).toHaveAttribute('href', expect.stringContaining('settings'));
    });
  });
});

describe('Tutor Profile Page - Own Profile', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockTutorUser);
    (tutors.getMyProfile as jest.Mock).mockResolvedValue(mockTutorProfile);
    (tutors.getReviews as jest.Mock).mockResolvedValue(mockReviews);
  });

  it('renders tutor profile with professional information', async () => {
    const TutorProfilePage = (await import('@/app/tutor/profile/page')).default;
    render(<TutorProfilePage />);

    await waitFor(() => {
      expect(tutors.getMyProfile).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText('Mathematics Expert')).toBeInTheDocument();
      expect(screen.getByText('PhD in Applied Mathematics')).toBeInTheDocument();
      expect(screen.getByText(/75.*hour/i)).toBeInTheDocument();
    });
  });

  it('displays subjects list', async () => {
    const TutorProfilePage = (await import('@/app/tutor/profile/page')).default;
    render(<TutorProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('Mathematics')).toBeInTheDocument();
      expect(screen.getByText('Calculus')).toBeInTheDocument();
      expect(screen.getByText('Statistics')).toBeInTheDocument();
    });
  });

  it('displays education and certifications', async () => {
    const TutorProfilePage = (await import('@/app/tutor/profile/page')).default;
    render(<TutorProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('MIT')).toBeInTheDocument();
      expect(screen.getByText(/PhD.*Mathematics/i)).toBeInTheDocument();
      expect(screen.getByText('Teaching Certificate')).toBeInTheDocument();
    });
  });

  it('displays rating and review count', async () => {
    const TutorProfilePage = (await import('@/app/tutor/profile/page')).default;
    render(<TutorProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('4.9')).toBeInTheDocument();
      expect(screen.getByText(/125.*review/i)).toBeInTheDocument();
    });
  });

  it('shows edit profile button for own profile', async () => {
    const TutorProfilePage = (await import('@/app/tutor/profile/page')).default;
    render(<TutorProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit.*profile/i })).toBeInTheDocument();
    });
  });

  it('shows availability schedule', async () => {
    const TutorProfilePage = (await import('@/app/tutor/profile/page')).default;
    render(<TutorProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/availability|schedule/i)).toBeInTheDocument();
      expect(screen.getByText(/monday|wednesday|friday/i)).toBeInTheDocument();
    });
  });
});

describe('Tutor Profile Page - Public View', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockStudentUser);
    (tutors.getPublic as jest.Mock).mockResolvedValue(mockTutorProfile);
    (tutors.getReviews as jest.Mock).mockResolvedValue(mockReviews);
    (favorites.checkFavorite as jest.Mock).mockResolvedValue(null);
  });

  it('renders public tutor profile', async () => {
    const TutorPublicPage = (await import('@/app/tutors/[id]/page')).default;
    render(<TutorPublicPage params={{ id: '1' }} />);

    await waitFor(() => {
      expect(tutors.getPublic).toHaveBeenCalledWith(1);
    });

    await waitFor(() => {
      expect(screen.getByText('Mathematics Expert')).toBeInTheDocument();
    });
  });

  it('shows book session button', async () => {
    const TutorPublicPage = (await import('@/app/tutors/[id]/page')).default;
    render(<TutorPublicPage params={{ id: '1' }} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /book.*session/i })).toBeInTheDocument();
    });
  });

  it('shows message button', async () => {
    const TutorPublicPage = (await import('@/app/tutors/[id]/page')).default;
    render(<TutorPublicPage params={{ id: '1' }} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /message/i })).toBeInTheDocument();
    });
  });

  it('shows save/favorite button', async () => {
    const TutorPublicPage = (await import('@/app/tutors/[id]/page')).default;
    render(<TutorPublicPage params={{ id: '1' }} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save|favorite/i })).toBeInTheDocument();
    });
  });

  it('toggles favorite status', async () => {
    const user = userEvent.setup();

    (favorites.addFavorite as jest.Mock).mockResolvedValue({ id: 1, tutor_profile_id: 1 });

    const TutorPublicPage = (await import('@/app/tutors/[id]/page')).default;
    render(<TutorPublicPage params={{ id: '1' }} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save|favorite/i })).toBeInTheDocument();
    });

    const favoriteButton = screen.getByRole('button', { name: /save|favorite/i });
    await user.click(favoriteButton);

    await waitFor(() => {
      expect(favorites.addFavorite).toHaveBeenCalledWith(1);
    });
  });

  it('displays reviews section', async () => {
    const TutorPublicPage = (await import('@/app/tutors/[id]/page')).default;
    render(<TutorPublicPage params={{ id: '1' }} />);

    await waitFor(() => {
      expect(tutors.getReviews).toHaveBeenCalledWith(1);
    });

    await waitFor(() => {
      expect(screen.getByText('Excellent tutor!')).toBeInTheDocument();
      expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    });
  });

  it('hides edit button for other profiles', async () => {
    const TutorPublicPage = (await import('@/app/tutors/[id]/page')).default;
    render(<TutorPublicPage params={{ id: '1' }} />);

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /edit.*profile/i })).not.toBeInTheDocument();
    });
  });
});

describe('Tutor Profile Editing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockTutorUser);
    (tutors.getMyProfile as jest.Mock).mockResolvedValue(mockTutorProfile);
  });

  it('allows editing about section', async () => {
    const user = userEvent.setup();

    (tutors.updateAbout as jest.Mock).mockResolvedValue({
      ...mockTutorProfile,
      title: 'Updated Title',
    });

    const TutorProfilePage = (await import('@/app/tutor/profile/page')).default;
    render(<TutorProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit.*profile/i })).toBeInTheDocument();
    });

    // Click edit
    const editButton = screen.getByRole('button', { name: /edit.*profile/i });
    await user.click(editButton);

    // Update title
    const titleInput = await screen.findByLabelText(/title/i);
    await user.clear(titleInput);
    await user.type(titleInput, 'Updated Title');

    // Save
    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(tutors.updateAbout).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Updated Title' })
      );
      expect(toastMocks.showSuccess).toHaveBeenCalled();
    });
  });

  it('allows updating hourly rate', async () => {
    const user = userEvent.setup();

    (tutors.updatePricing as jest.Mock).mockResolvedValue({
      ...mockTutorProfile,
      hourly_rate: 80,
    });

    const TutorProfilePage = (await import('@/app/tutor/profile/page')).default;
    render(<TutorProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit.*price|edit.*rate/i })).toBeInTheDocument();
    });

    const editPriceButton = screen.getByRole('button', { name: /edit.*price|edit.*rate/i });
    await user.click(editPriceButton);

    const rateInput = await screen.findByLabelText(/hourly.*rate/i);
    await user.clear(rateInput);
    await user.type(rateInput, '80');

    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(tutors.updatePricing).toHaveBeenCalledWith(
        expect.objectContaining({ hourly_rate: 80 })
      );
    });
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();

    const TutorProfilePage = (await import('@/app/tutor/profile/page')).default;
    render(<TutorProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit.*profile/i })).toBeInTheDocument();
    });

    const editButton = screen.getByRole('button', { name: /edit.*profile/i });
    await user.click(editButton);

    // Clear required field
    const titleInput = await screen.findByLabelText(/title/i);
    await user.clear(titleInput);

    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/title.*required/i)).toBeInTheDocument();
    });

    expect(tutors.updateAbout).not.toHaveBeenCalled();
  });
});

describe('Tutor Availability Management', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockTutorUser);
    (tutors.getMyProfile as jest.Mock).mockResolvedValue(mockTutorProfile);
    (availability.getMyAvailability as jest.Mock).mockResolvedValue(mockTutorProfile.availability);
  });

  it('displays current availability schedule', async () => {
    const SchedulePage = (await import('@/app/tutor/schedule/page')).default;
    render(<SchedulePage />);

    await waitFor(() => {
      expect(availability.getMyAvailability).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText(/monday/i)).toBeInTheDocument();
      expect(screen.getByText(/09:00.*17:00|9.*AM.*5.*PM/i)).toBeInTheDocument();
    });
  });

  it('allows adding new availability slot', async () => {
    const user = userEvent.setup();

    (availability.createAvailability as jest.Mock).mockResolvedValue({
      id: 4,
      day_of_week: 2,
      start_time: '10:00',
      end_time: '18:00',
    });

    const SchedulePage = (await import('@/app/tutor/schedule/page')).default;
    render(<SchedulePage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add.*slot|add.*time/i })).toBeInTheDocument();
    });

    const addButton = screen.getByRole('button', { name: /add.*slot|add.*time/i });
    await user.click(addButton);

    // Select day
    const daySelect = await screen.findByLabelText(/day/i);
    await user.selectOptions(daySelect, '2'); // Tuesday

    // Select times
    const startInput = screen.getByLabelText(/start.*time/i);
    await user.type(startInput, '10:00');

    const endInput = screen.getByLabelText(/end.*time/i);
    await user.type(endInput, '18:00');

    const saveButton = screen.getByRole('button', { name: /save|add/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(availability.createAvailability).toHaveBeenCalledWith(
        expect.objectContaining({
          day_of_week: 2,
          start_time: '10:00',
          end_time: '18:00',
        })
      );
    });
  });

  it('allows deleting availability slot', async () => {
    const user = userEvent.setup();

    (availability.deleteAvailability as jest.Mock).mockResolvedValue({});

    const SchedulePage = (await import('@/app/tutor/schedule/page')).default;
    render(<SchedulePage />);

    await waitFor(() => {
      expect(screen.getByText(/monday/i)).toBeInTheDocument();
    });

    const deleteButton = screen.getAllByRole('button', { name: /delete|remove/i })[0];
    await user.click(deleteButton);

    // Confirm deletion
    const confirmButton = await screen.findByRole('button', { name: /confirm|yes/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(availability.deleteAvailability).toHaveBeenCalled();
    });
  });
});

describe('Profile Loading and Error States', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
  });

  it('shows loading state during profile fetch', async () => {
    (auth.getCurrentUser as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockStudentUser), 500))
    );

    const ProfilePage = (await import('@/app/profile/page')).default;
    render(<ProfilePage />);

    expect(screen.getByTestId('loading-spinner') || screen.getByText(/loading/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  it('shows error when profile fails to load', async () => {
    (auth.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Failed to load profile'));

    const ProfilePage = (await import('@/app/profile/page')).default;
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/error|failed.*load/i)).toBeInTheDocument();
    });
  });

  it('shows 404 for non-existent tutor profile', async () => {
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockStudentUser);
    (tutors.getPublic as jest.Mock).mockRejectedValue({
      response: { status: 404, data: { detail: 'Tutor not found' } },
    });

    const TutorPublicPage = (await import('@/app/tutors/[id]/page')).default;
    render(<TutorPublicPage params={{ id: '999' }} />);

    await waitFor(() => {
      expect(screen.getByText(/not.*found|doesn't.*exist/i)).toBeInTheDocument();
    });
  });

  it('handles update error gracefully', async () => {
    const user = userEvent.setup();

    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockTutorUser);
    (tutors.getMyProfile as jest.Mock).mockResolvedValue(mockTutorProfile);
    (tutors.updateAbout as jest.Mock).mockRejectedValue(
      new Error('Failed to update profile')
    );

    const TutorProfilePage = (await import('@/app/tutor/profile/page')).default;
    render(<TutorProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit.*profile/i })).toBeInTheDocument();
    });

    const editButton = screen.getByRole('button', { name: /edit.*profile/i });
    await user.click(editButton);

    const titleInput = await screen.findByLabelText(/title/i);
    await user.clear(titleInput);
    await user.type(titleInput, 'New Title');

    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(toastMocks.showError).toHaveBeenCalled();
    });
  });
});
