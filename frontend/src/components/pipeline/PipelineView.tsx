"use client";

import React from 'react';
import { useAtom } from 'jotai';
import { cn } from '@/lib/utils';
import { pipelineStatusAtom } from '@/lib/atoms';
import { Card } from '../ui/Card';
import { Progress } from '../ui/Progress';
import { Badge } from '@/components/ui/Badge';
import { Database, FileText, Network, Server } from 'lucide-react';

interface PipelineViewProps {
  className?: string;
}

interface PipelineStage {
  id: string;
  name: string;
  icon: React.ElementType;
  description: string;
  progress: number;
}

const stages: PipelineStage[] = [
  { 
    id: 'ingestion', 
    name: 'Data Ingestion', 
    icon: Database,
    description: 'Loading and preprocessing data from various sources',
    progress: 0
  },
  { 
    id: 'chunking', 
    name: 'Text Chunking', 
    icon: FileText,
    description: 'Splitting text into optimal chunks for processing',
    progress: 0
  },
  { 
    id: 'embedding', 
    name: 'Embedding Generation', 
    icon: Network,
    description: 'Converting text chunks into vector embeddings',
    progress: 0
  },
  { 
    id: 'indexing', 
    name: 'Vector Indexing', 
    icon: Server,
    description: 'Storing and indexing vectors for efficient retrieval',
    progress: 0
  },
];

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
    <div className={cn('space-y-4', className)}>
      {stages.map((stage) => (
        <Card key={stage.id} className="relative overflow-hidden">
          <div className="p-4">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-primary/10 p-2">
                <stage.icon className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{stage.name}</h3>
                  <Badge variant={stage.progress === 100 ? 'success' : 'secondary'}>
                    {stage.progress}%
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  {stage.description}
                </p>
                <Progress 
                  value={stage.progress} 
                  className={cn(
                    "h-2 mt-2",
                    stage.progress === 100 && "bg-green-500/20"
                  )}
                />
              </div>
            </div>
          </div>
          {stage.progress > 0 && stage.progress < 100 && (
            <div className="absolute inset-0 bg-primary/5 animate-pulse" />
          )}
        </Card>
      ))}
    </div>
  );
} 