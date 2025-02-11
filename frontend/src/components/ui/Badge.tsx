import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80',
        secondary:
          'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive:
          'border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80',
        outline: 'text-foreground',
        success: 'border-transparent bg-green-500 text-white shadow hover:bg-green-600',
        warning: 'border-transparent bg-yellow-500 text-white shadow hover:bg-yellow-600',
        info: 'border-transparent bg-blue-500 text-white shadow hover:bg-blue-600',
        ghost: 'border-transparent bg-accent text-accent-foreground hover:bg-accent/80',
      },
      size: {
        default: 'px-2.5 py-0.5 text-xs',
        sm: 'px-2 py-0.5 text-[10px]',
        lg: 'px-3 py-1 text-sm',
      },
      isInteractive: {
        true: 'cursor-pointer',
        false: '',
      },
      withDot: {
        true: 'pl-2',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
      isInteractive: false,
      withDot: false,
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  dotColor?: string;
}

function Badge({
  className,
  variant,
  size,
  isInteractive,
  withDot,
  dotColor,
  ...props
}: BadgeProps) {
  return (
    <div
      className={cn(
        badgeVariants({ variant, size, isInteractive, withDot, className })
      )}
      {...props}
    >
      {withDot && (
        <div
          className="mr-1 h-1.5 w-1.5 rounded-full"
          style={{ backgroundColor: dotColor }}
        />
      )}
      {props.children}
    </div>
  );
}

export { Badge, badgeVariants }; 