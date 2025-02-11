import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { TextChunkVisualizer } from '../pipeline/TextChunkVisualizer';
import { Button } from '../ui/Button';
import { Slider } from '../ui/Slider';
import { Filter, History, X, Search, Sparkles, Brain, ChevronRight } from 'lucide-react';
import { ScrollArea } from '../ui/scroll-area';
import { Badge } from '../ui/Badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";

// Import the TextChunk type from TextChunkVisualizer
import type { TextChunk } from '../pipeline/TextChunkVisualizer';

interface ContextChunk extends Omit<TextChunk, 'metadata'> {
  metadata: TextChunk['metadata'] & {
    similarity: number;
    url?: string;
    source_type: 'restaurant' | 'news' | 'wikipedia' | string;
  };
}

interface ChunksData {
  restaurant: ContextChunk[];
  wikipedia: ContextChunk[];
  news: ContextChunk[];
}

interface ContextPanelProps {
  className?: string;
  chunks: ChunksData;
  onChunkClick?: (chunk: ContextChunk) => void;
  onChunkRemove?: (chunkId: string) => void;
  onClearContext?: () => void;
  contextHistory?: {
    query: string;
    chunks: ChunksData;
    timestamp: number;
  }[];
  onHistorySelect?: (chunks: ChunksData) => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function ContextPanel({
  className,
  chunks,
  onChunkClick,
  onChunkRemove,
  onClearContext,
  contextHistory = [],
  onHistorySelect,
  isCollapsed = false,
  onToggleCollapse,
}: ContextPanelProps) {
  const [showHistory, setShowHistory] = useState(false);
  const [minSimilarity, setMinSimilarity] = useState(0);
  const [sourceFilter, setSourceFilter] = useState<'all' | 'restaurant' | 'wikipedia' | 'news'>('all');

  // Combine all chunks into a single array for filtering
  const allChunks = [
    ...chunks.restaurant,
    ...chunks.wikipedia,
    ...chunks.news
  ];

  // Filter chunks based on similarity score and source
  const filteredChunks = allChunks.filter(
    (chunk) =>
      chunk.metadata.similarity >= minSimilarity &&
      (sourceFilter === 'all' || chunk.metadata.source_type === sourceFilter)
  );

  // Map ContextChunk to TextChunk for the visualizer
  const visualizerChunks: TextChunk[] = filteredChunks.map(chunk => {
    // Ensure source_type is one of the valid types
    let source: 'restaurant' | 'wikipedia' | 'news' = 'restaurant';
    if (chunk.metadata.source_type === 'wikipedia') source = 'wikipedia';
    if (chunk.metadata.source_type === 'news') source = 'news';

    return {
      ...chunk,
      metadata: {
        ...chunk.metadata,
        similarity: chunk.metadata.similarity,
        source // Use the validated source type
      },
    };
  });

  // Get total chunks count
  const totalChunks = allChunks.length;

  return (
    <Card className={cn(
      'flex flex-col overflow-hidden sf-card relative transition-all duration-300',
      isCollapsed ? 'w-[52px] p-0' : '',
      className
    )}>
      {isCollapsed ? (
        // Simplified Collapsed View with full clickable area
        <button 
          onClick={onToggleCollapse}
          className={cn(
            "w-full h-full min-h-full cursor-pointer",
            "flex flex-col items-center justify-center",
            "bg-background",
            "transition-all duration-300",
            "hover:bg-muted/10",
            "border-l border-border/40",
            "group",
            "p-0 m-0"
          )}
        >
          {/* Centered Text and Line Container */}
          <div className="flex flex-col items-center justify-center h-full pointer-events-none">
            <span 
              className={cn(
                "text-[10px] font-bold tracking-[0.2em] text-muted-foreground/70",
                "rotate-90 whitespace-nowrap",
                "transition-all duration-300 group-hover:text-muted-foreground",
                "mb-16"
              )}
            >
              RETRIEVED CONTEXT
            </span>
            <div className={cn(
              "w-[1px] h-32",
              "bg-border/40",
              "group-hover:bg-border/60",
              "transition-all duration-300",
              "mt-4"
            )} />
          </div>
        </button>
      ) : (
        <>
          {/* Header */}
          <div className="sf-glass border-b p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-[hsl(var(--sf-golden-gate))]" />
                <h3 className="sf-heading font-semibold">Retrieved Context</h3>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onToggleCollapse}
                  className="hover:bg-[hsl(var(--sf-golden-gate))]/10 transition-colors duration-200"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="sf-glass border-b p-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="text-sm font-medium text-muted-foreground">Relevance Filter</label>
                <Slider
                  min={0}
                  max={1}
                  step={0.01}
                  value={[minSimilarity]}
                  onValueChange={([value]) => setMinSimilarity(value)}
                  className="mt-2"
                />
                <div className="mt-1 text-xs text-[hsl(var(--sf-golden-gate))] font-medium">
                  {(minSimilarity * 100).toFixed(0)}% match or higher
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Source</label>
                <select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value as any)}
                  className={cn(
                    "mt-1 w-full rounded-md border bg-background px-2 py-1.5",
                    "text-sm sf-input transition-colors duration-200",
                    "focus:border-[hsl(var(--sf-golden-gate))] focus:ring-1 focus:ring-[hsl(var(--sf-golden-gate))]"
                  )}
                >
                  <option value="all">All Sources</option>
                  <option value="restaurant">Restaurants</option>
                  <option value="wikipedia">Wikipedia</option>
                  <option value="news">News</option>
                </select>
              </div>
            </div>
          </div>

          {/* Content */}
          <ScrollArea className="flex-1">
            <div className="p-4">
              {showHistory ? (
                // Context History
                <div className="space-y-4">
                  {contextHistory.map((item, index) => (
                    <Card
                      key={index}
                      className="cursor-pointer p-4 hover:bg-[hsl(var(--sf-golden-gate))]/5 sf-hover-lift"
                      onClick={() => onHistorySelect?.(item.chunks)}
                    >
                      <div className="mb-2 flex items-center justify-between">
                        <div className="sf-heading">{item.query}</div>
                        <div className="text-sm text-muted-foreground">
                          {new Date(item.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {Object.values(item.chunks).flat().length} context chunks
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                // Current Context
                <div className="space-y-4">
                  {filteredChunks.length > 0 ? (
                    <TextChunkVisualizer
                      chunks={visualizerChunks}
                      onChunkClick={(chunk) => onChunkClick?.(chunk as ContextChunk)}
                    />
                  ) : allChunks.length > 0 ? (
                    <div className="text-center text-sm text-muted-foreground">
                      No chunks match the current filters
                    </div>
                  ) : (
                    <div className="text-center text-sm text-muted-foreground">
                      No context available
                    </div>
                  )}
                </div>
              )}
            </div>
          </ScrollArea>
        </>
      )}
    </Card>
  );
} 