/**
 * Tests for SkeletonLoader components
 * Tests all skeleton variants for loading states across the application
 */

import { render, screen } from '@testing-library/react';
import SkeletonLoader, {
  TutorCardSkeleton,
  TutorProfileSkeleton,
  BookingCardSkeleton,
  BookingListSkeleton,
  MessageThreadSkeleton,
  MessageListSkeleton,
  DashboardStatsSkeleton,
  NotificationSkeleton,
  NotificationListSkeleton,
  CalendarSkeleton,
} from '@/components/SkeletonLoader';

describe('SkeletonLoader Component', () => {
  describe('Basic SkeletonLoader', () => {
    it('renders with default props', () => {
      const { container } = render(<SkeletonLoader />);
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });

    it('applies rectangular variant by default', () => {
      const { container } = render(<SkeletonLoader />);
      const skeleton = container.querySelector('.rounded-lg');
      expect(skeleton).toBeInTheDocument();
    });

    it('applies text variant', () => {
      const { container } = render(<SkeletonLoader variant="text" />);
      const skeleton = container.querySelector('.rounded');
      expect(skeleton).toBeInTheDocument();
    });

    it('applies circle variant', () => {
      const { container } = render(<SkeletonLoader variant="circle" />);
      const skeleton = container.querySelector('.rounded-full');
      expect(skeleton).toBeInTheDocument();
    });

    it('applies custom width and height', () => {
      const { container } = render(<SkeletonLoader width="200px" height="50px" />);
      const skeleton = container.firstChild as HTMLElement;
      expect(skeleton.style.width).toBe('200px');
      expect(skeleton.style.height).toBe('50px');
    });

    it('applies custom className', () => {
      const { container } = render(<SkeletonLoader className="custom-class" />);
      const skeleton = container.querySelector('.custom-class');
      expect(skeleton).toBeInTheDocument();
    });

    it('renders multiple lines when lines prop is provided', () => {
      const { container } = render(<SkeletonLoader lines={3} />);
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBe(3);
    });

    it('renders single line when lines is 1', () => {
      const { container } = render(<SkeletonLoader lines={1} />);
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBe(1);
    });

    it('makes last line 80% width when multiple lines', () => {
      const { container } = render(<SkeletonLoader lines={3} width="100%" />);
      const skeletons = container.querySelectorAll('.animate-pulse');
      const lastSkeleton = skeletons[skeletons.length - 1] as HTMLElement;
      expect(lastSkeleton.style.width).toBe('80%');
    });

    it('has proper animation classes', () => {
      const { container } = render(<SkeletonLoader />);
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('bg-gradient-to-r');
      expect(skeleton).toHaveClass('from-slate-200');
      expect(skeleton).toHaveClass('via-slate-300');
      expect(skeleton).toHaveClass('to-slate-200');
    });

    it('has proper dark mode classes', () => {
      const { container } = render(<SkeletonLoader />);
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('dark:from-slate-700');
      expect(skeleton).toHaveClass('dark:via-slate-600');
      expect(skeleton).toHaveClass('dark:to-slate-700');
    });

    it('applies bg-[length:200%_100%] for animation effect', () => {
      const { container } = render(<SkeletonLoader />);
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('bg-[length:200%_100%]');
    });
  });

  describe('BookingCardSkeleton', () => {
    it('renders correctly', () => {
      const { container } = render(<BookingCardSkeleton />);
      const card = container.querySelector('.bg-white');
      expect(card).toBeInTheDocument();
    });

    it('contains animate-pulse class on container', () => {
      const { container } = render(<BookingCardSkeleton />);
      const card = container.querySelector('.animate-pulse');
      expect(card).toBeInTheDocument();
    });

    it('renders circular skeleton for avatar', () => {
      const { container } = render(<BookingCardSkeleton />);
      const circles = container.querySelectorAll('.rounded-full');
      expect(circles.length).toBeGreaterThan(0);
    });

    it('has rounded-xl card styling', () => {
      const { container } = render(<BookingCardSkeleton />);
      const card = container.querySelector('.rounded-xl');
      expect(card).toBeInTheDocument();
    });

    it('has proper layout structure with flex', () => {
      const { container } = render(<BookingCardSkeleton />);
      const flexLayout = container.querySelector('.flex.items-start');
      expect(flexLayout).toBeInTheDocument();
    });

    it('has dark mode styling', () => {
      const { container } = render(<BookingCardSkeleton />);
      const card = container.querySelector('.dark\\:bg-slate-900');
      expect(card).toBeInTheDocument();
    });

    it('has no interactive elements', () => {
      const { container } = render(<BookingCardSkeleton />);
      const buttons = container.querySelectorAll('button');
      const links = container.querySelectorAll('a');
      expect(buttons.length).toBe(0);
      expect(links.length).toBe(0);
    });
  });

  describe('BookingListSkeleton', () => {
    it('renders default 3 cards', () => {
      const { container } = render(<BookingListSkeleton />);
      const cards = container.querySelectorAll('.animate-pulse');
      expect(cards.length).toBe(3);
    });

    it('renders custom number of cards', () => {
      const { container } = render(<BookingListSkeleton count={5} />);
      const cards = container.querySelectorAll('.animate-pulse');
      expect(cards.length).toBe(5);
    });

    it('renders 1 card when count is 1', () => {
      const { container } = render(<BookingListSkeleton count={1} />);
      const cards = container.querySelectorAll('.animate-pulse');
      expect(cards.length).toBe(1);
    });

    it('has proper spacing between cards', () => {
      const { container } = render(<BookingListSkeleton />);
      const spacedContainer = container.querySelector('.space-y-4');
      expect(spacedContainer).toBeInTheDocument();
    });
  });

  describe('MessageThreadSkeleton', () => {
    it('renders correctly', () => {
      const { container } = render(<MessageThreadSkeleton />);
      const thread = container.querySelector('.animate-pulse');
      expect(thread).toBeInTheDocument();
    });

    it('renders circular avatar placeholder', () => {
      const { container } = render(<MessageThreadSkeleton />);
      const circles = container.querySelectorAll('.rounded-full');
      expect(circles.length).toBeGreaterThan(0);
    });

    it('has flex layout with gap', () => {
      const { container } = render(<MessageThreadSkeleton />);
      const flexLayout = container.querySelector('.flex.items-start.gap-3');
      expect(flexLayout).toBeInTheDocument();
    });

    it('has proper padding', () => {
      const { container } = render(<MessageThreadSkeleton />);
      const padded = container.querySelector('.p-4');
      expect(padded).toBeInTheDocument();
    });
  });

  describe('MessageListSkeleton', () => {
    it('renders default 5 threads', () => {
      const { container } = render(<MessageListSkeleton />);
      const threads = container.querySelectorAll('.animate-pulse');
      expect(threads.length).toBe(5);
    });

    it('renders custom number of threads', () => {
      const { container } = render(<MessageListSkeleton count={3} />);
      const threads = container.querySelectorAll('.animate-pulse');
      expect(threads.length).toBe(3);
    });

    it('has divider styling between threads', () => {
      const { container } = render(<MessageListSkeleton />);
      const dividedContainer = container.querySelector('.divide-y');
      expect(dividedContainer).toBeInTheDocument();
    });

    it('has dark mode divider styling', () => {
      const { container } = render(<MessageListSkeleton />);
      const dividedContainer = container.querySelector('.dark\\:divide-slate-800');
      expect(dividedContainer).toBeInTheDocument();
    });
  });

  describe('DashboardStatsSkeleton', () => {
    it('renders correctly', () => {
      const { container } = render(<DashboardStatsSkeleton />);
      const grid = container.querySelector('.animate-pulse');
      expect(grid).toBeInTheDocument();
    });

    it('renders 4 stat cards in grid', () => {
      const { container } = render(<DashboardStatsSkeleton />);
      const cards = container.querySelectorAll('.rounded-xl.border');
      expect(cards.length).toBe(4);
    });

    it('has responsive grid layout', () => {
      const { container } = render(<DashboardStatsSkeleton />);
      const grid = container.querySelector('.grid-cols-2.md\\:grid-cols-4');
      expect(grid).toBeInTheDocument();
    });

    it('has proper gap between stat cards', () => {
      const { container } = render(<DashboardStatsSkeleton />);
      const grid = container.querySelector('.gap-4');
      expect(grid).toBeInTheDocument();
    });

    it('each card has proper padding', () => {
      const { container } = render(<DashboardStatsSkeleton />);
      const paddedCards = container.querySelectorAll('.p-4');
      expect(paddedCards.length).toBe(4);
    });
  });

  describe('NotificationSkeleton', () => {
    it('renders correctly', () => {
      const { container } = render(<NotificationSkeleton />);
      const notification = container.querySelector('.animate-pulse');
      expect(notification).toBeInTheDocument();
    });

    it('renders circular avatar placeholder', () => {
      const { container } = render(<NotificationSkeleton />);
      const circles = container.querySelectorAll('.rounded-full');
      expect(circles.length).toBeGreaterThan(0);
    });

    it('has flex layout with proper gap', () => {
      const { container } = render(<NotificationSkeleton />);
      const flexLayout = container.querySelector('.flex.items-start.gap-4');
      expect(flexLayout).toBeInTheDocument();
    });

    it('has proper padding', () => {
      const { container } = render(<NotificationSkeleton />);
      const padded = container.querySelector('.p-4');
      expect(padded).toBeInTheDocument();
    });
  });

  describe('NotificationListSkeleton', () => {
    it('renders default 5 notifications', () => {
      const { container } = render(<NotificationListSkeleton />);
      const notifications = container.querySelectorAll('.animate-pulse');
      expect(notifications.length).toBe(5);
    });

    it('renders custom number of notifications', () => {
      const { container } = render(<NotificationListSkeleton count={3} />);
      const notifications = container.querySelectorAll('.animate-pulse');
      expect(notifications.length).toBe(3);
    });

    it('has divider styling between notifications', () => {
      const { container } = render(<NotificationListSkeleton />);
      const dividedContainer = container.querySelector('.divide-y');
      expect(dividedContainer).toBeInTheDocument();
    });

    it('has dark mode divider styling', () => {
      const { container } = render(<NotificationListSkeleton />);
      const dividedContainer = container.querySelector('.dark\\:divide-slate-800');
      expect(dividedContainer).toBeInTheDocument();
    });
  });

  describe('CalendarSkeleton', () => {
    it('renders correctly', () => {
      const { container } = render(<CalendarSkeleton />);
      const calendar = container.querySelector('.animate-pulse');
      expect(calendar).toBeInTheDocument();
    });

    it('has card styling with rounded corners', () => {
      const { container } = render(<CalendarSkeleton />);
      const card = container.querySelector('.rounded-xl');
      expect(card).toBeInTheDocument();
    });

    it('renders header with navigation placeholders', () => {
      const { container } = render(<CalendarSkeleton />);
      const header = container.querySelector('.flex.justify-between.items-center');
      expect(header).toBeInTheDocument();
    });

    it('renders 7-column grid for days header', () => {
      const { container } = render(<CalendarSkeleton />);
      const grid = container.querySelector('.grid-cols-7');
      expect(grid).toBeInTheDocument();
    });

    it('renders 35 day cells (5 weeks)', () => {
      const { container } = render(<CalendarSkeleton />);
      const grids = container.querySelectorAll('.grid-cols-7');
      // Second grid should have 35 children
      const calendarGrid = grids[1];
      expect(calendarGrid?.children.length).toBe(35);
    });

    it('has proper padding', () => {
      const { container } = render(<CalendarSkeleton />);
      const padded = container.querySelector('.p-4');
      expect(padded).toBeInTheDocument();
    });

    it('has border styling', () => {
      const { container } = render(<CalendarSkeleton />);
      const bordered = container.querySelector('.border');
      expect(bordered).toBeInTheDocument();
    });
  });

  describe('TutorCardSkeleton', () => {
    it('renders tutor card skeleton structure', () => {
      const { container } = render(<TutorCardSkeleton />);
      const card = container.querySelector('.bg-white.rounded-2xl');
      expect(card).toBeInTheDocument();
    });

    it('contains multiple skeleton elements', () => {
      const { container } = render(<TutorCardSkeleton />);
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('has grid layout for stats', () => {
      const { container } = render(<TutorCardSkeleton />);
      const grid = container.querySelector('.grid-cols-2');
      expect(grid).toBeInTheDocument();
    });

    it('renders circular skeleton for avatar', () => {
      const { container } = render(<TutorCardSkeleton />);
      const circle = container.querySelector('.rounded-full');
      expect(circle).toBeInTheDocument();
    });

    it('has animate-pulse class on container', () => {
      const { container } = render(<TutorCardSkeleton />);
      const card = container.querySelector('.animate-pulse');
      expect(card).toBeInTheDocument();
    });

    it('has shadow styling', () => {
      const { container } = render(<TutorCardSkeleton />);
      const card = container.querySelector('.shadow-soft');
      expect(card).toBeInTheDocument();
    });
  });

  describe('TutorProfileSkeleton', () => {
    it('renders tutor profile skeleton structure', () => {
      const { container } = render(<TutorProfileSkeleton />);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('has proper layout grid', () => {
      const { container } = render(<TutorProfileSkeleton />);
      const grid = container.querySelector('.lg\\:grid-cols-12');
      expect(grid).toBeInTheDocument();
    });

    it('renders breadcrumb skeleton', () => {
      const { container } = render(<TutorProfileSkeleton />);
      // Check for container structure
      expect(container.querySelector('.container')).toBeInTheDocument();
    });

    it('renders hero header section', () => {
      const { container } = render(<TutorProfileSkeleton />);
      const rounded = container.querySelectorAll('.rounded-3xl');
      expect(rounded.length).toBeGreaterThan(0);
    });

    it('renders video placeholder with aspect ratio', () => {
      const { container } = render(<TutorProfileSkeleton />);
      const video = container.querySelector('.aspect-video');
      expect(video).toBeInTheDocument();
    });

    it('renders sidebar with sticky positioning', () => {
      const { container } = render(<TutorProfileSkeleton />);
      const sticky = container.querySelector('.sticky');
      expect(sticky).toBeInTheDocument();
    });

    it('renders stats grid with 3 columns', () => {
      const { container } = render(<TutorProfileSkeleton />);
      const statsGrid = container.querySelector('.grid-cols-3');
      expect(statsGrid).toBeInTheDocument();
    });

    it('has proper background styling', () => {
      const { container } = render(<TutorProfileSkeleton />);
      const bg = container.querySelector('.bg-slate-50');
      expect(bg).toBeInTheDocument();
    });

    it('has left column spanning 8 columns on large screens', () => {
      const { container } = render(<TutorProfileSkeleton />);
      const leftColumn = container.querySelector('.lg\\:col-span-8');
      expect(leftColumn).toBeInTheDocument();
    });

    it('has right column spanning 4 columns on large screens', () => {
      const { container } = render(<TutorProfileSkeleton />);
      const rightColumn = container.querySelector('.lg\\:col-span-4');
      expect(rightColumn).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('skeleton elements have no interactive content', () => {
      const { container } = render(<SkeletonLoader />);
      const buttons = container.querySelectorAll('button');
      const links = container.querySelectorAll('a');
      expect(buttons.length).toBe(0);
      expect(links.length).toBe(0);
    });

    it('tutor card skeleton has no interactive elements', () => {
      const { container } = render(<TutorCardSkeleton />);
      const buttons = container.querySelectorAll('button');
      const links = container.querySelectorAll('a');
      expect(buttons.length).toBe(0);
      expect(links.length).toBe(0);
    });

    it('booking card skeleton has no interactive elements', () => {
      const { container } = render(<BookingCardSkeleton />);
      const buttons = container.querySelectorAll('button');
      const links = container.querySelectorAll('a');
      expect(buttons.length).toBe(0);
      expect(links.length).toBe(0);
    });

    it('message thread skeleton has no interactive elements', () => {
      const { container } = render(<MessageThreadSkeleton />);
      const buttons = container.querySelectorAll('button');
      const links = container.querySelectorAll('a');
      expect(buttons.length).toBe(0);
      expect(links.length).toBe(0);
    });

    it('notification skeleton has no interactive elements', () => {
      const { container } = render(<NotificationSkeleton />);
      const buttons = container.querySelectorAll('button');
      const links = container.querySelectorAll('a');
      expect(buttons.length).toBe(0);
      expect(links.length).toBe(0);
    });

    it('calendar skeleton has no interactive elements', () => {
      const { container } = render(<CalendarSkeleton />);
      const buttons = container.querySelectorAll('button');
      const links = container.querySelectorAll('a');
      expect(buttons.length).toBe(0);
      expect(links.length).toBe(0);
    });

    it('dashboard stats skeleton has no interactive elements', () => {
      const { container } = render(<DashboardStatsSkeleton />);
      const buttons = container.querySelectorAll('button');
      const links = container.querySelectorAll('a');
      expect(buttons.length).toBe(0);
      expect(links.length).toBe(0);
    });
  });

  describe('Snapshot Tests', () => {
    it('SkeletonLoader matches snapshot', () => {
      const { container } = render(<SkeletonLoader />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('BookingCardSkeleton matches snapshot', () => {
      const { container } = render(<BookingCardSkeleton />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('MessageThreadSkeleton matches snapshot', () => {
      const { container } = render(<MessageThreadSkeleton />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('DashboardStatsSkeleton matches snapshot', () => {
      const { container } = render(<DashboardStatsSkeleton />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('NotificationSkeleton matches snapshot', () => {
      const { container } = render(<NotificationSkeleton />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('CalendarSkeleton matches snapshot', () => {
      const { container } = render(<CalendarSkeleton />);
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
