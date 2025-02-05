import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { Progress } from '../ui/Progress';
import { CodeBlock } from '../ui/CodeBlock';
import {
  Database,
  HardDrive,
  BarChart,
  AlertCircle,
  Clock,
  Layers,
  Cpu,
  Network,
} from 'lucide-react';

interface IndexOperation {
  id: string;
  type: 'upsert' | 'delete' | 'update';
  status: 'pending' | 'processing' | 'complete' | 'error';
  vectors: {
    id: string;
    text: string;
    dimensions: number;
  }[];
  metadata?: {
    indexSize: number;
    totalVectors: number;
    avgIndexTime: number;
    memoryUsage?: number;
    cpuUsage?: number;
    diskUsage?: number;
  };
  performance?: {
    indexBuildTime: number;
    vectorInsertTime: number;
    optimizationTime: number;
    totalTime: number;
  };
  networkStats?: {
    bytesReceived: number;
    bytesSent: number;
    latency: number;
    connectionErrors: number;
  };
  error?: string;
  timestamp: number;
}

interface IndexingVisualizerProps {
  className?: string;
  operations: IndexOperation[];
  databaseName?: string;
  indexName?: string;
  dimensions?: number;
}

export function IndexingVisualizer({
  className,
  operations,
  databaseName = 'Qdrant',
  indexName = 'menu_items',
  dimensions = 1536,
}: IndexingVisualizerProps) {
  // Calculate overall progress
  const completedOps = operations.filter(op => op.status === 'complete').length;
  const totalProgress = (completedOps / operations.length) * 100;

  // Calculate total vectors across all operations
  const totalVectors = operations.reduce(
    (sum, op) => sum + (op.metadata?.totalVectors || 0),
    0
  );

  // Calculate average indexing time
  const avgIndexTime = operations.reduce(
    (sum, op) => sum + (op.metadata?.avgIndexTime || 0),
    0
  ) / completedOps || 0;

  // Calculate system metrics
  const systemMetrics = operations.reduce(
    (metrics, op) => ({
      memoryUsage: Math.max(metrics.memoryUsage, op.metadata?.memoryUsage || 0),
      cpuUsage: Math.max(metrics.cpuUsage, op.metadata?.cpuUsage || 0),
      diskUsage: Math.max(metrics.diskUsage, op.metadata?.diskUsage || 0),
    }),
    { memoryUsage: 0, cpuUsage: 0, diskUsage: 0 }
  );

  // Calculate network statistics
  const networkStats = operations.reduce(
    (stats, op) => ({
      totalReceived: stats.totalReceived + (op.networkStats?.bytesReceived || 0),
      totalSent: stats.totalSent + (op.networkStats?.bytesSent || 0),
      avgLatency:
        stats.avgLatency + (op.networkStats?.latency || 0) / operations.length,
      totalErrors: stats.totalErrors + (op.networkStats?.connectionErrors || 0),
    }),
    { totalReceived: 0, totalSent: 0, avgLatency: 0, totalErrors: 0 }
  );

  return (
    <div className={cn('space-y-6', className)}>
      {/* Database Info */}
      <Card className="p-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="text-sm text-muted-foreground">Database</div>
            <div className="font-medium">{databaseName}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Index</div>
            <div className="font-medium">{indexName}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Dimensions</div>
            <div className="font-medium">{dimensions}</div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Total Vectors</div>
            <div className="font-medium">{totalVectors.toLocaleString()}</div>
          </div>
        </div>
      </Card>

      {/* System Metrics */}
      <Card className="p-4">
        <h3 className="mb-4 text-sm font-medium">System Metrics</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Cpu className="h-4 w-4" />
              <span>CPU Usage</span>
            </div>
            <div className="font-medium">{systemMetrics.cpuUsage.toFixed(1)}%</div>
          </div>
          <div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Layers className="h-4 w-4" />
              <span>Memory Usage</span>
            </div>
            <div className="font-medium">
              {(systemMetrics.memoryUsage / 1024 / 1024 / 1024).toFixed(2)} GB
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <HardDrive className="h-4 w-4" />
              <span>Disk Usage</span>
            </div>
            <div className="font-medium">
              {(systemMetrics.diskUsage / 1024 / 1024 / 1024).toFixed(2)} GB
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>Avg Index Time</span>
            </div>
            <div className="font-medium">{avgIndexTime.toFixed(2)}ms</div>
          </div>
        </div>
      </Card>

      {/* Network Statistics */}
      <Card className="p-4">
        <h3 className="mb-4 text-sm font-medium">Network Statistics</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Network className="h-4 w-4" />
              <span>Data Received</span>
            </div>
            <div className="font-medium">
              {(networkStats.totalReceived / 1024 / 1024).toFixed(2)} MB
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Network className="h-4 w-4" />
              <span>Data Sent</span>
            </div>
            <div className="font-medium">
              {(networkStats.totalSent / 1024 / 1024).toFixed(2)} MB
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>Avg Latency</span>
            </div>
            <div className="font-medium">{networkStats.avgLatency.toFixed(2)}ms</div>
          </div>
          <div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <AlertCircle className="h-4 w-4" />
              <span>Connection Errors</span>
            </div>
            <div className="font-medium">{networkStats.totalErrors}</div>
          </div>
        </div>
      </Card>

      {/* Overall Progress */}
      <Card className="p-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Indexing Progress</span>
            <span className="font-medium">{Math.round(totalProgress)}%</span>
          </div>
          <Progress value={totalProgress} />
          <div className="text-xs text-muted-foreground">
            {completedOps} of {operations.length} operations completed
            {avgIndexTime > 0 && ` (avg. ${avgIndexTime.toFixed(2)}ms per vector)`}
          </div>
        </div>
      </Card>

      {/* Operations List */}
      <div className="space-y-4">
        {operations.map(operation => (
          <Card key={operation.id} className="overflow-hidden">
            <div className="border-b border-border p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className={cn(
                      'rounded-full p-2',
                      operation.status === 'complete' && 'bg-green-500/10 text-green-500',
                      operation.status === 'processing' && 'bg-primary/10 text-primary animate-pulse',
                      operation.status === 'error' && 'bg-destructive/10 text-destructive',
                      operation.status === 'pending' && 'bg-muted text-muted-foreground'
                    )}
                  >
                    {operation.status === 'processing' ? (
                      <Database className="h-4 w-4" />
                    ) : operation.status === 'complete' ? (
                      <HardDrive className="h-4 w-4" />
                    ) : operation.status === 'error' ? (
                      <AlertCircle className="h-4 w-4" />
                    ) : (
                      <BarChart className="h-4 w-4" />
                    )}
                  </div>
                  <div className="text-sm font-medium">
                    {operation.type.charAt(0).toUpperCase() + operation.type.slice(1)} Operation
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(operation.timestamp).toLocaleTimeString()}
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div className="text-muted-foreground">
                    {operation.vectors.length} vectors
                  </div>
                  {operation.metadata?.indexSize && (
                    <div className="text-muted-foreground">
                      {(operation.metadata.indexSize / 1024 / 1024).toFixed(2)} MB
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="p-4">
              {operation.error ? (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {operation.error}
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Sample Vectors */}
                  <div>
                    <div className="text-sm font-medium">Sample Vectors</div>
                    <CodeBlock
                      code={operation.vectors
                        .slice(0, 2)
                        .map(
                          v => `${v.id}: "${v.text.substring(0, 100)}${
                            v.text.length > 100 ? '...' : ''
                          }"`
                        )
                        .join('\n')}
                      language="javascript"
                      variant="ghost"
                      className="bg-transparent"
                    />
                  </div>

                  {/* Performance Metrics */}
                  {operation.performance && (
                    <div>
                      <div className="mb-2 text-sm font-medium">Performance Breakdown</div>
                      <div className="grid grid-cols-2 gap-4 rounded-md border p-4 text-sm lg:grid-cols-4">
                        <div>
                          <div className="text-muted-foreground">Index Build</div>
                          <div className="font-medium">
                            {operation.performance.indexBuildTime.toFixed(2)}ms
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Vector Insert</div>
                          <div className="font-medium">
                            {operation.performance.vectorInsertTime.toFixed(2)}ms
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Optimization</div>
                          <div className="font-medium">
                            {operation.performance.optimizationTime.toFixed(2)}ms
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Total Time</div>
                          <div className="font-medium">
                            {operation.performance.totalTime.toFixed(2)}ms
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* System Resource Usage */}
                  {operation.metadata && (
                    <div>
                      <div className="mb-2 text-sm font-medium">System Resources</div>
                      <div className="grid grid-cols-2 gap-4 rounded-md border p-4 text-sm lg:grid-cols-4">
                        <div>
                          <div className="text-muted-foreground">Index Size</div>
                          <div className="font-medium">
                            {(operation.metadata.indexSize / 1024 / 1024).toFixed(2)} MB
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Total Vectors</div>
                          <div className="font-medium">
                            {operation.metadata.totalVectors.toLocaleString()}
                          </div>
                        </div>
                        {operation.metadata.memoryUsage && (
                          <div>
                            <div className="text-muted-foreground">Memory Usage</div>
                            <div className="font-medium">
                              {(operation.metadata.memoryUsage / 1024 / 1024).toFixed(2)} MB
                            </div>
                          </div>
                        )}
                        {operation.metadata.cpuUsage && (
                          <div>
                            <div className="text-muted-foreground">CPU Usage</div>
                            <div className="font-medium">
                              {operation.metadata.cpuUsage.toFixed(1)}%
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Network Statistics */}
                  {operation.networkStats && (
                    <div>
                      <div className="mb-2 text-sm font-medium">Network Statistics</div>
                      <div className="grid grid-cols-2 gap-4 rounded-md border p-4 text-sm lg:grid-cols-4">
                        <div>
                          <div className="text-muted-foreground">Data Received</div>
                          <div className="font-medium">
                            {(operation.networkStats.bytesReceived / 1024).toFixed(2)} KB
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Data Sent</div>
                          <div className="font-medium">
                            {(operation.networkStats.bytesSent / 1024).toFixed(2)} KB
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Latency</div>
                          <div className="font-medium">
                            {operation.networkStats.latency.toFixed(2)}ms
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Connection Errors</div>
                          <div className="font-medium">
                            {operation.networkStats.connectionErrors}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

IndexingVisualizer.displayName = 'IndexingVisualizer'; 