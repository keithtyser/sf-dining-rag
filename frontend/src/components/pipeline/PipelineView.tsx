import React from 'react';
import { useAtom } from 'jotai';
import { cn } from '@/lib/utils';
import { pipelineStatusAtom } from '@/lib/atoms';
import { DataSourceVisualizer } from './DataSourceVisualizer';
import { TextChunkVisualizer } from './TextChunkVisualizer';
import { EmbeddingVisualizer } from './EmbeddingVisualizer';
import { IndexingVisualizer } from './IndexingVisualizer';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Progress } from '../ui/Progress';

interface PipelineViewProps {
  className?: string;
}

export function PipelineView({ className }: PipelineViewProps) {
  const [pipelineStatus] = useAtom(pipelineStatusAtom);

  // Helper function to determine if a stage is active
  const isStageActive = (stage: typeof pipelineStatus.stage) => {
    return pipelineStatus.stage === stage;
  };

  // Helper function to determine if a stage is complete
  const isStageComplete = (stage: typeof pipelineStatus.stage) => {
    const stages = ['idle', 'loading', 'scraping', 'preprocessing', 'chunking', 'embedding'];
    const currentIndex = stages.indexOf(pipelineStatus.stage);
    const stageIndex = stages.indexOf(stage);
    return stageIndex < currentIndex;
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overall Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Overall Progress</span>
              <span className="font-medium">{pipelineStatus.progress}%</span>
            </div>
            <Progress value={pipelineStatus.progress} />
            {pipelineStatus.error && (
              <p className="mt-2 text-sm text-destructive">{pipelineStatus.error}</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Data Source Stage */}
      <Card
        className={cn(
          'transition-colors',
          isStageActive('loading') && 'border-primary',
          isStageComplete('loading') && 'border-green-500'
        )}
      >
        <CardHeader>
          <CardTitle>Data Ingestion</CardTitle>
        </CardHeader>
        <CardContent>
          <DataSourceVisualizer
            stages={[
              {
                stage: 'loading',
                progress: isStageActive('loading') ? pipelineStatus.progress : isStageComplete('loading') ? 100 : 0,
                status: isStageActive('loading') ? 'processing' : isStageComplete('loading') ? 'complete' : 'pending',
              },
              {
                stage: 'scraping',
                progress: isStageActive('scraping') ? pipelineStatus.progress : isStageComplete('scraping') ? 100 : 0,
                status: isStageActive('scraping') ? 'processing' : isStageComplete('scraping') ? 'complete' : 'pending',
              },
              {
                stage: 'preprocessing',
                progress: isStageActive('preprocessing') ? pipelineStatus.progress : isStageComplete('preprocessing') ? 100 : 0,
                status: isStageActive('preprocessing') ? 'processing' : isStageComplete('preprocessing') ? 'complete' : 'pending',
              },
            ]}
          />
        </CardContent>
      </Card>

      {/* Text Chunking Stage */}
      <Card
        className={cn(
          'transition-colors',
          isStageActive('chunking') && 'border-primary',
          isStageComplete('chunking') && 'border-green-500'
        )}
      >
        <CardHeader>
          <CardTitle>Text Chunking</CardTitle>
        </CardHeader>
        <CardContent>
          <TextChunkVisualizer
            chunks={[]} // TODO: Get chunks from state
          />
        </CardContent>
      </Card>

      {/* Embedding Stage */}
      <Card
        className={cn(
          'transition-colors',
          isStageActive('embedding') && 'border-primary',
          isStageComplete('embedding') && 'border-green-500'
        )}
      >
        <CardHeader>
          <CardTitle>Embedding Generation</CardTitle>
        </CardHeader>
        <CardContent>
          <EmbeddingVisualizer
            batches={[]} // TODO: Get batches from state
          />
        </CardContent>
      </Card>

      {/* Indexing Stage */}
      <Card
        className={cn(
          'transition-colors',
          isStageActive('embedding') && 'border-primary',
          isStageComplete('embedding') && 'border-green-500'
        )}
      >
        <CardHeader>
          <CardTitle>Vector Indexing</CardTitle>
        </CardHeader>
        <CardContent>
          <IndexingVisualizer
            operations={[]} // TODO: Get operations from state
          />
        </CardContent>
      </Card>
    </div>
  );
} 