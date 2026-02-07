import { describe, it, expect } from 'vitest';

describe('Tutor filter URL sync', () => {
  function buildUrlFromFilters(filters: {
    subject?: string;
    search_query?: string;
    min_rating?: number;
    price_min?: number;
    price_max?: number;
    sort_by?: string;
    page?: number;
  }): string {
    const params = new URLSearchParams();
    if (filters.subject) params.set('subject', filters.subject);
    if (filters.search_query) params.set('q', filters.search_query);
    if (filters.min_rating !== undefined) params.set('rating', String(filters.min_rating));
    if (filters.price_min !== undefined) params.set('price_min', String(filters.price_min));
    if (filters.price_max !== undefined) params.set('price_max', String(filters.price_max));
    if (filters.sort_by && filters.sort_by !== 'rating') params.set('sort', filters.sort_by);
    if (filters.page && filters.page > 1) params.set('page', String(filters.page));
    const qs = params.toString();
    return qs ? `/tutors?${qs}` : '/tutors';
  }

  it('should produce clean URL with no filters', () => {
    const url = buildUrlFromFilters({});
    expect(url).toBe('/tutors');
  });

  it('should include subject filter in URL', () => {
    const url = buildUrlFromFilters({ subject: 'Math' });
    expect(url).toBe('/tutors?subject=Math');
  });

  it('should include search query as q param', () => {
    const url = buildUrlFromFilters({ search_query: 'John' });
    expect(url).toBe('/tutors?q=John');
  });

  it('should include multiple filters', () => {
    const url = buildUrlFromFilters({
      subject: 'Physics',
      min_rating: 4,
      price_min: 25,
      price_max: 50,
      sort_by: 'rate_asc',
      page: 2,
    });

    expect(url).toContain('subject=Physics');
    expect(url).toContain('rating=4');
    expect(url).toContain('price_min=25');
    expect(url).toContain('price_max=50');
    expect(url).toContain('sort=rate_asc');
    expect(url).toContain('page=2');
  });

  it('should omit default sort_by (rating)', () => {
    const url = buildUrlFromFilters({ sort_by: 'rating' });
    expect(url).toBe('/tutors');
  });

  it('should omit page 1', () => {
    const url = buildUrlFromFilters({ page: 1 });
    expect(url).toBe('/tutors');
  });

  it('should restore filters from URL params', () => {
    const url = new URL('http://localhost/tutors?subject=Math&q=John&rating=3&price_min=25&price_max=100&sort=rate_desc&page=3');
    const params = url.searchParams;

    expect(params.get('subject')).toBe('Math');
    expect(params.get('q')).toBe('John');
    expect(Number(params.get('rating'))).toBe(3);
    expect(Number(params.get('price_min'))).toBe(25);
    expect(Number(params.get('price_max'))).toBe(100);
    expect(params.get('sort')).toBe('rate_desc');
    expect(Number(params.get('page'))).toBe(3);
  });
});
