import React from 'react';
import { Card } from '../ui/Card';
import { Progress } from '../ui/Progress';
import { useRAGPipeline } from '@/hooks/useRAGPipeline';
import { cn } from '@/lib/utils';
import { Loader2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

interface RAGPipelineVisualizerProps {
  className?: string;
  websocketUrl: string;
}

export function RAGPipelineVisualizer({
  className,
  websocketUrl,
}: RAGPipelineVisualizerProps) {
  const { state, error } = useRAGPipeline(websocketUrl);

  const renderStatusIcon = (status: 'idle' | 'running' | 'complete' | 'error') => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
      case 'complete':
        return <CheckCircle2 className="h-4 w-4 text-success" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-destructive" />;
      default:
        return <AlertCircle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const renderStageProgress = (
    title: string,
    status: 'idle' | 'running' | 'complete' | 'error',
    progress: number,
    error?: string
  ) => (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {renderStatusIcon(status)}
          <span className="font-medium">{title}</span>
        </div>
        <span className="text-sm text-muted-foreground">{progress}%</span>
      </div>
      <Progress value={progress} />
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
    </div>
  );

  return (
    <Card className={cn('p-4 space-y-6', className)}>
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">RAG Pipeline Status</h3>

        {/* Retrieval Stage */}
        {renderStageProgress(
          'Retrieval',
          state.retrieval.status,
          state.retrieval.progress,
          state.retrieval.error
        )}

        {/* Preprocessing Stage */}
        <div className="space-y-2">
          {renderStageProgress(
            'Preprocessing',
            state.preprocessing.status,
            state.preprocessing.progress,
            state.preprocessing.error
          )}
          {state.preprocessing.status !== 'idle' && (
            <div className="ml-6 space-y-1">
              {state.preprocessing.steps.map((step, index) => (
                <div key={index} className="flex items-center gap-2">
                  {renderStatusIcon(step.status === 'pending' ? 'idle' : step.status)}
                  <span className="text-sm">{step.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Generation Stage */}
        {renderStageProgress(
          'Generation',
          state.generation.status,
          state.generation.progress,
          state.generation.error
        )}

        {/* Token Usage */}
        {state.tokenUsage.total > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium">Token Usage</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>Prompt Tokens:</div>
              <div className="text-right">{state.tokenUsage.prompt}</div>
              <div>Completion Tokens:</div>
              <div className="text-right">{state.tokenUsage.completion}</div>
              <div>Total Tokens:</div>
              <div className="text-right">{state.tokenUsage.total}</div>
              <div>Estimated Cost:</div>
              <div className="text-right">${state.tokenUsage.cost.toFixed(4)}</div>
            </div>
          </div>
        )}

        {/* Performance Metrics */}
        {state.performance.totalTime > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium">Performance</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>Retrieval Time:</div>
              <div className="text-right">{state.performance.retrievalTime}ms</div>
              <div>Preprocessing Time:</div>
              <div className="text-right">{state.performance.preprocessingTime}ms</div>
              <div>Generation Time:</div>
              <div className="text-right">{state.performance.generationTime}ms</div>
              <div>Total Time:</div>
              <div className="text-right">{state.performance.totalTime}ms</div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}
      </div>
    </Card>
  );
} 