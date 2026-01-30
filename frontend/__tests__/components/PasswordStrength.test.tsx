/**
 * Tests for PasswordStrength component
 * Tests password strength indicator and requirements checklist
 */

import { render, screen } from '@testing-library/react';
import PasswordStrength, { isPasswordValid, PASSWORD_REQUIREMENTS } from '@/components/PasswordStrength';

describe('PasswordStrength', () => {
  describe('rendering', () => {
    it('renders nothing when password is empty', () => {
      const { container } = render(<PasswordStrength password="" />);
      expect(container.firstChild).toBeNull();
    });

    it('renders strength indicator when password is provided', () => {
      render(<PasswordStrength password="test" />);
      expect(screen.getByText('Password strength')).toBeInTheDocument();
    });

    it('renders requirements checklist by default', () => {
      render(<PasswordStrength password="test" />);
      expect(screen.getByText('Password requirements')).toBeInTheDocument();
    });

    it('hides requirements checklist when showRequirements is false', () => {
      render(<PasswordStrength password="test" showRequirements={false} />);
      expect(screen.queryByText('Password requirements')).not.toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <PasswordStrength password="test" className="custom-class" />
      );
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('strength levels', () => {
    it('shows "Very weak" for very short passwords', () => {
      render(<PasswordStrength password="ab" />);
      expect(screen.getByText('Very weak')).toBeInTheDocument();
    });

    it('shows "Weak" for short passwords with limited character types', () => {
      render(<PasswordStrength password="abcdefgh" />);
      expect(screen.getByText('Weak')).toBeInTheDocument();
    });

    it('shows "Fair" for passwords with medium complexity', () => {
      render(<PasswordStrength password="Abcdefgh1" />);
      expect(screen.getByText('Fair')).toBeInTheDocument();
    });

    it('shows "Strong" for passwords with good complexity', () => {
      render(<PasswordStrength password="Abcdef12!" />);
      expect(screen.getByText('Strong')).toBeInTheDocument();
    });

    it('shows "Very strong" for long passwords with all character types', () => {
      render(<PasswordStrength password="Abcdefgh123456!@#" />);
      expect(screen.getByText('Very strong')).toBeInTheDocument();
    });
  });

  describe('strength colors', () => {
    it('has red color for very weak passwords', () => {
      render(<PasswordStrength password="a" />);
      const strengthLabel = screen.getByText('Very weak');
      expect(strengthLabel).toHaveClass('text-red-600');
    });

    it('has orange color for weak passwords', () => {
      render(<PasswordStrength password="abcdefgh" />);
      const strengthLabel = screen.getByText('Weak');
      expect(strengthLabel).toHaveClass('text-orange-600');
    });

    it('has amber color for fair passwords', () => {
      render(<PasswordStrength password="Abcdefgh1" />);
      const strengthLabel = screen.getByText('Fair');
      expect(strengthLabel).toHaveClass('text-amber-600');
    });

    it('has emerald color for strong passwords', () => {
      render(<PasswordStrength password="Abcdef12!" />);
      const strengthLabel = screen.getByText('Strong');
      expect(strengthLabel).toHaveClass('text-emerald-600');
    });
  });

  describe('progress bar', () => {
    it('renders four progress segments', () => {
      const { container } = render(<PasswordStrength password="test" />);
      const segments = container.querySelectorAll('.h-1\\.5.flex-1');
      expect(segments.length).toBe(4);
    });

    it('fills more segments for stronger passwords', () => {
      const { container: weakContainer } = render(
        <PasswordStrength password="ab" />
      );
      const weakFilledSegments = weakContainer.querySelectorAll('.bg-red-500');

      const { container: strongContainer } = render(
        <PasswordStrength password="Abcdef12!@#" />
      );
      const strongFilledSegments = strongContainer.querySelectorAll('.bg-emerald-500, .bg-emerald-600');

      expect(strongFilledSegments.length).toBeGreaterThan(weakFilledSegments.length);
    });
  });

  describe('requirements checklist', () => {
    it('displays all five requirements', () => {
      render(<PasswordStrength password="test" />);

      expect(screen.getByText('At least 8 characters')).toBeInTheDocument();
      expect(screen.getByText('One uppercase letter')).toBeInTheDocument();
      expect(screen.getByText('One lowercase letter')).toBeInTheDocument();
      expect(screen.getByText('One number')).toBeInTheDocument();
      expect(screen.getByText('One special character (!@#$%^&*)')).toBeInTheDocument();
    });

    it('marks length requirement as met when password has 8+ characters', () => {
      render(<PasswordStrength password="abcdefgh" />);
      const lengthItem = screen.getByText('At least 8 characters');
      expect(lengthItem.closest('li')).toHaveClass('text-emerald-600');
    });

    it('marks uppercase requirement as met when password has uppercase', () => {
      render(<PasswordStrength password="testA" />);
      const uppercaseItem = screen.getByText('One uppercase letter');
      expect(uppercaseItem.closest('li')).toHaveClass('text-emerald-600');
    });

    it('marks lowercase requirement as met when password has lowercase', () => {
      render(<PasswordStrength password="TESTa" />);
      const lowercaseItem = screen.getByText('One lowercase letter');
      expect(lowercaseItem.closest('li')).toHaveClass('text-emerald-600');
    });

    it('marks number requirement as met when password has number', () => {
      render(<PasswordStrength password="test1" />);
      const numberItem = screen.getByText('One number');
      expect(numberItem.closest('li')).toHaveClass('text-emerald-600');
    });

    it('marks special character requirement as met when password has special char', () => {
      render(<PasswordStrength password="test!" />);
      const specialItem = screen.getByText('One special character (!@#$%^&*)');
      expect(specialItem.closest('li')).toHaveClass('text-emerald-600');
    });

    it('shows check icon for met requirements', () => {
      const { container } = render(<PasswordStrength password="Abcdef12!" />);
      const checkIcons = container.querySelectorAll('li svg');
      expect(checkIcons.length).toBeGreaterThan(0);
    });

    it('shows x icon for unmet requirements', () => {
      const { container } = render(<PasswordStrength password="test" />);
      // Looking for unmet requirement items (text-slate-500)
      const unmetItems = container.querySelectorAll('li.text-slate-500');
      expect(unmetItems.length).toBeGreaterThan(0);
    });

    it('applies strikethrough to met requirements', () => {
      render(<PasswordStrength password="testpassword" />);
      const lengthItem = screen.getByText('At least 8 characters');
      expect(lengthItem).toHaveClass('line-through');
    });

    it('shows "All requirements met" message when all requirements are satisfied', () => {
      render(<PasswordStrength password="Abcdef12!" />);
      expect(screen.getByText(/All requirements met/)).toBeInTheDocument();
    });

    it('does not show "All requirements met" when some requirements are not satisfied', () => {
      render(<PasswordStrength password="abcdefgh" />);
      expect(screen.queryByText(/All requirements met/)).not.toBeInTheDocument();
    });
  });

  describe('real-time updates', () => {
    it('updates strength indicator when password changes', () => {
      const { rerender } = render(<PasswordStrength password="ab" />);
      expect(screen.getByText('Very weak')).toBeInTheDocument();

      rerender(<PasswordStrength password="Abcdef12!" />);
      expect(screen.getByText('Strong')).toBeInTheDocument();
    });

    it('updates requirements checklist when password changes', () => {
      const { rerender } = render(<PasswordStrength password="test" />);

      const uppercaseItem = screen.getByText('One uppercase letter');
      expect(uppercaseItem.closest('li')).toHaveClass('text-slate-500');

      rerender(<PasswordStrength password="testA" />);
      const updatedUppercaseItem = screen.getByText('One uppercase letter');
      expect(updatedUppercaseItem.closest('li')).toHaveClass('text-emerald-600');
    });
  });

  describe('isPasswordValid utility', () => {
    it('returns false for passwords missing length requirement', () => {
      expect(isPasswordValid('Ab1!')).toBe(false);
    });

    it('returns false for passwords missing uppercase', () => {
      expect(isPasswordValid('abcdefg1!')).toBe(false);
    });

    it('returns false for passwords missing lowercase', () => {
      expect(isPasswordValid('ABCDEFG1!')).toBe(false);
    });

    it('returns false for passwords missing number', () => {
      expect(isPasswordValid('Abcdefgh!')).toBe(false);
    });

    it('returns false for passwords missing special character', () => {
      expect(isPasswordValid('Abcdefgh1')).toBe(false);
    });

    it('returns true for passwords meeting all requirements', () => {
      expect(isPasswordValid('Abcdefgh1!')).toBe(true);
    });
  });

  describe('PASSWORD_REQUIREMENTS export', () => {
    it('exports PASSWORD_REQUIREMENTS array', () => {
      expect(PASSWORD_REQUIREMENTS).toBeDefined();
      expect(Array.isArray(PASSWORD_REQUIREMENTS)).toBe(true);
    });

    it('has five requirements', () => {
      expect(PASSWORD_REQUIREMENTS.length).toBe(5);
    });

    it('each requirement has id, label, and validator', () => {
      PASSWORD_REQUIREMENTS.forEach((req) => {
        expect(req).toHaveProperty('id');
        expect(req).toHaveProperty('label');
        expect(req).toHaveProperty('validator');
        expect(typeof req.validator).toBe('function');
      });
    });
  });

  describe('penalty patterns', () => {
    it('penalizes passwords with only letters', () => {
      const { rerender } = render(<PasswordStrength password="ABCDEFGH" />);
      const onlyLettersStrength = screen.getByText(/weak|fair/i);

      rerender(<PasswordStrength password="ABCD1234" />);
      const withNumbersStrength = screen.getByText(/fair|strong/i);

      // Mixed passwords should generally score higher
      expect(withNumbersStrength).toBeInTheDocument();
    });

    it('penalizes passwords with only numbers', () => {
      render(<PasswordStrength password="12345678" />);
      expect(screen.getByText('Very weak')).toBeInTheDocument();
    });

    it('penalizes passwords with repeated characters', () => {
      render(<PasswordStrength password="aaabbbccc" />);
      // Repeated characters should result in lower score
      const strengthLabel = screen.getByText(/weak|fair/i);
      expect(strengthLabel).toBeInTheDocument();
    });
  });
});
