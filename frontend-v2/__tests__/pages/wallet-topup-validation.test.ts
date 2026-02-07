import { describe, it, expect } from 'vitest';

describe('Wallet topup validation', () => {
  function validateTopup(amountStr: string): { valid: boolean; error: string; cents?: number } {
    const amount = parseFloat(amountStr);
    if (!amount || amount <= 0) {
      return { valid: false, error: 'Amount must be greater than $0' };
    }
    if (amount > 10000) {
      return { valid: false, error: 'Amount cannot exceed $10,000' };
    }
    return { valid: true, error: '', cents: Math.round(amount * 100) };
  }

  it('should reject zero amount', () => {
    const result = validateTopup('0');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('greater than');
  });

  it('should reject negative amount', () => {
    const result = validateTopup('-5');
    expect(result.valid).toBe(false);
  });

  it('should reject empty string', () => {
    const result = validateTopup('');
    expect(result.valid).toBe(false);
  });

  it('should reject amounts over 10000', () => {
    const result = validateTopup('10001');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('10,000');
  });

  it('should accept exactly 10000', () => {
    const result = validateTopup('10000');
    expect(result.valid).toBe(true);
    expect(result.cents).toBe(1000000);
  });

  it('should accept valid amounts', () => {
    const result = validateTopup('25');
    expect(result.valid).toBe(true);
    expect(result.cents).toBe(2500);
  });

  it('should accept decimal amounts', () => {
    const result = validateTopup('49.99');
    expect(result.valid).toBe(true);
    expect(result.cents).toBe(4999);
  });

  it('should use Math.round for proper cents conversion', () => {
    // 19.99 * 100 might be 1998.9999... in floating point
    const result = validateTopup('19.99');
    expect(result.cents).toBe(1999);

    const result2 = validateTopup('0.01');
    expect(result2.cents).toBe(1);
  });

  it('should accept small positive amounts', () => {
    const result = validateTopup('0.50');
    expect(result.valid).toBe(true);
    expect(result.cents).toBe(50);
  });
});
