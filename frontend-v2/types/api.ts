/**
 * Standard paginated response matching backend pagination pattern.
 * Use this for all paginated API responses.
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiErrorResponse {
  detail: string;
  code?: string;
}
