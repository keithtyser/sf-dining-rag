import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
  content: string;
  isUser: boolean;
  isLoading?: boolean;
  className?: string;
}

export function ChatMessage({ content, isUser, isLoading, className }: ChatMessageProps) {
  return (
    <div
      className={cn(
        'sf-message max-w-[85%]',
        isUser ? 'sf-message-user ml-auto' : 'mr-auto',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className="min-w-[24px] h-6 flex items-center justify-center">
          <span className={cn(
            'sf-icon text-lg transform transition-transform duration-300',
            isUser ? 'hover:rotate-12' : 'animate-bridge'
          )}>
            {isUser ? '👤' : '🌉'}
          </span>
        </div>
        <div className="flex-1 space-y-2">
          <div className={cn(
            'text-sm font-medium',
            isUser ? 'text-muted-foreground' : 'sf-heading'
          )}>
            {isUser ? 'You' : 'SF Dining Guide'}
          </div>
          {isLoading ? (
            <div className="flex items-center gap-2 text-muted-foreground animate-pulse">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Exploring SF restaurants...</span>
            </div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                className="[&>p]:my-3 [&>ul]:my-3 [&>ol]:my-3 [&>pre]:my-3"
                components={{
                  p: ({ children }) => <p className="my-3 leading-relaxed">{children}</p>,
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      className="text-[hsl(var(--sf-golden-gate))] hover:text-[hsl(var(--sf-sunset))] 
                               underline decoration-[hsl(var(--sf-golden-gate))]/30 
                               hover:decoration-[hsl(var(--sf-sunset))] transition-colors duration-300"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {children}
                    </a>
                  ),
                  code: ({ children }) => (
                    <code className="bg-muted px-1.5 py-0.5 rounded-md font-mono text-sm">
                      {children}
                    </code>
                  ),
                  pre: ({ children }) => (
                    <pre className="bg-muted p-4 rounded-md font-mono text-sm overflow-auto">
                      {children}
                    </pre>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc pl-4 my-3 space-y-1">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal pl-4 my-3 space-y-1">{children}</ol>
                  ),
                  li: ({ children }) => (
                    <li className="my-1 marker:text-[hsl(var(--sf-golden-gate))]">{children}</li>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-bold text-[hsl(var(--sf-golden-gate))]">{children}</strong>
                  ),
                  em: ({ children }) => (
                    <em className="italic text-[hsl(var(--sf-bay-blue))]">{children}</em>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-[hsl(var(--sf-golden-gate))]/30 
                                         pl-4 italic text-muted-foreground">
                      {children}
                    </blockquote>
                  ),
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 