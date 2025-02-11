import React from 'react';
import { cn } from '@/lib/utils';
import { CodeBlock } from '../ui/CodeBlock';
import { Button } from '../ui/Button';
import { ThumbsUp, ThumbsDown, RefreshCw, Clock, AlertCircle, Copy, CheckCircle2 } from 'lucide-react';
import { format } from 'date-fns';

interface MessageContent {
  type: 'text' | 'code' | 'image';
  content: string;
  language?: string; // For code blocks
  altText?: string; // For images
}

interface MessageBubbleProps {
  className?: string;
  role: 'user' | 'assistant' | 'system';
  content: MessageContent | MessageContent[];
  timestamp: number;
  status?: 'sending' | 'sent' | 'error';
  error?: string;
  onRetry?: () => Promise<void>;
  onFeedback?: (isPositive: boolean) => Promise<void>;
  onCopy?: (content: string) => Promise<void>;
}

export function MessageBubble({
  className,
  role,
  content,
  timestamp,
  status = 'sent',
  error,
  onRetry,
  onFeedback,
  onCopy,
}: MessageBubbleProps) {
  const [copied, setCopied] = React.useState(false);
  const [feedback, setFeedback] = React.useState<'positive' | 'negative' | null>(null);
  const [isRetrying, setIsRetrying] = React.useState(false);

  const handleCopy = async (text: string) => {
    try {
      await onCopy?.(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleRetry = async () => {
    if (isRetrying) return;
    try {
      setIsRetrying(true);
      await onRetry?.();
    } catch (error) {
      console.error('Retry failed:', error);
    } finally {
      setIsRetrying(false);
    }
  };

  const handleFeedback = async (isPositive: boolean) => {
    try {
      await onFeedback?.(isPositive);
      setFeedback(isPositive ? 'positive' : 'negative');
    } catch (error) {
      console.error('Failed to send feedback:', error);
    }
  };

  const renderContent = (content: MessageContent) => {
    switch (content.type) {
      case 'code':
        return (
          <div className="relative">
            {content.content && (
              <CodeBlock
                code={content.content}
                language={content.language || 'plaintext'}
                className="my-2"
              />
            )}
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-2 top-2"
              onClick={() => handleCopy(content.content)}
            >
              {copied ? <CheckCircle2 className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
        );
      case 'image':
        return (
          <img
            src={content.content}
            alt={content.altText || 'Message image'}
            className="my-2 rounded-md max-w-full h-auto"
          />
        );
      default:
        return <p className="whitespace-pre-wrap">{content.content}</p>;
    }
  };

  return (
    <div
      className={cn(
        'flex gap-2',
        role === 'assistant' ? 'flex-row' : 'flex-row-reverse',
        className
      )}
    >
      <div
        className={cn(
          'relative max-w-[80%] rounded-lg px-4 py-2',
          role === 'assistant'
            ? 'bg-primary text-primary-foreground'
            : role === 'user'
            ? 'bg-secondary text-secondary-foreground'
            : 'bg-muted text-muted-foreground',
          status === 'error' && 'border-2 border-destructive'
        )}
      >
        {/* Content */}
        <div className="space-y-2">
          {Array.isArray(content)
            ? content.map((item, index) => (
                <div key={index}>{renderContent(item)}</div>
              ))
            : renderContent(content)}
        </div>

        {/* Footer */}
        <div className="mt-2 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            {status === 'sending' && (
              <span className="flex items-center gap-1 text-muted-foreground">
                <Clock className="h-3 w-3" />
                Sending...
              </span>
            )}
            {status === 'error' && (
              <span className="flex items-center gap-1 text-destructive">
                <AlertCircle className="h-3 w-3" />
                {error || 'Failed to send'}
              </span>
            )}
            <time className="text-muted-foreground">
              {format(timestamp, 'HH:mm')}
            </time>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {status === 'error' && onRetry && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2"
                onClick={handleRetry}
                disabled={isRetrying}
              >
                <RefreshCw className={cn('h-3 w-3', isRetrying && 'animate-spin')} />
              </Button>
            )}
            {role === 'assistant' && onFeedback && (
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    'h-6 px-2',
                    feedback === 'positive' && 'text-success'
                  )}
                  onClick={() => handleFeedback(true)}
                  disabled={feedback !== null}
                >
                  <ThumbsUp className="h-3 w-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    'h-6 px-2',
                    feedback === 'negative' && 'text-destructive'
                  )}
                  onClick={() => handleFeedback(false)}
                  disabled={feedback !== null}
                >
                  <ThumbsDown className="h-3 w-3" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 