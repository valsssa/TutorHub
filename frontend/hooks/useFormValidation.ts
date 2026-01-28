import { useState, useCallback } from "react";

export interface ValidationRule {
  required?: boolean | string;
  minLength?: { value: number; message: string };
  maxLength?: { value: number; message: string };
  pattern?: { value: RegExp; message: string };
  min?: { value: number; message: string };
  max?: { value: number; message: string };
  validate?: (value: any) => boolean | string;
}

export interface FieldConfig {
  [key: string]: ValidationRule;
}

export interface FormErrors {
  [key: string]: string;
}

export interface UseFormValidationReturn<T> {
  values: T;
  errors: FormErrors;
  touched: { [key: string]: boolean };
  isValid: boolean;
  handleChange: (name: string, value: any) => void;
  handleBlur: (name: string) => void;
  handleSubmit: (
    onSubmit: (values: T) => void | Promise<void>,
  ) => (e?: React.FormEvent) => Promise<void>;
  setFieldError: (field: string, error: string) => void;
  setFieldValue: (field: string, value: any) => void;
  resetForm: () => void;
  validateField: (name: string, value: any) => string;
}

export function useFormValidation<T extends Record<string, any>>(
  initialValues: T,
  validationRules: FieldConfig,
): UseFormValidationReturn<T> {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<{ [key: string]: boolean }>({});

  const validateField = useCallback(
    (name: string, value: any): string => {
      const rules = validationRules[name];
      if (!rules) return "";

      // Required validation
      if (rules.required) {
        const isEmpty = value === "" || value === null || value === undefined;
        if (isEmpty) {
          return typeof rules.required === "string"
            ? rules.required
            : `${name} is required`;
        }
      }

      // Skip other validations if empty and not required
      if (value === "" || value === null || value === undefined) {
        return "";
      }

      // MinLength validation
      if (rules.minLength && typeof value === "string") {
        if (value.length < rules.minLength.value) {
          return rules.minLength.message;
        }
      }

      // MaxLength validation
      if (rules.maxLength && typeof value === "string") {
        if (value.length > rules.maxLength.value) {
          return rules.maxLength.message;
        }
      }

      // Pattern validation
      if (rules.pattern && typeof value === "string") {
        if (!rules.pattern.value.test(value)) {
          return rules.pattern.message;
        }
      }

      // Min value validation
      if (rules.min !== undefined) {
        const numValue = typeof value === "string" ? parseFloat(value) : value;
        if (numValue < rules.min.value) {
          return rules.min.message;
        }
      }

      // Max value validation
      if (rules.max !== undefined) {
        const numValue = typeof value === "string" ? parseFloat(value) : value;
        if (numValue > rules.max.value) {
          return rules.max.message;
        }
      }

      // Custom validation
      if (rules.validate) {
        const result = rules.validate(value);
        if (typeof result === "string") {
          return result;
        }
        if (result === false) {
          return "Invalid value";
        }
      }

      return "";
    },
    [validationRules],
  );

  const validateAllFields = useCallback((): boolean => {
    const newErrors: FormErrors = {};
    let isValid = true;

    Object.keys(validationRules).forEach((name) => {
      const error = validateField(name, values[name]);
      if (error) {
        newErrors[name] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  }, [values, validationRules, validateField]);

  const handleChange = useCallback(
    (name: string, value: any) => {
      setValues((prev) => ({ ...prev, [name]: value }));

      // Validate on change if field has been touched
      if (touched[name]) {
        const error = validateField(name, value);
        setErrors((prev) => ({ ...prev, [name]: error }));
      }
    },
    [touched, validateField],
  );

  const handleBlur = useCallback(
    (name: string) => {
      setTouched((prev) => ({ ...prev, [name]: true }));

      // Validate on blur
      const error = validateField(name, values[name]);
      setErrors((prev) => ({ ...prev, [name]: error }));
    },
    [values, validateField],
  );

  const setFieldError = useCallback((field: string, error: string) => {
    setErrors((prev) => ({ ...prev, [field]: error }));
  }, []);

  const setFieldValue = useCallback((field: string, value: any) => {
    setValues((prev) => ({ ...prev, [field]: value }));
  }, []);

  const resetForm = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  const handleSubmit = useCallback(
    (onSubmit: (values: T) => void | Promise<void>) =>
      async (e?: React.FormEvent) => {
        if (e) {
          e.preventDefault();
        }

        // Mark all fields as touched
        const allTouched: { [key: string]: boolean } = {};
        Object.keys(validationRules).forEach((key) => {
          allTouched[key] = true;
        });
        setTouched(allTouched);

        // Validate all fields
        if (validateAllFields()) {
          await onSubmit(values);
        }
      },
    [values, validationRules, validateAllFields],
  );

  const isValid =
    Object.keys(errors).length === 0 && Object.keys(touched).length > 0;

  return {
    values,
    errors,
    touched,
    isValid,
    handleChange,
    handleBlur,
    handleSubmit,
    setFieldError,
    setFieldValue,
    resetForm,
    validateField,
  };
}
