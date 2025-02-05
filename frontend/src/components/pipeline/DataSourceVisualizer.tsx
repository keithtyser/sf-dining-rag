import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { Progress } from '../ui/Progress';
import { Database, Globe, SplitSquareHorizontal, Braces, Binary } from 'lucide-react';

interface ProcessingStats {
  menuItems: number;
  wikiArticles: number;
  totalChunks: number;
  averageChunkSize: number;
  embeddingDimensions: number;
}

interface StageProgress {
  stage: 'loading' | 'scraping' | 'preprocessing' | 'chunking' | 'embedding';
  progress: number;
  status: 'pending' | 'processing' | 'complete' | 'error';
  details?: string;
}

interface DataSourceVisualizerProps {
  className?: string;
  stats?: ProcessingStats;
  stages: StageProgress[];
}

const stageIcons = {
  loading: Database,
  scraping: Globe,
  preprocessing: Braces,
  chunking: SplitSquareHorizontal,
  embedding: Binary,
};

const stageDescriptions = {
  loading: 'Loading restaurant menu data from CSV',
  scraping: 'Scraping Wikipedia articles for context',
  preprocessing: 'Cleaning and preprocessing text',
  chunking: 'Splitting content into chunks',
  embedding: 'Generating embeddings',
};

export function DataSourceVisualizer({
  className,
  stats,
  stages,
}: DataSourceVisualizerProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* Pipeline Stages */}
      <div className="grid gap-4">
        {stages.map(({ stage, progress, status, details }) => {
          const Icon = stageIcons[stage];
          return (
            <Card key={stage} className="p-4">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      'rounded-full p-2',
                      status === 'complete' && 'bg-green-500/10 text-green-500',
                      status === 'processing' && 'bg-primary/10 text-primary animate-pulse',
                      status === 'error' && 'bg-destructive/10 text-destructive',
                      status === 'pending' && 'bg-muted text-muted-foreground'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-medium">{stageDescriptions[stage]}</div>
                      <div className="text-sm text-muted-foreground">{progress}%</div>
                    </div>
                    <Progress value={progress} />
                    {details && (
                      <div className="text-xs text-muted-foreground">{details}</div>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Processing Stats */}
      {stats && (
        <Card className="p-4">
          <h3 className="mb-4 text-sm font-medium">Processing Statistics</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">Menu Items</div>
              <div className="font-medium">{stats.menuItems}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Wikipedia Articles</div>
              <div className="font-medium">{stats.wikiArticles}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Total Chunks</div>
              <div className="font-medium">{stats.totalChunks}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Avg. Chunk Size</div>
              <div className="font-medium">{stats.averageChunkSize} tokens</div>
            </div>
            <div className="col-span-2">
              <div className="text-muted-foreground">Embedding Dimensions</div>
              <div className="font-medium">{stats.embeddingDimensions}</div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
} 