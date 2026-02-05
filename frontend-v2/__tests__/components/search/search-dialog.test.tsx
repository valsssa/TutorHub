import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { SearchDialog } from '@/components/search/search-dialog';

// Mock useRouter
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock the search hooks
const mockUseSearch = vi.fn();
const mockAddRecentSearch = vi.fn();
const mockRemoveRecentSearch = vi.fn();
const mockClearRecentSearches = vi.fn();
const mockRecentSearches: Array<{ id: string; query: string; timestamp: number }> = [];

vi.mock('@/lib/hooks/use-search', () => ({
  useSearch: (query: string) => mockUseSearch(query),
  useRecentSearches: () => ({
    recentSearches: mockRecentSearches,
    addRecentSearch: mockAddRecentSearch,
    removeRecentSearch: mockRemoveRecentSearch,
    clearRecentSearches: mockClearRecentSearches,
  }),
}));

// Mock SearchResults component
vi.mock('@/components/search/search-results', () => ({
  SearchResults: ({
    tutors,
    subjects,
    selectedIndex,
    onSelect,
  }: {
    tutors: Array<{ id: number; name: string }>;
    subjects: Array<{ id: number; name: string }>;
    selectedIndex: number;
    onSelect: (type: 'tutor' | 'subject', id: number) => void;
  }) => (
    <div data-testid="search-results">
      {tutors.map((tutor, idx) => (
        <button
          key={tutor.id}
          data-testid={`tutor-${tutor.id}`}
          data-selected={selectedIndex === idx}
          onClick={() => onSelect('tutor', tutor.id)}
        >
          {tutor.name}
        </button>
      ))}
      {subjects.map((subject, idx) => (
        <button
          key={subject.id}
          data-testid={`subject-${subject.id}`}
          data-selected={selectedIndex === tutors.length + idx}
          onClick={() => onSelect('subject', subject.id)}
        >
          {subject.name}
        </button>
      ))}
    </div>
  ),
}));

