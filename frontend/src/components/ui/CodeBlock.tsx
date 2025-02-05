import React, { useEffect, useState } from 'react';
import { getHighlighter, Highlighter } from 'shiki';
import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';

const codeBlockVariants = cva(
  'relative w-full font-mono text-sm overflow-x-auto rounded-lg border',
  {
    variants: {
      variant: {
        default: 'bg-muted/50 border-border',
        ghost: 'border-transparent bg-transparent',
      },
      size: {
        default: 'p-4',
        sm: 'p-2 text-xs',
        lg: 'p-6',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface CodeBlockProps
  extends React.HTMLAttributes<HTMLPreElement>,
    VariantProps<typeof codeBlockVariants> {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
  highlightLines?: number[];
  caption?: string;
}

export const CodeBlock = React.forwardRef<HTMLPreElement, CodeBlockProps>(
  (
    {
      className,
      variant,
      size,
      code,
      language = 'typescript',
      showLineNumbers = false,
      highlightLines = [],
      caption,
      ...props
    },
    ref
  ) => {
    const [highlighter, setHighlighter] = useState<Highlighter | null>(null);
    const [highlighted, setHighlighted] = useState<string>('');

    useEffect(() => {
      const initHighlighter = async () => {
        const highlighter = await getHighlighter({
          themes: ['github-dark'],
          langs: [language],
        });
        setHighlighter(highlighter);
      };

      initHighlighter();
    }, [language]);

    useEffect(() => {
      if (highlighter) {
        const html = highlighter.codeToHtml(code, {
          lang: language,
          theme: 'github-dark',
        });
        setHighlighted(html);
      }
    }, [highlighter, code, language]);

    return (
      <div className="group relative w-full">
        <pre
          ref={ref}
          className={cn(codeBlockVariants({ variant, size, className }))}
          {...props}
        >
          {highlighter ? (
            <div
              className="relative"
              dangerouslySetInnerHTML={{ __html: highlighted }}
            />
          ) : (
            <code className="block text-sm">{code}</code>
          )}
          {showLineNumbers && (
            <div
              aria-hidden="true"
              className="absolute left-0 top-0 h-full w-12 select-none border-r border-border bg-muted/50 px-2 text-right font-mono text-xs text-muted-foreground"
            >
              {code.split('\n').map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    'leading-6',
                    highlightLines.includes(i + 1) && 'bg-primary/10 text-primary'
                  )}
                >
                  {i + 1}
                </div>
              ))}
            </div>
          )}
        </pre>
        {caption && (
          <div className="mt-2 text-xs text-muted-foreground">{caption}</div>
        )}
      </div>
    );
  }
);

CodeBlock.displayName = 'CodeBlock'; 