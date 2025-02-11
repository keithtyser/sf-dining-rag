import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { Info, Bot, Star, Tag, MapPin, Hash, Clock, Utensils, List, Newspaper, Book } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { ScrollArea } from '../ui/scroll-area';

// Helper function to safely parse JSON strings
const safeJSONParse = (str: string | string[] | undefined | null): string[] => {
  if (Array.isArray(str)) return str;
  if (!str) return [];
  try {
    const parsed = JSON.parse(str);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export interface TextChunk {
  id: string;
  text: string;
  tokens: number;
  metadata: {
    source: 'restaurant' | 'wikipedia' | 'news';
    title: string;
    position: number;
    similarity?: number;
    restaurant?: string;
    category?: string;
    item_name?: string;
    description?: string;
    ingredients?: string | string[];
    categories?: string | string[];
    keywords?: string | string[];
    rating?: number;
    review_count?: number;
    price?: string;
    address?: string;
    tokens?: number;
    publish_date?: string;
    url?: string;
    restaurant_name?: string;
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
      {chunks.map((chunk, index) => {
        const uniqueKey = `${chunk.id}_${index}`;
        
        return (
          <Card
            key={uniqueKey}
            className={cn(
              'transition-colors hover:bg-[hsl(var(--sf-golden-gate))]/5',
              'cursor-pointer border border-border/50',
              highlightedChunkId === chunk.id && 'ring-1 ring-[hsl(var(--sf-golden-gate))]',
              'overflow-hidden sf-hover-lift'
            )}
            onClick={() => onChunkClick?.(chunk)}
          >
            <div className="p-4 space-y-3">
              {/* Source and Match Score */}
              <div className="flex items-center justify-between">
                <Badge variant="default" className={cn(
                  "flex items-center gap-1",
                  chunk.metadata.source === 'restaurant' && "bg-[hsl(var(--sf-golden-gate))]",
                  chunk.metadata.source === 'wikipedia' && "bg-blue-500",
                  chunk.metadata.source === 'news' && "bg-green-500"
                )}>
                  {chunk.metadata.source.toUpperCase()}
                </Badge>
                <div className="flex items-center gap-2">
                  <Badge variant={
                    (chunk.metadata.similarity ?? 0) > 0.8 ? 'success' :
                    (chunk.metadata.similarity ?? 0) > 0.5 ? 'warning' : 'destructive'
                  }>
                    {((chunk.metadata.similarity ?? 0) * 100).toFixed(0)}% match
                  </Badge>
                  <span className="text-xs text-muted-foreground">#{index + 1}</span>
                </div>
              </div>

              {/* Raw Chunk Data */}
              <div className="font-mono text-xs whitespace-pre-wrap break-words bg-muted/30 rounded-lg p-3 overflow-x-auto">
                <div className="font-semibold mb-2 break-all">ID: {chunk.id}</div>
                <div className="mb-2">
                  <span className="font-semibold">Metadata:</span>
                  {Object.entries(chunk.metadata).map(([key, value]) => {
                    if (!value) return null;
                    let displayValue = value;
                    if (typeof value === 'string' && value.trim() === '') return null;
                    if (Array.isArray(value) && value.length === 0) return null;
                    
                    // Format arrays and objects
                    if (typeof value === 'object' || Array.isArray(value)) {
                      displayValue = JSON.stringify(value, null, 2);
                    }
                    
                    return (
                      <div key={key} className="ml-2 break-all">
                        <span className="font-medium">{key}:</span>{' '}
                        <span className="break-words">{displayValue}</span>
                      </div>
                    );
                  })}
                </div>
                <div>
                  <span className="font-semibold">Text:</span>
                  <div className="ml-2 break-words">{chunk.text}</div>
                </div>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
} 