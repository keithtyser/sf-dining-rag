import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { CodeBlock } from '../ui/CodeBlock';
import { Info } from 'lucide-react';

interface TextChunk {
  id: string;
  text: string;
  tokens: number;
  metadata: {
    source: 'menu' | 'wikipedia';
    title: string;
    position: number;
    similarity?: number;
  };
}

interface TextChunkVisualizerProps {
  className?: string;
  chunks: TextChunk[];
  highlightedChunkId?: string;
  onChunkClick?: (chunk: TextChunk) => void;
}

export function TextChunkVisualizer({
  className,
  chunks,
  highlightedChunkId,
  onChunkClick,
}: TextChunkVisualizerProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {chunks.map(chunk => (
        <Card
          key={chunk.id}
          className={cn(
            'transition-colors cursor-pointer hover:border-primary/50',
            highlightedChunkId === chunk.id && 'border-primary bg-primary/5'
          )}
          onClick={() => onChunkClick?.(chunk)}
        >
          <div className="border-b border-border p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className={cn(
                    'rounded-full px-2 py-1 text-xs font-medium',
                    chunk.metadata.source === 'menu'
                      ? 'bg-blue-500/10 text-blue-500'
                      : 'bg-amber-500/10 text-amber-500'
                  )}
                >
                  {chunk.metadata.source === 'menu' ? 'Menu Item' : 'Wikipedia'}
                </div>
                <div className="text-sm font-medium">{chunk.metadata.title}</div>
              </div>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Info className="h-4 w-4" />
                  <span>Chunk {chunk.metadata.position}</span>
                </div>
                <div>{chunk.tokens} tokens</div>
                {chunk.metadata.similarity !== undefined && (
                  <div
                    className={cn(
                      'font-medium',
                      chunk.metadata.similarity > 0.8
                        ? 'text-green-500'
                        : chunk.metadata.similarity > 0.5
                        ? 'text-amber-500'
                        : 'text-red-500'
                    )}
                  >
                    {(chunk.metadata.similarity * 100).toFixed(1)}% match
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="p-4">
            <CodeBlock
              code={chunk.text}
              language="markdown"
              variant="ghost"
              className="bg-transparent"
            />
          </div>
        </Card>
      ))}
    </div>
  );
} 