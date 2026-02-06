import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card';

describe('Card', () => {
  it('renders Card with children', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText(/card content/i)).toBeInTheDocument();
  });

  it('applies default styling', () => {
    render(<Card>Content</Card>);
    const card = screen.getByText(/content/i);
    expect(card).toHaveClass('rounded-2xl', 'bg-white', 'shadow-soft');
  });

  it('applies hover styling when hover prop is true', () => {
    render(<Card hover>Hover card</Card>);
    const card = screen.getByText(/hover card/i);
    expect(card).toHaveClass('hover:shadow-soft-md', 'cursor-pointer');
  });

  it('merges custom className', () => {
    render(<Card className="custom-class">Custom</Card>);
    const card = screen.getByText(/custom/i);
    expect(card).toHaveClass('custom-class');
  });
});

describe('CardHeader', () => {
  it('renders CardHeader with children', () => {
    render(<CardHeader>Header content</CardHeader>);
    expect(screen.getByText(/header content/i)).toBeInTheDocument();
  });

  it('applies default styling', () => {
    render(<CardHeader>Header</CardHeader>);
    const header = screen.getByText(/header/i);
    expect(header).toHaveClass('flex', 'flex-col', 'mb-4');
  });
});

describe('CardTitle', () => {
  it('renders CardTitle with children', () => {
    render(<CardTitle>My Title</CardTitle>);
    expect(screen.getByRole('heading', { name: /my title/i })).toBeInTheDocument();
  });

  it('renders as h3 element', () => {
    render(<CardTitle>Title</CardTitle>);
    const title = screen.getByRole('heading', { name: /title/i });
    expect(title.tagName).toBe('H3');
  });
});

describe('CardDescription', () => {
  it('renders CardDescription with children', () => {
    render(<CardDescription>Description text</CardDescription>);
    expect(screen.getByText(/description text/i)).toBeInTheDocument();
  });

  it('applies correct text styling', () => {
    render(<CardDescription>Description</CardDescription>);
    const description = screen.getByText(/description/i);
    expect(description).toHaveClass('text-sm', 'text-slate-500');
  });
});

describe('CardContent', () => {
  it('renders CardContent with children', () => {
    render(<CardContent>Main content goes here</CardContent>);
    expect(screen.getByText(/main content goes here/i)).toBeInTheDocument();
  });

  it('merges custom className', () => {
    render(<CardContent className="mt-4">Content</CardContent>);
    const content = screen.getByText(/content/i);
    expect(content).toHaveClass('mt-4');
  });
});

describe('CardFooter', () => {
  it('renders CardFooter with children', () => {
    render(<CardFooter>Footer content</CardFooter>);
    expect(screen.getByText(/footer content/i)).toBeInTheDocument();
  });

  it('applies border styling', () => {
    render(<CardFooter>Footer</CardFooter>);
    const footer = screen.getByText(/footer/i);
    expect(footer).toHaveClass('border-t', 'pt-4', 'mt-4');
  });
});

describe('Card composition', () => {
  it('renders all card components together', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
        </CardHeader>
        <CardDescription>This is a description</CardDescription>
        <CardContent>
          <p>Main content</p>
        </CardContent>
        <CardFooter>
          <button>Action</button>
        </CardFooter>
      </Card>
    );

    expect(screen.getByRole('heading', { name: /card title/i })).toBeInTheDocument();
    expect(screen.getByText(/this is a description/i)).toBeInTheDocument();
    expect(screen.getByText(/main content/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /action/i })).toBeInTheDocument();
  });
});
