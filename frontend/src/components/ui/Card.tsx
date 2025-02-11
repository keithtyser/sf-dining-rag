import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const cardVariants = cva(
  'rounded-lg border bg-card text-card-foreground shadow transition-all duration-200',
  {
    variants: {
      variant: {
        default: 'hover:shadow-md',
        ghost: 'border-none shadow-none hover:bg-accent/50',
        outline: 'bg-background shadow-none',
        elevated: 'shadow-lg hover:shadow-xl',
        interactive: 'cursor-pointer hover:scale-[1.02] hover:shadow-lg active:scale-[0.98]',
      },
      size: {
        default: 'p-6',
        sm: 'p-4',
        lg: 'p-8',
        compact: 'p-2',
      },
      isFullWidth: {
        true: 'w-full',
        false: '',
      },
      isClickable: {
        true: 'cursor-pointer hover:border-primary/50',
        false: '',
      },
      isSelected: {
        true: 'border-primary bg-primary/5',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
      isFullWidth: false,
      isClickable: false,
      isSelected: false,
    },
  }
);

const cardHeaderVariants = cva('flex flex-col space-y-1.5', {
  variants: {
    size: {
      default: 'px-6 pt-6',
      sm: 'px-4 pt-4',
      lg: 'px-8 pt-8',
      compact: 'px-2 pt-2',
    },
  },
  defaultVariants: {
    size: 'default',
  },
});

const cardFooterVariants = cva(
  'flex items-center mt-4',
  {
    variants: {
      size: {
        default: 'px-6 pb-6',
        sm: 'px-4 pb-4',
        lg: 'px-8 pb-8',
        compact: 'px-2 pb-2',
      },
    },
    defaultVariants: {
      size: 'default',
    },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  asChild?: boolean;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, size, isFullWidth, isClickable, isSelected, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        cardVariants({ variant, size, isFullWidth, isClickable, isSelected, className })
      )}
      {...props}
    />
  )
);
Card.displayName = 'Card';

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { size?: VariantProps<typeof cardHeaderVariants>['size'] }
>(({ className, size, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(cardHeaderVariants({ size, className }))}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement> & { as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' }
>(({ className, as: Comp = 'h3', ...props }, ref) => (
  <Comp
    ref={ref}
    className={cn('text-lg font-semibold leading-none tracking-tight', className)}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-muted-foreground', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { size?: VariantProps<typeof cardHeaderVariants>['size'] }
>(({ className, size, ...props }, ref) => (
  <div 
    ref={ref} 
    className={cn('px-6 py-4', {
      'px-4 py-3': size === 'sm',
      'px-8 py-6': size === 'lg',
      'px-2 py-1': size === 'compact',
    }, className)} 
    {...props} 
  />
));
CardContent.displayName = 'CardContent';

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { size?: VariantProps<typeof cardFooterVariants>['size'] }
>(({ className, size, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(cardFooterVariants({ size, className }))}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
}; 