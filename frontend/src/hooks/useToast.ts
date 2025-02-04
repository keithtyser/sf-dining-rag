import { useState, useCallback } from 'react';

export type ToastType = 'default' | 'success' | 'destructive' | 'info' | 'warning';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  variant?: ToastType;
  duration?: number;
}

export interface ToastOptions {
  title?: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  variant?: ToastType;
  duration?: number;
}

const DEFAULT_TOAST_DURATION = 5000;

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback(
    (options: ToastOptions) => {
      const id = Math.random().toString(36).slice(2);
      const toast: Toast = {
        id,
        title: options.title,
        description: options.description,
        action: options.action,
        variant: options.variant || 'default',
        duration: options.duration || DEFAULT_TOAST_DURATION,
      };

      setToasts(prev => [...prev, toast]);

      if (toast.duration && toast.duration > 0) {
        setTimeout(() => {
          dismissToast(id);
        }, toast.duration);
      }

      return id;
    },
    []
  );

  const dismissToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const success = useCallback(
    (options: Omit<ToastOptions, 'variant'>) =>
      addToast({ ...options, variant: 'success' }),
    [addToast]
  );

  const error = useCallback(
    (options: Omit<ToastOptions, 'variant'>) =>
      addToast({ ...options, variant: 'destructive' }),
    [addToast]
  );

  const info = useCallback(
    (options: Omit<ToastOptions, 'variant'>) =>
      addToast({ ...options, variant: 'info' }),
    [addToast]
  );

  const warning = useCallback(
    (options: Omit<ToastOptions, 'variant'>) =>
      addToast({ ...options, variant: 'warning' }),
    [addToast]
  );

  return {
    toasts,
    addToast,
    dismissToast,
    success,
    error,
    info,
    warning,
  };
} 