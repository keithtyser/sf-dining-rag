import { useEffect, useRef, useState } from 'react';
import { WebSocketEvent, WebSocketManager } from '@/lib/websocket/WebSocketManager';

// Singleton instance for the WebSocket manager
let wsManager: WebSocketManager | null = null;

export function useWebSocket<T>(event: WebSocketEvent) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [connectionState, setConnectionState] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');
  
  // Use a ref to track the latest event type to prevent stale closures
  const eventRef = useRef(event);
  eventRef.current = event;

  useEffect(() => {
    // Initialize the WebSocket manager if it doesn't exist
    if (!wsManager) {
      wsManager = new WebSocketManager(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001');
    }

    // Connect to the WebSocket server
    wsManager.connect();

    // Update connection state
    const updateConnectionState = () => {
      setConnectionState(wsManager?.getConnectionState() || 'disconnected');
    };

    // Subscribe to the event
    const unsubscribe = wsManager.subscribe<T>(event, (newData) => {
      setData(newData);
      setError(null);
    });

    // Set initial connection state
    updateConnectionState();

    // Cleanup function
    return () => {
      unsubscribe();
    };
  }, [event]); // Only re-run if the event type changes

  return {
    data,
    error,
    connectionState,
    isConnected: connectionState === 'connected',
  };
}

// Hook for subscribing to multiple WebSocket events
export function useWebSocketMulti<T extends Record<WebSocketEvent, any>>(
  events: WebSocketEvent[]
) {
  const [data, setData] = useState<Partial<T>>({});
  const [error, setError] = useState<Error | null>(null);
  const [connectionState, setConnectionState] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');

  useEffect(() => {
    if (!wsManager) {
      wsManager = new WebSocketManager(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001');
    }

    wsManager.connect();

    // Update connection state
    const updateConnectionState = () => {
      setConnectionState(wsManager?.getConnectionState() || 'disconnected');
    };

    // Subscribe to all events
    const unsubscribes = events.map(event =>
      wsManager!.subscribe(event, (newData) => {
        setData(prev => ({
          ...prev,
          [event]: newData,
        }));
        setError(null);
      })
    );

    // Set initial connection state
    updateConnectionState();

    // Cleanup function
    return () => {
      unsubscribes.forEach(unsubscribe => unsubscribe());
    };
  }, [events.join(',')]); // Only re-run if the events array changes

  return {
    data,
    error,
    connectionState,
    isConnected: connectionState === 'connected',
  };
} 