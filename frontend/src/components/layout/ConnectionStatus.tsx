"use client";

import React from 'react';
import { Badge } from '../ui/Badge';
import { useWebSocketContext } from '@/providers/WebSocketProvider';
import { Button } from '../ui/Button';
import { AlertCircle, CheckCircle, Loader2, Code } from 'lucide-react';

export function ConnectionStatus() {
  const { connectionState, reconnect, error, isDevelopment } = useWebSocketContext();

  const getStatusColor = () => {
    if (isDevelopment) return 'secondary';
    switch (connectionState) {
      case 'connected':
        return 'success';
      case 'connecting':
        return 'warning';
      case 'disconnected':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const getStatusIcon = () => {
    if (isDevelopment) return <Code className="w-4 h-4" />;
    switch (connectionState) {
      case 'connected':
        return <CheckCircle className="w-4 h-4" />;
      case 'connecting':
        return <Loader2 className="w-4 h-4 animate-spin" />;
      case 'disconnected':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Badge variant={getStatusColor()} className="flex items-center gap-1">
        {getStatusIcon()}
        <span className="capitalize">
          {isDevelopment ? 'Development Mode' : connectionState}
        </span>
      </Badge>
      {!isDevelopment && connectionState === 'disconnected' && (
        <Button
          variant="outline"
          size="sm"
          onClick={reconnect}
          className="h-6 px-2 text-xs"
        >
          Reconnect
        </Button>
      )}
      {!isDevelopment && error && (
        <span className="text-sm text-destructive" title={error.message}>
          Connection Error
        </span>
      )}
    </div>
  );
} 