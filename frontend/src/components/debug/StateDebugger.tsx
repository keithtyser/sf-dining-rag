import React from 'react';
import { useAtom } from 'jotai';
import { cn } from '@/lib/utils';
import { debugStateAtom, uiStateAtom } from '@/lib/atoms';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { CodeBlock } from '../ui/CodeBlock';

interface StateDebuggerProps {
  className?: string;
}

export function StateDebugger({ className }: StateDebuggerProps) {
  const [debugState, setDebugState] = useAtom(debugStateAtom);
  const [uiState] = useAtom(uiStateAtom);

  if (!uiState.debug) return null;

  const clearErrors = () => {
    setDebugState(prev => ({ ...prev, errors: [] }));
  };

  const toggleDebug = () => {
    setDebugState(prev => ({ ...prev, debug: !prev.debug }));
  };

  return (
    <Card className={cn('', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>State Debugger</CardTitle>
          <div className="space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={clearErrors}
              disabled={debugState.errors.length === 0}
            >
              Clear Errors
            </Button>
            <Button
              variant={debugState.debug ? 'destructive' : 'default'}
              size="sm"
              onClick={toggleDebug}
            >
              {debugState.debug ? 'Disable' : 'Enable'} Debug Mode
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* WebSocket Stats */}
        <div>
          <h3 className="mb-2 text-sm font-medium">WebSocket Statistics</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Connections</div>
              <div className="text-2xl font-bold">{debugState.wsConnections}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Messages</div>
              <div className="text-2xl font-bold">{debugState.wsMessages}</div>
            </div>
          </div>
        </div>

        {/* API Stats */}
        <div>
          <h3 className="mb-2 text-sm font-medium">API Calls</h3>
          <div className="text-2xl font-bold">{debugState.apiCalls}</div>
        </div>

        {/* Errors */}
        {debugState.errors.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-medium">Recent Errors</h3>
            <div className="space-y-2">
              {debugState.errors.map((error, index) => (
                <div key={index} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-destructive">
                      {error.message}
                    </span>
                    <span className="text-muted-foreground">
                      {new Date(error.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {error.stack && (
                    <CodeBlock
                      code={error.stack}
                      language="plaintext"
                      variant="ghost"
                      size="sm"
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 