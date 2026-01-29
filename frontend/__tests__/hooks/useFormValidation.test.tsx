/**
 * Tests for useFormValidation hook
 * Tests validation rules: required, minLength, maxLength, pattern, min, max, custom validate
 */

import { renderHook, act } from '@testing-library/react';
import { useFormValidation } from '@/hooks/useFormValidation';

describe('useFormValidation', () => {
  describe('required validation', () => {
    it('validates required fields with default message', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { email: '' },
          { email: { required: true } }
        )
      );

      act(() => {
        result.current.handleBlur('email');
      });

      expect(result.current.errors.email).toBe('email is required');
    });

    it('validates required fields with custom message', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { email: '' },
          { email: { required: 'Email is required' } }
        )
      );

      act(() => {
        result.current.handleBlur('email');
      });

      expect(result.current.errors.email).toBe('Email is required');
    });

    it('clears error when valid value is provided', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { email: '' },
          { email: { required: true } }
        )
      );

      act(() => {
        result.current.handleBlur('email');
      });
      expect(result.current.errors.email).toBeTruthy();

      act(() => {
        result.current.handleChange('email', 'test@example.com');
      });

      expect(result.current.errors.email).toBe('');
    });
  });

  describe('minLength validation', () => {
    it('validates minimum length', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { password: 'abc' },
          {
            password: {
              minLength: { value: 8, message: 'Password must be at least 8 characters' },
            },
          }
        )
      );

      act(() => {
        result.current.handleBlur('password');
      });

      expect(result.current.errors.password).toBe('Password must be at least 8 characters');
    });

    it('passes when length meets minimum', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { password: 'password123' },
          {
            password: {
              minLength: { value: 8, message: 'Password must be at least 8 characters' },
            },
          }
        )
      );

      act(() => {
        result.current.handleBlur('password');
      });

      expect(result.current.errors.password).toBe('');
    });
  });

  describe('maxLength validation', () => {
    it('validates maximum length', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { bio: 'a'.repeat(300) },
          {
            bio: {
              maxLength: { value: 255, message: 'Bio must not exceed 255 characters' },
            },
          }
        )
      );

      act(() => {
        result.current.handleBlur('bio');
      });

      expect(result.current.errors.bio).toBe('Bio must not exceed 255 characters');
    });
  });

  describe('pattern validation', () => {
    it('validates email pattern', () => {
      const emailPattern = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;

      const { result } = renderHook(() =>
        useFormValidation(
          { email: 'invalid-email' },
          {
            email: {
              pattern: { value: emailPattern, message: 'Invalid email address' },
            },
          }
        )
      );

      act(() => {
        result.current.handleBlur('email');
      });

      expect(result.current.errors.email).toBe('Invalid email address');
    });

    it('passes valid email', () => {
      const emailPattern = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;

      const { result } = renderHook(() =>
        useFormValidation(
          { email: 'test@example.com' },
          {
            email: {
              pattern: { value: emailPattern, message: 'Invalid email address' },
            },
          }
        )
      );

      act(() => {
        result.current.handleBlur('email');
      });

      expect(result.current.errors.email).toBe('');
    });
  });

  describe('min/max number validation', () => {
    it('validates minimum value', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { age: 15 },
          {
            age: {
              min: { value: 18, message: 'Must be at least 18 years old' },
            },
          }
        )
      );

      act(() => {
        result.current.handleBlur('age');
      });

      expect(result.current.errors.age).toBe('Must be at least 18 years old');
    });

    it('validates maximum value', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { rating: 6 },
          {
            rating: {
              max: { value: 5, message: 'Rating cannot exceed 5' },
            },
          }
        )
      );

      act(() => {
        result.current.handleBlur('rating');
      });

      expect(result.current.errors.rating).toBe('Rating cannot exceed 5');
    });
  });

  describe('custom validation', () => {
    it('validates with custom function returning string', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { confirmPassword: 'different' },
          {
            confirmPassword: {
              validate: (value) =>
                value === 'password' ? true : 'Passwords do not match',
            },
          }
        )
      );

      act(() => {
        result.current.handleBlur('confirmPassword');
      });

      expect(result.current.errors.confirmPassword).toBe('Passwords do not match');
    });

    it('validates with custom function returning false', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { terms: false },
          {
            terms: {
              validate: (value) => value === true,
            },
          }
        )
      );

      act(() => {
        result.current.handleBlur('terms');
      });

      expect(result.current.errors.terms).toBe('Invalid value');
    });
  });

  describe('form submission', () => {
    it('calls onSubmit when form is valid', async () => {
      const onSubmit = jest.fn();

      const { result } = renderHook(() =>
        useFormValidation(
          { email: 'test@example.com' },
          { email: { required: true } }
        )
      );

      await act(async () => {
        await result.current.handleSubmit(onSubmit)();
      });

      expect(onSubmit).toHaveBeenCalledWith({ email: 'test@example.com' });
    });

    it('does not call onSubmit when form is invalid', async () => {
      const onSubmit = jest.fn();

      const { result } = renderHook(() =>
        useFormValidation(
          { email: '' },
          { email: { required: true } }
        )
      );

      await act(async () => {
        await result.current.handleSubmit(onSubmit)();
      });

      expect(onSubmit).not.toHaveBeenCalled();
      expect(result.current.errors.email).toBe('email is required');
    });

    it('marks all fields as touched on submit', async () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { email: '', name: '' },
          { email: { required: true }, name: { required: true } }
        )
      );

      await act(async () => {
        await result.current.handleSubmit(() => {})();
      });

      expect(result.current.touched.email).toBe(true);
      expect(result.current.touched.name).toBe(true);
    });
  });

  describe('form utilities', () => {
    it('resets form to initial values', () => {
      const { result } = renderHook(() =>
        useFormValidation(
          { email: '' },
          { email: { required: true } }
        )
      );

      act(() => {
        result.current.handleChange('email', 'changed@example.com');
        result.current.handleBlur('email');
      });

      expect(result.current.values.email).toBe('changed@example.com');

      act(() => {
        result.current.resetForm();
      });

      expect(result.current.values.email).toBe('');
      expect(result.current.errors).toEqual({});
      expect(result.current.touched).toEqual({});
    });

    it('allows setting field error manually', () => {
      const { result } = renderHook(() =>
        useFormValidation({ email: 'test@example.com' }, {})
      );

      act(() => {
        result.current.setFieldError('email', 'Email already exists');
      });

      expect(result.current.errors.email).toBe('Email already exists');
    });

    it('allows setting field value manually', () => {
      const { result } = renderHook(() =>
        useFormValidation({ email: '' }, {})
      );

      act(() => {
        result.current.setFieldValue('email', 'manual@example.com');
      });

      expect(result.current.values.email).toBe('manual@example.com');
    });
  });
});
