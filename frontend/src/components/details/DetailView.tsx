import React from 'react';
import { useAtom } from 'jotai';
import { cn } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { PipelineView } from '../pipeline/PipelineView';
import { MetricsDashboard } from '../metrics/MetricsDashboard';
import { SystemStatus } from '../metrics/SystemStatus';
import { StateDebugger } from '../debug/StateDebugger';
import { Download, Filter, Search } from 'lucide-react';

interface DetailViewProps {
  className?: string;
}

export function DetailView({ className }: DetailViewProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight">Technical Details</h2>
          <p className="text-sm text-muted-foreground">
            Comprehensive view of pipeline status, metrics, and system health
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex w-full max-w-sm items-center gap-2">
            <Input
              type="search"
              placeholder="Search logs and events..."
              className="h-8 w-[150px] lg:w-[250px]"
            />
            <Button variant="outline" size="sm" className="h-8 w-8 px-0">
              <Filter className="h-4 w-4" />
            </Button>
          </div>
          <Button variant="outline" size="sm" className="h-8">
            <Download className="mr-2 h-4 w-4" />
            Export Data
          </Button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
        {/* System Status Card */}
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <SystemStatus />
          </CardContent>
        </Card>

        {/* Debug Panel */}
        <Card>
          <CardHeader>
            <CardTitle>Debug Tools</CardTitle>
          </CardHeader>
          <CardContent>
            <StateDebugger className="border-none shadow-none" />
          </CardContent>
        </Card>

        {/* Pipeline Status */}
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Pipeline Status</CardTitle>
          </CardHeader>
          <CardContent>
            <PipelineView />
          </CardContent>
        </Card>

        {/* Performance Metrics */}
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <MetricsDashboard />
          </CardContent>
        </Card>

        {/* System Logs */}
        <Card className="xl:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>System Logs</CardTitle>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm">
                Clear
              </Button>
              <Button variant="ghost" size="sm">
                Download
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] space-y-1 overflow-auto rounded-md bg-muted p-4 font-mono text-sm">
              <div className="text-muted-foreground">No logs available</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 