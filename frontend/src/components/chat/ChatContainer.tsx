import React, { useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Send, Copy, Command, Loader2 } from 'lucide-react';
import { CodeBlock } from '../ui/CodeBlock';
import { useToast } from '@/hooks/useToast';
import type { VirtualItem } from '@tanstack/react-virtual';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  status?: 'sending' | 'error';
  error?: string;
}

interface ChatContainerProps {
  className?: string;
  messages: Message[];
  isTyping?: boolean;
  onSendMessage: (message: string) => Promise<void>;
  onRetry?: (messageId: string) => Promise<void>;
}

export function ChatContainer({
  className,
  messages,
  isTyping = false,
  onSendMessage,
  onRetry,
}: ChatContainerProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const parentRef = useRef<HTMLDivElement>(null);
  const { addToast } = useToast();

  // Set up virtualization for messages
  const rowVirtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100, // Estimate each message height
    overscan: 5, // Number of items to render outside of the visible area
  });

  const handleSend = async () => {
    if (!input.trim()) return;

    try {
      setIsLoading(true);
      await onSendMessage(input);
      setInput('');
    } catch (error) {
      addToast({
        title: 'Failed to send message',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      addToast({
        title: 'Copied to clipboard',
        description: 'Message content has been copied',
        variant: 'success',
      });
    } catch (error) {
      addToast({
        title: 'Failed to copy',
        description: 'Could not copy message to clipboard',
        variant: 'destructive',
      });
    }
  };

  return (
    <Card className={cn('flex h-full flex-col overflow-hidden', className)}>
      {/* Messages Container */}
      <div
        ref={parentRef}
        className="flex-1 overflow-auto p-4"
        style={{
          height: '100%',
          width: '100%',
        }}
      >
        <div
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {rowVirtualizer.getVirtualItems().map((virtualRow: VirtualItem) => {
            const message = messages[virtualRow.index];
            return (
              <div
                key={message.id}
                data-index={virtualRow.index}
                ref={rowVirtualizer.measureElement}
                className={cn(
                  'mb-4 flex',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualRow.start}px)`,
                }}
              >
                <div
                  className={cn(
                    'relative max-w-[80%] rounded-lg px-4 py-2',
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted',
                    message.status === 'error' && 'border-2 border-destructive'
                  )}
                >
                  {/* Message Content */}
                  {message.content.startsWith('```') ? (
                    <CodeBlock
                      code={message.content.replace(/```\w*\n?|\n?```/g, '')}
                      language="plaintext"
                      showLineNumbers
                    />
                  ) : (
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  )}

                  {/* Message Footer */}
                  <div className="mt-1 flex items-center justify-end gap-2 text-xs opacity-70">
                    <span>
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => copyToClipboard(message.content)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Error State */}
                  {message.status === 'error' && (
                    <div className="mt-2 text-sm text-destructive">
                      <p>{message.error}</p>
                      {onRetry && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onRetry(message.id)}
                          className="mt-1"
                        >
                          Retry
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Assistant is typing...</span>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0"
            onClick={() => {
              addToast({
                title: 'Available Commands',
                description: 'Type / to see available commands',
                variant: 'info',
              });
            }}
          >
            <Command className="h-5 w-5" />
          </Button>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
            disabled={isLoading}
            className="min-h-[40px]"
          />
          <Button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="shrink-0"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
} 