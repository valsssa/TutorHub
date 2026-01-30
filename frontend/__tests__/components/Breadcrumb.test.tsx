/**
 * Tests for Breadcrumb component
 * Tests breadcrumb navigation functionality
 */

import { render, screen } from '@testing-library/react';
import Breadcrumb, { generateBreadcrumbItems } from '@/components/Breadcrumb';

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

describe('Breadcrumb', () => {
  describe('Basic Rendering', () => {
    it('renders breadcrumb navigation', () => {
      render(<Breadcrumb items={[{ label: 'Page' }]} />);

      expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toBeInTheDocument();
    });

    it('renders items in a list', () => {
      render(
        <Breadcrumb
          items={[
            { label: 'Category', href: '/category' },
            { label: 'Current Page' },
          ]}
        />
      );

      expect(screen.getByRole('list')).toBeInTheDocument();
    });

    it('renders with single item', () => {
      render(<Breadcrumb items={[{ label: 'Current Page' }]} />);

      expect(screen.getByText('Current Page')).toBeInTheDocument();
    });

    it('renders with multiple items', () => {
      render(
        <Breadcrumb
          items={[
            { label: 'First', href: '/first' },
            { label: 'Second', href: '/second' },
            { label: 'Third' },
          ]}
        />
      );

      expect(screen.getByText('First')).toBeInTheDocument();
      expect(screen.getByText('Second')).toBeInTheDocument();
      expect(screen.getByText('Third')).toBeInTheDocument();
    });
  });

  describe('Home Item', () => {
    it('shows home icon by default', () => {
      const { container } = render(
        <Breadcrumb items={[{ label: 'Page' }]} />
      );

      // Home icon should be rendered
      const homeIcon = container.querySelector('svg');
      expect(homeIcon).toBeInTheDocument();
    });

    it('links home to /dashboard by default', () => {
      render(<Breadcrumb items={[{ label: 'Page' }]} />);

      const homeLink = screen.getByRole('link', { name: /home/i });
      expect(homeLink).toHaveAttribute('href', '/dashboard');
    });

    it('links home to custom href when provided', () => {
      render(
        <Breadcrumb
          items={[{ label: 'Page' }]}
          homeHref="/custom-home"
        />
      );

      const homeLink = screen.getByRole('link', { name: /home/i });
      expect(homeLink).toHaveAttribute('href', '/custom-home');
    });

    it('hides home when showHome is false', () => {
      render(
        <Breadcrumb
          items={[{ label: 'Page' }]}
          showHome={false}
        />
      );

      expect(screen.queryByText('Home')).not.toBeInTheDocument();
    });
  });

  describe('Link Behavior', () => {
    it('renders items with href as links', () => {
      render(
        <Breadcrumb
          items={[
            { label: 'Category', href: '/category' },
            { label: 'Current Page' },
          ]}
        />
      );

      const categoryLink = screen.getByRole('link', { name: /category/i });
      expect(categoryLink).toHaveAttribute('href', '/category');
    });

    it('renders last item without link (current page)', () => {
      render(
        <Breadcrumb
          items={[
            { label: 'Category', href: '/category' },
            { label: 'Current Page' },
          ]}
        />
      );

      // Current page should not be a link
      const currentPage = screen.getByText('Current Page');
      expect(currentPage.closest('a')).toBeNull();
    });

    it('marks current page with aria-current', () => {
      render(
        <Breadcrumb
          items={[
            { label: 'Category', href: '/category' },
            { label: 'Current Page' },
          ]}
        />
      );

      const currentPage = screen.getByText('Current Page').closest('span');
      expect(currentPage).toHaveAttribute('aria-current', 'page');
    });

    it('does not link last item even if href is provided', () => {
      render(
        <Breadcrumb
          items={[
            { label: 'Category', href: '/category' },
            { label: 'Current Page', href: '/current' },
          ]}
        />
      );

      // Last item should not be a link even with href
      const currentPage = screen.getByText('Current Page');
      expect(currentPage.closest('a')).toBeNull();
    });
  });

  describe('Separator', () => {
    it('renders default chevron separator', () => {
      const { container } = render(
        <Breadcrumb
          items={[
            { label: 'First', href: '/first' },
            { label: 'Second' },
          ]}
        />
      );

      // Chevron icons should be present as separators
      const separators = container.querySelectorAll('[aria-hidden="true"]');
      expect(separators.length).toBeGreaterThan(0);
    });

    it('renders custom separator', () => {
      render(
        <Breadcrumb
          items={[
            { label: 'First', href: '/first' },
            { label: 'Second' },
          ]}
          separator={<span>/</span>}
        />
      );

      expect(screen.getByText('/')).toBeInTheDocument();
    });

    it('does not render separator after last item', () => {
      const { container } = render(
        <Breadcrumb
          items={[{ label: 'Only Item' }]}
          showHome={false}
        />
      );

      // With only one item and no home, there should be no separator
      const separators = container.querySelectorAll('[aria-hidden="true"]');
      // The only aria-hidden elements should be icons, not separators
      expect(separators.length).toBe(0);
    });
  });

  describe('Icons', () => {
    it('renders custom icon for item', () => {
      const CustomIcon = () => <span data-testid="custom-icon">*</span>;

      render(
        <Breadcrumb
          items={[
            { label: 'With Icon', href: '/with-icon', icon: <CustomIcon /> },
            { label: 'Current' },
          ]}
        />
      );

      expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it('applies sm size classes', () => {
      const { container } = render(
        <Breadcrumb items={[{ label: 'Page' }]} size="sm" />
      );

      const nav = container.querySelector('nav');
      expect(nav).toHaveClass('text-xs');
    });

    it('applies md size classes (default)', () => {
      const { container } = render(
        <Breadcrumb items={[{ label: 'Page' }]} size="md" />
      );

      const nav = container.querySelector('nav');
      expect(nav).toHaveClass('text-sm');
    });

    it('uses md as default size', () => {
      const { container } = render(
        <Breadcrumb items={[{ label: 'Page' }]} />
      );

      const nav = container.querySelector('nav');
      expect(nav).toHaveClass('text-sm');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <Breadcrumb
          items={[{ label: 'Page' }]}
          className="custom-breadcrumb"
        />
      );

      const nav = container.querySelector('nav');
      expect(nav).toHaveClass('custom-breadcrumb');
    });
  });

  describe('Empty State', () => {
    it('renders only home when items array is empty', () => {
      render(<Breadcrumb items={[]} />);

      expect(screen.getByText('Home')).toBeInTheDocument();
    });

    it('renders nothing visible when items empty and showHome false', () => {
      render(<Breadcrumb items={[]} showHome={false} />);

      expect(screen.getByRole('list')).toBeEmptyDOMElement();
    });
  });

  describe('Accessibility', () => {
    it('has proper navigation landmark', () => {
      render(<Breadcrumb items={[{ label: 'Page' }]} />);

      expect(screen.getByRole('navigation')).toHaveAttribute('aria-label', 'Breadcrumb');
    });

    it('uses semantic list structure', () => {
      render(
        <Breadcrumb
          items={[
            { label: 'Category', href: '/category' },
            { label: 'Current Page' },
          ]}
        />
      );

      const list = screen.getByRole('list');
      const items = list.querySelectorAll('li');
      expect(items.length).toBe(3); // Home + Category + Current Page
    });
  });
});

describe('generateBreadcrumbItems', () => {
  it('generates items from pathname', () => {
    const items = generateBreadcrumbItems('/bookings/123');

    expect(items).toHaveLength(2);
    expect(items[0].label).toBe('Bookings');
    expect(items[0].href).toBe('/bookings');
    expect(items[1].label).toBe('123');
    expect(items[1].href).toBeUndefined(); // Last item has no href
  });

  it('converts kebab-case to Title Case', () => {
    const items = generateBreadcrumbItems('/my-bookings/upcoming-lessons');

    expect(items[0].label).toBe('My Bookings');
    expect(items[1].label).toBe('Upcoming Lessons');
  });

  it('uses custom labels when provided', () => {
    const items = generateBreadcrumbItems('/bookings/123', {
      '/bookings': 'My Sessions',
      '123': 'Session Details',
    });

    expect(items[0].label).toBe('My Sessions');
    expect(items[1].label).toBe('Session Details');
  });

  it('handles single segment paths', () => {
    const items = generateBreadcrumbItems('/dashboard');

    expect(items).toHaveLength(1);
    expect(items[0].label).toBe('Dashboard');
    expect(items[0].href).toBeUndefined();
  });

  it('handles root path', () => {
    const items = generateBreadcrumbItems('/');

    expect(items).toHaveLength(0);
  });

  it('handles dynamic segments like [id]', () => {
    const items = generateBreadcrumbItems('/users/[id]');

    expect(items[1].label).toBe('id');
  });

  it('handles segments with dashes in dynamic parts', () => {
    const items = generateBreadcrumbItems('/tutors/[tutor-id]');

    expect(items[1].label).toBe('tutor id');
  });

  it('builds correct href paths', () => {
    const items = generateBreadcrumbItems('/level1/level2/level3');

    expect(items[0].href).toBe('/level1');
    expect(items[1].href).toBe('/level1/level2');
    expect(items[2].href).toBeUndefined(); // Last item
  });
});
