import { cn } from '@/lib/utils';
import { forwardRef } from 'react';

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
}

export const Avatar = forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, size = 'md', children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'relative flex shrink-0 overflow-hidden rounded-full',
          {
            'h-8 w-8': size === 'sm',
            'h-10 w-10': size === 'md',
            'h-12 w-12': size === 'lg',
          },
          'transition-colors duration-200',
          className
        )}
        {...props}
      >
        <div className="flex h-full w-full items-center justify-center">
          {children}
        </div>
      </div>
    );
  }
);

interface AvatarFallbackProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
}

export function AvatarFallback({ className, children, ...props }: AvatarFallbackProps) {
  return (
    <div
      className={cn(
        'flex h-full w-full items-center justify-center rounded-full bg-muted',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
} 