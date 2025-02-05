import { useEffect } from 'react';
import { useAtom } from 'jotai';
import { debugStateAtom } from '@/lib/atoms';

interface StateChange<T = any> {
  atom: string;
  prev: T;
  next: T;
  timestamp: number;
}

const MAX_HISTORY = 100;
const stateHistory: StateChange[] = [];

export function useStateDebugger<T>(atomName: string, value: T, onChange?: (value: T) => void) {
  const [debugState, setDebugState] = useAtom(debugStateAtom);

  useEffect(() => {
    // Add state change to history
    const change: StateChange<T> = {
      atom: atomName,
      prev: stateHistory[stateHistory.length - 1]?.next as T,
      next: value,
      timestamp: Date.now(),
    };

    stateHistory.push(change);
    if (stateHistory.length > MAX_HISTORY) {
      stateHistory.shift();
    }

    // Log state change if debug mode is enabled
    if (process.env.NODE_ENV === 'development' || debugState.debug) {
      console.group(`State Change: ${atomName}`);
      console.log('Previous:', change.prev);
      console.log('Next:', change.next);
      console.log('Timestamp:', new Date(change.timestamp).toISOString());
      console.groupEnd();
    }

    // Call onChange handler if provided
    onChange?.(value);
  }, [value, atomName, debugState.debug, onChange]);

  // Return utility functions for debugging
  return {
    getHistory: () => [...stateHistory],
    clearHistory: () => {
      stateHistory.length = 0;
    },
    getLastChange: () => stateHistory[stateHistory.length - 1],
    getChangesByAtom: (atom: string) => stateHistory.filter(change => change.atom === atom),
    addError: (error: Error) => {
      setDebugState(prev => ({
        ...prev,
        errors: [
          ...prev.errors,
          {
            timestamp: Date.now(),
            message: error.message,
            stack: error.stack,
          },
        ],
      }));
    },
  };
} 