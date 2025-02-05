import React from 'react';
import { cn } from '@/lib/utils';
import { useWebSocketContext } from '@/providers/WebSocketProvider';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from './Button';

interface ConnectionStatusProps {
  className?: string;
  showReconnect?: boolean;
}

export function ConnectionStatus({
  className,
  showReconnect = true,
}: ConnectionStatusProps) {
  const { connectionState, reconnect } = useWebSocketContext();

  return (
    <div
      className={cn(
        'flex items-center gap-2 text-sm',
        {
          'text-green-500': connectionState === 'connected',
          'text-yellow-500': connectionState === 'connecting',
          'text-destructive': connectionState === 'disconnected',
        },
        className
      )}
    >
      {connectionState === 'connected' ? (
        <CheckCircle2 className="h-4 w-4" />
      ) : connectionState === 'connecting' ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <AlertCircle className="h-4 w-4" />
      )}
      <span className="capitalize">{connectionState}</span>
      {showReconnect && connectionState === 'disconnected' && (
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2 text-xs"
          onClick={reconnect}
        >
          Reconnect
        </Button>
      )}
    </div>
  );
}

ConnectionStatus.displayName = 'ConnectionStatus'; 