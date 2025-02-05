import React, { createContext, useContext, useEffect, useState } from 'react';
import { WebSocketManager } from '@/lib/websocket/WebSocketManager';

interface WebSocketContextValue {
  connectionState: 'connected' | 'connecting' | 'disconnected';
  reconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}

interface WebSocketProviderProps {
  children: React.ReactNode;
  url?: string;
}

export function WebSocketProvider({
  children,
  url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001',
}: WebSocketProviderProps) {
  const [wsManager] = useState(() => new WebSocketManager(url));
  const [connectionState, setConnectionState] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');

  useEffect(() => {
    // Initial connection
    wsManager.connect();

    // Set up an interval to check connection state
    const interval = setInterval(() => {
      setConnectionState(wsManager.getConnectionState());
    }, 1000);

    // Cleanup
    return () => {
      clearInterval(interval);
      wsManager.disconnect();
    };
  }, [wsManager]);

  const reconnect = () => {
    wsManager.disconnect();
    wsManager.connect();
  };

  const value = {
    connectionState,
    reconnect,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
} 