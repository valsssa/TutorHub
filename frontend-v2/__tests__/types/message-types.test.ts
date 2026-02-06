import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Message type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/message.ts'),
    'utf-8'
  );

  it('should use message as primary content field', () => {
    expect(typeFile).toMatch(/^\s+message: string;/m);
  });

  it('should NOT have content alias', () => {
    expect(typeFile).not.toMatch(/^\s+content\??: string;/m);
  });
});

describe('PaginatedMessagesResponse type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/message.ts'),
    'utf-8'
  );

  it('should use messages as primary field', () => {
    expect(typeFile).toMatch(/messages: Message\[\]/);
  });

  it('should NOT have items alias', () => {
    expect(typeFile).not.toMatch(/items\?: Message\[\]/);
  });
});
