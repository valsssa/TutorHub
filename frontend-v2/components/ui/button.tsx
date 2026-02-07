import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-xl font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:ring-offset-slate-900 disabled:opacity-50 disabled:pointer-events-none whitespace-nowrap',
  {
    variants: {
      variant: {
        primary:
          'bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-500 shadow-soft hover:shadow-soft-md',
        secondary:
          'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700',
        outline:
          'border-2 border-slate-200 bg-transparent hover:border-primary-500 hover:text-primary-600 dark:border-slate-700',
        ghost:
          'bg-transparent hover:bg-slate-100 dark:hover:bg-slate-800',
        danger:
          'bg-red-500 text-white hover:bg-red-600 focus:ring-red-500',
        link:
          'bg-transparent text-primary-600 hover:underline p-0 h-auto',
      },
      size: {
        sm: 'h-9 sm:h-8 px-3 text-sm min-h-[36px] sm:min-h-0',
        md: 'h-11 sm:h-10 px-4 text-sm min-h-[44px] sm:min-h-0',
        lg: 'h-12 px-6 text-base min-h-[48px]',
        icon: 'h-11 w-11 sm:h-10 sm:w-10 min-h-[44px] sm:min-h-0',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  asChild?: boolean;
}

// HTML attributes that only apply to <button> elements, not to <a> or other elements
const BUTTON_ONLY_ATTRS = new Set([
  'type',
  'disabled',
  'formAction',
  'formEncType',
  'formMethod',
  'formNoValidate',
  'formTarget',
  'name',
  'value',
  'form',
  'autofocus',
]);

function filterButtonAttrs(props: Record<string, unknown>): Record<string, unknown> {
  const filtered: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(props)) {
    if (!BUTTON_ONLY_ATTRS.has(key)) {
      filtered[key] = value;
    }
  }
  return filtered;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, asChild, children, disabled, ...props }, ref) => {
    const isDisabledOrLoading = disabled || loading;

    if (asChild && React.isValidElement(children)) {
      const childProps = (children as React.ReactElement<{ className?: string; children?: React.ReactNode }>).props;
      const classes = cn(
        buttonVariants({ variant, size }),
        isDisabledOrLoading && 'pointer-events-none opacity-50',
        className,
        childProps.className,
      );

      // Filter out button-only HTML attrs; pass only safe attrs
      const safeProps = filterButtonAttrs(props);

      // Build new children: prepend loader spinner if loading
      const childChildren = childProps.children;
      const newChildren = loading
        ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {childChildren}
            </>
          )
        : childChildren;

      return React.cloneElement(children as React.ReactElement<Record<string, unknown>>, {
        className: classes,
        ref,
        ...(isDisabledOrLoading ? { 'aria-disabled': 'true' } : {}),
        ...safeProps,
        children: newChildren,
      });
    }

    const classes = cn(buttonVariants({ variant, size }), className);

    return (
      <button
        className={classes}
        ref={ref}
        disabled={isDisabledOrLoading}
        aria-busy={loading || undefined}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
