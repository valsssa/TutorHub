/**
 * Tests for ProfileCompletionMeter component
 * Tests profile completion tracking and navigation for tutor onboarding
 */

import { render, screen, fireEvent } from '@testing-library/react';
import ProfileCompletionMeter from '@/components/ProfileCompletionMeter';
import { TutorProfile } from '@/types';

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  CheckCircle: ({ className }: { className?: string }) => (
    <span data-testid="check-circle" className={className}>CheckCircle</span>
  ),
  Circle: ({ className }: { className?: string }) => (
    <span data-testid="circle" className={className}>Circle</span>
  ),
  ChevronRight: ({ className }: { className?: string }) => (
    <span data-testid="chevron-right" className={className}>ChevronRight</span>
  ),
}));

// Helper to create a base tutor profile with minimal required fields
const createBaseProfile = (overrides: Partial<TutorProfile> = {}): TutorProfile => ({
  id: 1,
  user_id: 1,
  name: 'Test Tutor',
  title: '',
  bio: '',
  hourly_rate: 0,
  experience_years: 0,
  languages: ['English'],
  average_rating: 0,
  total_reviews: 0,
  total_sessions: 0,
  is_approved: false,
  profile_status: 'incomplete',
  version: 1,
  // Extended fields used by ProfileCompletionMeter (may differ from TutorProfile type)
  ...overrides,
} as TutorProfile);

// Helper to create a complete profile (100% completion)
const createCompleteProfile = (): TutorProfile => createBaseProfile({
  title: 'Expert Math Tutor',
  bio: 'I am an experienced math tutor with over 10 years of teaching experience in calculus, algebra, and statistics.',
  subjects: [
    { id: 1, subject_id: 1, subject_name: 'Math', proficiency_level: 'Expert', years_experience: 10 },
  ],
  // Use type assertion for fields not in the strict TutorProfile type
  availability: [
    { id: 1, day_of_week: 1, start_time: '09:00', end_time: '17:00', is_recurring: true },
  ] as TutorProfile['availabilities'],
  hourly_rate_cents: 5000,
  avatar_url: 'https://example.com/avatar.jpg',
  education: 'PhD in Mathematics from MIT',
} as unknown as TutorProfile);

// Helper to create an incomplete profile (0% completion)
const createEmptyProfile = (): TutorProfile => createBaseProfile({
  title: '',
  bio: '',
  subjects: [],
  availability: [] as TutorProfile['availabilities'],
  hourly_rate_cents: 0,
  avatar_url: '',
  education: '',
} as unknown as TutorProfile);

// Helper to create a 50% complete profile (3 out of 6 steps)
const createHalfCompleteProfile = (): TutorProfile => createBaseProfile({
  title: 'Math Tutor',
  bio: 'I am an experienced math tutor with over 10 years of teaching experience in calculus, algebra, and statistics.',
  subjects: [
    { id: 1, subject_id: 1, subject_name: 'Math', proficiency_level: 'Expert', years_experience: 10 },
  ],
  availability: [] as TutorProfile['availabilities'],
  hourly_rate_cents: 5000, // Added to complete Pricing step (3/6 = 50%)
  avatar_url: '',
  education: '',
} as unknown as TutorProfile);

