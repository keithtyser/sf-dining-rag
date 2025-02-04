import React from 'react';
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider as RadixToastProvider,
  ToastTitle,
  ToastViewport,
  ToastAction,
} from './Toast';
import { useToast } from '@/hooks/useToast';

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const { toasts, dismissToast } = useToast();

  return (
    <RadixToastProvider>
      {children}
      {toasts.map(({ id, title, description, action, variant }) => (
        <Toast key={id} variant={variant} onOpenChange={() => dismissToast(id)}>
          <div className="grid gap-1">
            {title && <ToastTitle>{title}</ToastTitle>}
            {description && (
              <ToastDescription>{description}</ToastDescription>
            )}
          </div>
          {action && (
            <ToastAction
              altText={action.label}
              onClick={() => {
                action.onClick();
                dismissToast(id);
              }}
            >
              {action.label}
            </ToastAction>
          )}
          <ToastClose />
        </Toast>
      ))}
      <ToastViewport />
    </RadixToastProvider>
  );
} 