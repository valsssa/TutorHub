import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Notification type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/notification.ts'),
    'utf-8'
  );

  it('should use typed NotificationType for type field', () => {
    expect(typeFile).toMatch(/type: NotificationType/);
  });
});

describe('NotificationStats type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/notification.ts'),
    'utf-8'
  );

  it('should use count field matching backend', () => {
    // Backend returns { count: int }, not unread_count
    expect(typeFile).toMatch(/count: number/);
  });
});
