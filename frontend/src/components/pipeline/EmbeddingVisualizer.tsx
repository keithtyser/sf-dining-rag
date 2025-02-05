import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { Progress } from '../ui/Progress';
import { CodeBlock } from '../ui/CodeBlock';
import { ArrowRight, Binary, Cpu, Server } from 'lucide-react';

interface EmbeddingBatch {
  id: string;
  text: string;
  tokens: number;
  embedding?: number[];
  status: 'pending' | 'processing' | 'complete' | 'error';
  error?: string;
  apiLatency?: number;
}

interface EmbeddingVisualizerProps {
  className?: string;
  batches: EmbeddingBatch[];
  modelName?: string;
  dimensions?: number;
  batchSize?: number;
  apiEndpoint?: string;
}

export function EmbeddingVisualizer({
  className,
  batches,
  modelName = 'text-embedding-3-small',
  dimensions = 1536,
  batchSize = 8,
  apiEndpoint = 'api/embeddings',
}: EmbeddingVisualizerProps) {
  // Calculate overall progress
  const completedBatches = batches.filter(b => b.status === 'complete').length;
  const totalProgress = (completedBatches / batches.length) * 100;

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overview Card */}
      <Card className="p-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="text-sm text-muted-foreground">Model</div>
            <div className="font-medium">{modelName}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Dimensions</div>
            <div className="font-medium">{dimensions}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Batch Size</div>
            <div className="font-medium">{batchSize}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">API Endpoint</div>
            <div className="font-medium truncate">{apiEndpoint}</div>
          </div>
        </div>
      </Card>

      {/* Overall Progress */}
      <Card className="p-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Overall Progress</span>
            <span className="font-medium">{Math.round(totalProgress)}%</span>
          </div>
          <Progress value={totalProgress} />
          <div className="text-xs text-muted-foreground">
            {completedBatches} of {batches.length} batches completed
          </div>
        </div>
      </Card>

      {/* Batch Processing */}
      <div className="space-y-4">
        {batches.map(batch => (
          <Card key={batch.id} className="overflow-hidden">
            <div className="border-b border-border p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className={cn(
                      'rounded-full p-2',
                      batch.status === 'complete' && 'bg-green-500/10 text-green-500',
                      batch.status === 'processing' && 'bg-primary/10 text-primary animate-pulse',
                      batch.status === 'error' && 'bg-destructive/10 text-destructive',
                      batch.status === 'pending' && 'bg-muted text-muted-foreground'
                    )}
                  >
                    {batch.status === 'processing' ? (
                      <Cpu className="h-4 w-4" />
                    ) : batch.status === 'complete' ? (
                      <Binary className="h-4 w-4" />
                    ) : batch.status === 'error' ? (
                      <Server className="h-4 w-4" />
                    ) : (
                      <ArrowRight className="h-4 w-4" />
                    )}
                  </div>
                  <div className="text-sm font-medium">Batch {batch.id}</div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div className="text-muted-foreground">{batch.tokens} tokens</div>
                  {batch.apiLatency && (
                    <div className="text-muted-foreground">
                      {batch.apiLatency.toFixed(2)}ms
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="grid gap-4 p-4 lg:grid-cols-2">
              {/* Input Text */}
              <div>
                <div className="mb-2 text-sm font-medium">Input Text</div>
                <CodeBlock
                  code={batch.text}
                  language="markdown"
                  variant="ghost"
                  className="max-h-48 overflow-auto bg-transparent"
                />
              </div>
              {/* Output Embedding */}
              <div>
                <div className="mb-2 text-sm font-medium">Embedding Vector</div>
                {batch.embedding ? (
                  <CodeBlock
                    code={`// ${dimensions} dimensions\n[${batch.embedding
                      .slice(0, 8)
                      .map(n => n.toFixed(4))
                      .join(', ')}, ...]`}
                    language="javascript"
                    variant="ghost"
                    className="bg-transparent"
                  />
                ) : batch.error ? (
                  <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                    {batch.error}
                  </div>
                ) : (
                  <div className="flex h-24 items-center justify-center rounded-md border border-dashed text-sm text-muted-foreground">
                    {batch.status === 'processing'
                      ? 'Generating embedding...'
                      : 'Waiting to process...'}
                  </div>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
} 