import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('PaginatedResponse type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/api.ts'),
    'utf-8'
  );

  it('should have consistent pagination fields', () => {
    expect(typeFile).toContain('total: number');
    expect(typeFile).toContain('page: number');
    expect(typeFile).toContain('page_size: number');
  });

  it('should be generic with items field', () => {
    expect(typeFile).toMatch(/items: T\[\]/);
  });
});