describe('SearchDialog', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSearch.mockReturnValue({
      results: null,
      isLoading: false,
    });
    mockRecentSearches.length = 0;
  });

  afterEach(() => {
    document.body.style.overflow = '';
  });

  it('renders nothing when isOpen is false', () => {
    render(<SearchDialog isOpen={false} onClose={vi.fn()} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders dialog when isOpen is true', () => {
    render(<SearchDialog {...defaultProps} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search tutors, subjects/i)).toBeInTheDocument();
  });

  it('shows empty state when no query and no recent searches', () => {
    render(<SearchDialog {...defaultProps} />);
    expect(
      screen.getByText(/start typing to search for tutors or subjects/i)
    ).toBeInTheDocument();
  });

  it('focuses input when dialog opens', async () => {
    render(<SearchDialog {...defaultProps} />);
    const input = screen.getByPlaceholderText(/search tutors, subjects/i);

    await waitFor(() => {
      expect(input).toHaveFocus();
    });
  });

  describe('keyboard navigation', () => {
    it('closes dialog on Escape key', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(<SearchDialog isOpen={true} onClose={onClose} />);

      const input = screen.getByPlaceholderText(/search tutors, subjects/i);
      await user.type(input, '{Escape}');

      expect(onClose).toHaveBeenCalled();
    });

    it('navigates through results with ArrowDown', async () => {
      const user = userEvent.setup();
      mockUseSearch.mockReturnValue({
        results: {
          tutors: [
            { id: 1, name: 'Tutor 1' },
            { id: 2, name: 'Tutor 2' },
          ],
          subjects: [{ id: 1, name: 'Math' }],
        },
        isLoading: false,
      });

      render(<SearchDialog {...defaultProps} />);
      const input = screen.getByPlaceholderText(/search tutors, subjects/i);

      await user.type(input, 'test');
      await user.type(input, '{ArrowDown}');

      const tutor2Button = screen.getByTestId('tutor-2');
      expect(tutor2Button).toHaveAttribute('data-selected', 'true');
    });

    it('navigates through results with ArrowUp', async () => {
      const user = userEvent.setup();
      mockUseSearch.mockReturnValue({
        results: {
          tutors: [
            { id: 1, name: 'Tutor 1' },
            { id: 2, name: 'Tutor 2' },
          ],
          subjects: [],
        },
        isLoading: false,
      });

      render(<SearchDialog {...defaultProps} />);
      const input = screen.getByPlaceholderText(/search tutors, subjects/i);

      await user.type(input, 'test');
      await user.type(input, '{ArrowUp}');

      const tutor2Button = screen.getByTestId('tutor-2');
      expect(tutor2Button).toHaveAttribute('data-selected', 'true');
    });

    it('wraps around when navigating past the last item', async () => {
      const user = userEvent.setup();
      mockUseSearch.mockReturnValue({
        results: {
          tutors: [{ id: 1, name: 'Tutor 1' }],
          subjects: [{ id: 1, name: 'Math' }],
        },
        isLoading: false,
      });

      render(<SearchDialog {...defaultProps} />);
      const input = screen.getByPlaceholderText(/search tutors, subjects/i);

      await user.type(input, 'test');
      await user.type(input, '{ArrowDown}');
      await user.type(input, '{ArrowDown}');

      const tutor1Button = screen.getByTestId('tutor-1');
      expect(tutor1Button).toHaveAttribute('data-selected', 'true');
    });

    it('selects tutor on Enter key', async () => {
      const user = userEvent.setup();
      mockUseSearch.mockReturnValue({
        results: {
          tutors: [{ id: 1, name: 'Tutor 1' }],
          subjects: [],
        },
        isLoading: false,
      });

      render(<SearchDialog {...defaultProps} />);
      const input = screen.getByPlaceholderText(/search tutors, subjects/i);

      await user.type(input, 'test');
      await user.type(input, '{Enter}');

      expect(mockPush).toHaveBeenCalledWith('/tutors/1');
      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it('selects subject on Enter when navigated to subject', async () => {
      const user = userEvent.setup();
      mockUseSearch.mockReturnValue({
        results: {
          tutors: [{ id: 1, name: 'Tutor 1' }],
          subjects: [{ id: 5, name: 'Math' }],
        },
        isLoading: false,
      });

      render(<SearchDialog {...defaultProps} />);
      const input = screen.getByPlaceholderText(/search tutors, subjects/i);

      await user.type(input, 'test');
      await user.type(input, '{ArrowDown}');
      await user.type(input, '{Enter}');

      expect(mockPush).toHaveBeenCalledWith('/tutors?subject=5');
    });
  });

  describe('search input and results display', () => {
    it('updates query on input change', async () => {
      const user = userEvent.setup();
      render(<SearchDialog {...defaultProps} />);

      const input = screen.getByPlaceholderText(/search tutors, subjects/i);
      await user.type(input, 'math');

      expect(input).toHaveValue('math');
      expect(mockUseSearch).toHaveBeenCalledWith('math');
    });

    it('displays search results when query has results', async () => {
      const user = userEvent.setup();
      mockUseSearch.mockReturnValue({
        results: {
          tutors: [{ id: 1, name: 'John Doe' }],
          subjects: [{ id: 1, name: 'Mathematics' }],
        },
        isLoading: false,
      });

      render(<SearchDialog {...defaultProps} />);
      const input = screen.getByPlaceholderText(/search tutors, subjects/i);

      await user.type(input, 'math');

      expect(screen.getByTestId('search-results')).toBeInTheDocument();
    });

    it('resets selection index when query changes', async () => {
      const user = userEvent.setup();
      mockUseSearch.mockReturnValue({
        results: {
          tutors: [
            { id: 1, name: 'Tutor 1' },
            { id: 2, name: 'Tutor 2' },
          ],
          subjects: [],
        },
        isLoading: false,
      });

      render(<SearchDialog {...defaultProps} />);
      const input = screen.getByPlaceholderText(/search tutors, subjects/i);

      await user.type(input, 'test');
      await user.type(input, '{ArrowDown}');

      const tutor2Button = screen.getByTestId('tutor-2');
      expect(tutor2Button).toHaveAttribute('data-selected', 'true');

      await user.clear(input);
      await user.type(input, 'new');

      const tutor1Button = screen.getByTestId('tutor-1');
      expect(tutor1Button).toHaveAttribute('data-selected', 'true');
    });
  });

  describe('loading states', () => {
    it('shows loading spinner when searching', async () => {
      const user = userEvent.setup();
      mockUseSearch.mockReturnValue({
        results: null,
        isLoading: true,
      });

      render(<SearchDialog {...defaultProps} />);
      const input = screen.getByPlaceholderText(/search tutors, subjects/i);

      await user.type(input, 'test');

      expect(screen.getByText(/searching.../i)).toBeInTheDocument();
    });

    it('shows loading indicator in header when loading', async () => {
      const user = userEvent.setup();
      mockUseSearch.mockReturnValue({
        results: null,
        isLoading: true,
      });

      render(<SearchDialog {...defaultProps} />);
      const input = screen.getByPlaceholderText(/search tutors, subjects/i);

      await user.type(input, 'test');

      const dialog = screen.getByRole('dialog');
      const spinners = dialog.querySelectorAll('.animate-spin');
      expect(spinners.length).toBeGreaterThan(0);
    });
  });

  describe('recent searches', () => {
    beforeEach(() => {
      mockRecentSearches.push(
        { id: '1', query: 'math tutor', timestamp: Date.now() },
        { id: '2', query: 'english', timestamp: Date.now() - 1000 }
      );
    });

    it('displays recent searches when no query', () => {
      render(<SearchDialog {...defaultProps} />);

      expect(screen.getByText(/recent searches/i)).toBeInTheDocument();
      expect(screen.getByText('math tutor')).toBeInTheDocument();
      expect(screen.getByText('english')).toBeInTheDocument();
    });

    it('clicking recent search fills query', async () => {
      const user = userEvent.setup();
      render(<SearchDialog {...defaultProps} />);

      await user.click(screen.getByText('math tutor'));

      const input = screen.getByPlaceholderText(/search tutors, subjects/i);
      expect(input).toHaveValue('math tutor');
    });

    it('clicking clear all removes all recent searches', async () => {
      const user = userEvent.setup();
      render(<SearchDialog {...defaultProps} />);

      await user.click(screen.getByText(/clear all/i));

      expect(mockClearRecentSearches).toHaveBeenCalled();
    });

    it('clicking remove button removes specific search', async () => {
      const user = userEvent.setup();
      render(<SearchDialog {...defaultProps} />);

      const removeButtons = screen.getAllByRole('button', {
        name: /remove ".*" from recent searches/i,
      });
      await user.click(removeButtons[0]);

      expect(mockRemoveRecentSearch).toHaveBeenCalledWith('1');
    });

    it('saves query to recent searches when selecting result', async () => {
      const user = userEvent.setup();
      mockUseSearch.mockReturnValue({
        results: {
          tutors: [{ id: 1, name: 'John Doe' }],
          subjects: [],
        },
        isLoading: false,
      });

      render(<SearchDialog {...defaultProps} />);
      const input = screen.getByPlaceholderText(/search tutors, subjects/i);

      await user.type(input, 'john');
      await user.click(screen.getByTestId('tutor-1'));

      expect(mockAddRecentSearch).toHaveBeenCalledWith('john');
    });
  });

  describe('close button', () => {
    it('closes dialog when close button is clicked', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(<SearchDialog isOpen={true} onClose={onClose} />);

      await user.click(screen.getByRole('button', { name: /close search/i }));

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('click outside', () => {
    it('closes dialog when clicking outside', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(
        <div>
          <div data-testid="outside">Outside</div>
          <SearchDialog isOpen={true} onClose={onClose} />
        </div>
      );

      await user.click(screen.getByTestId('outside'));

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('body scroll lock', () => {
    it('locks body scroll when open', () => {
      render(<SearchDialog {...defaultProps} />);
      expect(document.body.style.overflow).toBe('hidden');
    });

    it('unlocks body scroll when closed', () => {
      const { rerender } = render(<SearchDialog {...defaultProps} />);
      expect(document.body.style.overflow).toBe('hidden');

      rerender(<SearchDialog isOpen={false} onClose={vi.fn()} />);
      expect(document.body.style.overflow).toBe('');
    });
  });

  describe('accessibility', () => {
    it('has correct ARIA attributes', () => {
      render(<SearchDialog {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-label', 'Search');
    });

    it('shows keyboard hints', () => {
      render(<SearchDialog {...defaultProps} />);

      expect(screen.getByText('Navigate')).toBeInTheDocument();
      expect(screen.getByText('Select')).toBeInTheDocument();
      expect(screen.getByText('Close')).toBeInTheDocument();
    });
  });
});