describe('ProfileCompletionMeter Component', () => {
  describe('Percentage Calculation', () => {
    it('shows 0% for empty profile', () => {
      render(<ProfileCompletionMeter profile={createEmptyProfile()} />);
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('shows 100% for complete profile', () => {
      render(<ProfileCompletionMeter profile={createCompleteProfile()} />);
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('shows approximately 50% for half complete profile', () => {
      render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      // 3 out of 6 steps = 50%
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('calculates percentage correctly for 1 completed step', () => {
      const profile = createBaseProfile({
        title: 'Math Tutor',
        bio: 'I am an experienced math tutor with over 10 years of teaching in various subjects.',
        subjects: [],
        availability: [] as TutorProfile['availabilities'],
        hourly_rate_cents: 0,
        avatar_url: '',
        education: '',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} />);
      // 1 out of 6 steps = ~17%
      expect(screen.getByText('17%')).toBeInTheDocument();
    });

    it('calculates percentage correctly for 5 completed steps', () => {
      const profile = createBaseProfile({
        title: 'Expert Tutor',
        bio: 'I am an experienced tutor with over 10 years of teaching experience in various subjects.',
        subjects: [
          { id: 1, subject_id: 1, subject_name: 'Math', proficiency_level: 'Expert', years_experience: 5 },
        ],
        availability: [
          { id: 1, day_of_week: 1, start_time: '09:00', end_time: '17:00', is_recurring: true },
        ] as TutorProfile['availabilities'],
        hourly_rate_cents: 5000,
        avatar_url: '',
        education: 'BS in Education',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} />);
      // 5 out of 6 steps = ~83%
      expect(screen.getByText('83%')).toBeInTheDocument();
    });
  });

  describe('Progress Bar', () => {
    it('renders progress bar', () => {
      const { container } = render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      const progressBar = container.querySelector('.h-2.bg-slate-100');
      expect(progressBar).toBeInTheDocument();
    });

    it('progress bar fills to correct width', () => {
      const { container } = render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      const progressFill = container.querySelector('.h-full.rounded-full');
      expect(progressFill).toHaveStyle({ width: '50%' });
    });

    it('shows red color for low completion (below 50%)', () => {
      const { container } = render(<ProfileCompletionMeter profile={createEmptyProfile()} />);
      const progressFill = container.querySelector('.bg-red-500');
      expect(progressFill).toBeInTheDocument();
    });

    it('shows amber color for medium completion (50-74%)', () => {
      const { container } = render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      const progressFill = container.querySelector('.bg-amber-500');
      expect(progressFill).toBeInTheDocument();
    });

    it('shows emerald color for high completion (75%+)', () => {
      const { container } = render(<ProfileCompletionMeter profile={createCompleteProfile()} />);
      const progressFill = container.querySelector('.bg-emerald-500');
      expect(progressFill).toBeInTheDocument();
    });
  });

  describe('Incomplete Items List', () => {
    it('shows all 6 steps', () => {
      render(<ProfileCompletionMeter profile={createEmptyProfile()} />);
      expect(screen.getByText('Basic Info')).toBeInTheDocument();
      expect(screen.getByText('Subjects')).toBeInTheDocument();
      expect(screen.getByText('Availability')).toBeInTheDocument();
      expect(screen.getByText('Pricing')).toBeInTheDocument();
      expect(screen.getByText('Profile Photo')).toBeInTheDocument();
      expect(screen.getByText('Education')).toBeInTheDocument();
    });

    it('shows descriptions for each step', () => {
      render(<ProfileCompletionMeter profile={createEmptyProfile()} />);
      expect(screen.getByText('Name, title, and bio')).toBeInTheDocument();
      expect(screen.getByText('At least one teaching subject')).toBeInTheDocument();
      expect(screen.getByText('Set your weekly schedule')).toBeInTheDocument();
      expect(screen.getByText('Set your hourly rate')).toBeInTheDocument();
      expect(screen.getByText('Upload a professional photo')).toBeInTheDocument();
      expect(screen.getByText('Add your qualifications')).toBeInTheDocument();
    });

    it('shows check icons for completed steps', () => {
      render(<ProfileCompletionMeter profile={createCompleteProfile()} />);
      const checkCircles = screen.getAllByTestId('check-circle');
      // 6 steps + 1 completion message icon = 7 total
      expect(checkCircles.length).toBe(7);
    });

    it('shows circle icons for incomplete steps', () => {
      render(<ProfileCompletionMeter profile={createEmptyProfile()} />);
      const circles = screen.getAllByTestId('circle');
      expect(circles.length).toBe(6);
    });

    it('shows chevron icons only for incomplete steps', () => {
      render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      const chevrons = screen.getAllByTestId('chevron-right');
      expect(chevrons.length).toBe(3); // 3 incomplete steps
    });
  });

  describe('Completion Message', () => {
    it('shows completion message at 100%', () => {
      render(<ProfileCompletionMeter profile={createCompleteProfile()} />);
      expect(screen.getByText('Your profile is complete and visible to students!')).toBeInTheDocument();
    });

    it('does not show completion message when not 100%', () => {
      render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      expect(screen.queryByText('Your profile is complete and visible to students!')).not.toBeInTheDocument();
    });

    it('shows progress footer for incomplete profiles', () => {
      render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      expect(screen.getByText(/steps completed/)).toBeInTheDocument();
    });

    it('shows encouragement message for low completion', () => {
      render(<ProfileCompletionMeter profile={createEmptyProfile()} />);
      expect(screen.getByText(/Complete more sections to appear in search results/)).toBeInTheDocument();
    });

    it('shows encouragement message for medium-high completion', () => {
      const profile = createBaseProfile({
        title: 'Expert Tutor',
        bio: 'I am an experienced tutor with over 10 years of teaching experience in various subjects.',
        subjects: [
          { id: 1, subject_id: 1, subject_name: 'Math', proficiency_level: 'Expert', years_experience: 5 },
        ],
        availability: [
          { id: 1, day_of_week: 1, start_time: '09:00', end_time: '17:00', is_recurring: true },
        ] as TutorProfile['availabilities'],
        hourly_rate_cents: 0,
        avatar_url: '',
        education: '',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} />);
      expect(screen.getByText(/You're almost there/)).toBeInTheDocument();
    });
  });

  describe('Click Handlers', () => {
    it('calls onNavigate with correct section when clicking incomplete item', () => {
      const mockNavigate = jest.fn();
      render(
        <ProfileCompletionMeter
          profile={createEmptyProfile()}
          onNavigate={mockNavigate}
        />
      );

      const subjectsButton = screen.getByText('Subjects').closest('button');
      fireEvent.click(subjectsButton!);

      expect(mockNavigate).toHaveBeenCalledWith('subjects');
    });

    it('calls onNavigate with correct section for each step', () => {
      const mockNavigate = jest.fn();
      render(
        <ProfileCompletionMeter
          profile={createEmptyProfile()}
          onNavigate={mockNavigate}
        />
      );

      const sections = ['basic', 'subjects', 'availability', 'pricing', 'photo', 'education'];
      const labels = ['Basic Info', 'Subjects', 'Availability', 'Pricing', 'Profile Photo', 'Education'];

      labels.forEach((label, index) => {
        mockNavigate.mockClear();
        const button = screen.getByText(label).closest('button');
        fireEvent.click(button!);
        expect(mockNavigate).toHaveBeenCalledWith(sections[index]);
      });
    });

    it('disables button for completed steps', () => {
      const mockNavigate = jest.fn();
      render(
        <ProfileCompletionMeter
          profile={createCompleteProfile()}
          onNavigate={mockNavigate}
        />
      );

      const basicInfoButton = screen.getByText('Basic Info').closest('button');
      expect(basicInfoButton).toBeDisabled();
    });

    it('does not call onNavigate when clicking completed item', () => {
      const mockNavigate = jest.fn();
      render(
        <ProfileCompletionMeter
          profile={createCompleteProfile()}
          onNavigate={mockNavigate}
        />
      );

      const basicInfoButton = screen.getByText('Basic Info').closest('button');
      fireEvent.click(basicInfoButton!);

      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('does not throw when onNavigate is not provided', () => {
      render(<ProfileCompletionMeter profile={createEmptyProfile()} />);

      const subjectsButton = screen.getByText('Subjects').closest('button');
      expect(() => fireEvent.click(subjectsButton!)).not.toThrow();
    });
  });

  describe('Compact Mode', () => {
    it('renders compact version', () => {
      const { container } = render(
        <ProfileCompletionMeter profile={createHalfCompleteProfile()} compact />
      );
      const compactCard = container.querySelector('.rounded-xl');
      expect(compactCard).toBeInTheDocument();
    });

    it('shows percentage in compact mode', () => {
      render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} compact />);
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('shows "Profile Completion" label in compact mode', () => {
      render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} compact />);
      expect(screen.getByText('Profile Completion')).toBeInTheDocument();
    });

    it('shows next incomplete step in compact mode', () => {
      const profile = createBaseProfile({
        title: 'Math Tutor',
        bio: 'I am an experienced tutor with over 10 years of teaching experience in various subjects.',
        subjects: [],
        availability: [] as TutorProfile['availabilities'],
        hourly_rate_cents: 0,
        avatar_url: '',
        education: '',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} compact />);
      expect(screen.getByText('Subjects')).toBeInTheDocument();
      expect(screen.getByText(/Next:/)).toBeInTheDocument();
    });

    it('shows completion message in compact mode at 100%', () => {
      render(<ProfileCompletionMeter profile={createCompleteProfile()} compact />);
      expect(screen.getByText('Profile complete!')).toBeInTheDocument();
    });

    it('does not show next step in compact mode at 100%', () => {
      render(<ProfileCompletionMeter profile={createCompleteProfile()} compact />);
      expect(screen.queryByText(/Next:/)).not.toBeInTheDocument();
    });

    it('calls onNavigate when clicking next step button in compact mode', () => {
      const mockNavigate = jest.fn();
      const profile = createBaseProfile({
        title: 'Math Tutor',
        bio: 'I am an experienced tutor with over 10 years of teaching experience in various subjects.',
        subjects: [],
        availability: [] as TutorProfile['availabilities'],
        hourly_rate_cents: 0,
        avatar_url: '',
        education: '',
      } as unknown as TutorProfile);
      render(
        <ProfileCompletionMeter profile={profile} onNavigate={mockNavigate} compact />
      );

      const nextButton = screen.getByText('Subjects').closest('button');
      fireEvent.click(nextButton!);

      expect(mockNavigate).toHaveBeenCalledWith('subjects');
    });
  });

  describe('Step Validation Logic', () => {
    it('marks Basic Info complete when title and bio >= 50 chars', () => {
      const profile = createBaseProfile({
        title: 'Expert Math Tutor',
        bio: 'I am an experienced math tutor with over 10 years of teaching experience.',
        subjects: [],
        availability: [] as TutorProfile['availabilities'],
        hourly_rate_cents: 0,
        avatar_url: '',
        education: '',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} />);

      const basicInfoStep = screen.getByText('Basic Info').closest('button');
      expect(basicInfoStep).toHaveClass('bg-emerald-50/50');
    });

    it('marks Basic Info incomplete when bio < 50 chars', () => {
      const profile = createBaseProfile({
        title: 'Expert Tutor',
        bio: 'Short bio',
        subjects: [],
        availability: [] as TutorProfile['availabilities'],
        hourly_rate_cents: 0,
        avatar_url: '',
        education: '',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} />);

      const basicInfoStep = screen.getByText('Basic Info').closest('button');
      expect(basicInfoStep).not.toHaveClass('bg-emerald-50/50');
    });

    it('marks Subjects complete when at least one subject exists', () => {
      const profile = createBaseProfile({
        title: '',
        bio: '',
        subjects: [
          { id: 1, subject_id: 1, subject_name: 'Math', proficiency_level: 'Beginner', years_experience: 1 },
        ],
        availability: [] as TutorProfile['availabilities'],
        hourly_rate_cents: 0,
        avatar_url: '',
        education: '',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} />);

      const subjectsStep = screen.getByText('Subjects').closest('button');
      expect(subjectsStep).toHaveClass('bg-emerald-50/50');
    });

    it('marks Availability complete when at least one slot exists', () => {
      const profile = createBaseProfile({
        title: '',
        bio: '',
        subjects: [],
        availability: [
          { id: 1, day_of_week: 1, start_time: '09:00', end_time: '17:00', is_recurring: true },
        ] as TutorProfile['availabilities'],
        hourly_rate_cents: 0,
        avatar_url: '',
        education: '',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} />);

      const availabilityStep = screen.getByText('Availability').closest('button');
      expect(availabilityStep).toHaveClass('bg-emerald-50/50');
    });

    it('marks Pricing complete when hourly_rate_cents > 0', () => {
      const profile = createBaseProfile({
        title: '',
        bio: '',
        subjects: [],
        availability: [] as TutorProfile['availabilities'],
        hourly_rate_cents: 5000,
        avatar_url: '',
        education: '',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} />);

      const pricingStep = screen.getByText('Pricing').closest('button');
      expect(pricingStep).toHaveClass('bg-emerald-50/50');
    });

    it('marks Profile Photo complete when avatar_url exists', () => {
      const profile = createBaseProfile({
        title: '',
        bio: '',
        subjects: [],
        availability: [] as TutorProfile['availabilities'],
        hourly_rate_cents: 0,
        avatar_url: 'https://example.com/photo.jpg',
        education: '',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} />);

      const photoStep = screen.getByText('Profile Photo').closest('button');
      expect(photoStep).toHaveClass('bg-emerald-50/50');
    });

    it('marks Education complete when education field is not empty', () => {
      const profile = createBaseProfile({
        title: '',
        bio: '',
        subjects: [],
        availability: [] as TutorProfile['availabilities'],
        hourly_rate_cents: 0,
        avatar_url: '',
        education: 'PhD in Mathematics',
      } as unknown as TutorProfile);
      render(<ProfileCompletionMeter profile={profile} />);

      const educationStep = screen.getByText('Education').closest('button');
      expect(educationStep).toHaveClass('bg-emerald-50/50');
    });
  });

  describe('UI Styling', () => {
    it('has proper header section in full mode', () => {
      render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      expect(screen.getByText('Profile Completion')).toBeInTheDocument();
      expect(screen.getByText('Complete your profile to attract more students')).toBeInTheDocument();
    });

    it('shows percentage in circular badge in full mode', () => {
      const { container } = render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      const badge = container.querySelector('.w-14.h-14.rounded-full');
      expect(badge).toBeInTheDocument();
    });

    it('applies emerald styling to percentage badge at 100%', () => {
      const { container } = render(<ProfileCompletionMeter profile={createCompleteProfile()} />);
      const badge = container.querySelector('.bg-emerald-100');
      expect(badge).toBeInTheDocument();
    });

    it('applies slate styling to percentage badge when not 100%', () => {
      const { container } = render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      const badge = container.querySelector('.bg-slate-100');
      expect(badge).toBeInTheDocument();
    });

    it('has rounded-2xl card styling in full mode', () => {
      const { container } = render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      const card = container.querySelector('.rounded-2xl');
      expect(card).toBeInTheDocument();
    });

    it('has proper dark mode styling', () => {
      const { container } = render(<ProfileCompletionMeter profile={createHalfCompleteProfile()} />);
      const darkCard = container.querySelector('.dark\\:bg-slate-900');
      expect(darkCard).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('step buttons are focusable', () => {
      render(<ProfileCompletionMeter profile={createEmptyProfile()} />);
      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        expect(button).not.toHaveAttribute('tabindex', '-1');
      });
    });

    it('completed step buttons are disabled', () => {
      render(<ProfileCompletionMeter profile={createCompleteProfile()} />);
      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        expect(button).toBeDisabled();
      });
    });

    it('incomplete step buttons are enabled', () => {
      render(<ProfileCompletionMeter profile={createEmptyProfile()} />);
      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        expect(button).toBeEnabled();
      });
    });
  });
});
