"use client";

import React, { useState } from 'react';
import { useAtom } from 'jotai';
import { cn } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Search, ThumbsUp, ThumbsDown, Filter, SlidersHorizontal } from 'lucide-react';
import { CodeBlock } from '../ui/CodeBlock';
import { Progress } from '../ui/Progress';

interface SearchResult {
  id: string;
  text: string;
  score: number;
  source: 'menu' | 'wikipedia';
  metadata: {
    title: string;
    category?: string;
    restaurant?: string;
    timestamp: number;
  };
}

interface SearchInterfaceProps {
  className?: string;
  onSearch?: (query: string) => Promise<void>;
  onFeedback?: (resultId: string, isRelevant: boolean) => Promise<void>;
}

export function SearchInterface({
  className,
  onSearch,
  onFeedback,
}: SearchInterfaceProps) {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [feedbackStates, setFeedbackStates] = useState<Record<string, boolean | undefined>>({});

  const handleSearch = async () => {
    if (!query.trim() || !onSearch) return;

    setIsSearching(true);
    try {
      await onSearch(query);
      // In a real implementation, we would update results here based on the response
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleFeedback = async (resultId: string, isRelevant: boolean) => {
    if (!onFeedback) return;

    try {
      await onFeedback(resultId, isRelevant);
      setFeedbackStates(prev => ({
        ...prev,
        [resultId]: isRelevant,
      }));
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Search Bar */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Input
            placeholder="Enter your search query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full pl-10"
          />
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon">
            <SlidersHorizontal className="h-4 w-4" />
          </Button>
          <Button
            onClick={handleSearch}
            disabled={isSearching || !query.trim()}
          >
            {isSearching ? (
              <>
                <Progress value={undefined} className="w-4 h-4 mr-2" />
                Searching
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Search
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Results Area */}
      <div className="rounded-lg border bg-card p-6">
        <div className="text-center text-muted-foreground">
          Enter a search query to see results
        </div>
      </div>
    </div>
  );
} 