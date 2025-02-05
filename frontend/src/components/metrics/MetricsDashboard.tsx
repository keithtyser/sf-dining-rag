import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { Progress } from '../ui/Progress';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import {
  Clock,
  Cpu,
  Database,
  HardDrive,
  Network,
  AlertCircle,
  Activity,
  Layers,
} from 'lucide-react';

interface MetricsData {
  timestamp: number;
  processingTime: number;
  memoryUsage: number;
  cpuUsage: number;
  apiLatency: number;
  queueSize: number;
  errorRate: number;
  throughput: number;
}

interface SystemStatus {
  healthy: boolean;
  message?: string;
  lastUpdate: number;
  services: {
    api: boolean;
    database: boolean;
    vectorStore: boolean;
    embedding: boolean;
  };
}

interface MetricsDashboardProps {
  className?: string;
  data: MetricsData[];
  systemStatus: SystemStatus;
  timeRange?: '1h' | '24h' | '7d' | '30d';
}

type MetricsAverages = {
  [K in keyof Omit<MetricsData, 'timestamp'>]: number;
};

export function MetricsDashboard({
  className,
  data,
  systemStatus,
  timeRange = '1h',
}: MetricsDashboardProps) {
  // Calculate current metrics from the latest data point
  const currentMetrics = data[data.length - 1] || {
    processingTime: 0,
    memoryUsage: 0,
    cpuUsage: 0,
    apiLatency: 0,
    queueSize: 0,
    errorRate: 0,
    throughput: 0,
  };

  // Calculate averages over the time range
  const averages = data.reduce<MetricsAverages>(
    (acc, curr) => ({
      processingTime: acc.processingTime + curr.processingTime,
      memoryUsage: acc.memoryUsage + curr.memoryUsage,
      cpuUsage: acc.cpuUsage + curr.cpuUsage,
      apiLatency: acc.apiLatency + curr.apiLatency,
      queueSize: acc.queueSize + curr.queueSize,
      errorRate: acc.errorRate + curr.errorRate,
      throughput: acc.throughput + curr.throughput,
    }),
    {
      processingTime: 0,
      memoryUsage: 0,
      cpuUsage: 0,
      apiLatency: 0,
      queueSize: 0,
      errorRate: 0,
      throughput: 0,
    }
  );

  Object.keys(averages).forEach(key => {
    averages[key as keyof MetricsAverages] /= data.length || 1;
  });

  return (
    <div className={cn('space-y-6', className)}>
      {/* System Status */}
      <Card className="p-4">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-medium">System Status</h3>
          <div
            className={cn(
              'flex items-center gap-2 rounded-full px-3 py-1 text-sm',
              systemStatus.healthy
                ? 'bg-green-500/10 text-green-500'
                : 'bg-destructive/10 text-destructive'
            )}
          >
            <Activity className="h-4 w-4" />
            <span>{systemStatus.healthy ? 'Healthy' : 'Issues Detected'}</span>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Object.entries(systemStatus.services).map(([service, status]) => (
            <div
              key={service}
              className={cn(
                'flex items-center gap-2 rounded-lg border p-3',
                status ? 'border-green-500/20' : 'border-destructive/20'
              )}
            >
              {service === 'api' ? (
                <Network className="h-4 w-4" />
              ) : service === 'database' ? (
                <Database className="h-4 w-4" />
              ) : service === 'vectorStore' ? (
                <HardDrive className="h-4 w-4" />
              ) : (
                <Cpu className="h-4 w-4" />
              )}
              <div>
                <div className="text-sm font-medium">
                  {service.charAt(0).toUpperCase() + service.slice(1)}
                </div>
                <div
                  className={cn(
                    'text-xs',
                    status ? 'text-green-500' : 'text-destructive'
                  )}
                >
                  {status ? 'Operational' : 'Down'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Current Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="p-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <div className="text-sm text-muted-foreground">Processing Time</div>
          </div>
          <div className="mt-2 flex items-end justify-between">
            <div className="text-2xl font-bold">
              {currentMetrics.processingTime.toFixed(2)}ms
            </div>
            <div
              className={cn(
                'text-sm',
                currentMetrics.processingTime < averages.processingTime
                  ? 'text-green-500'
                  : 'text-destructive'
              )}
            >
              {(
                ((currentMetrics.processingTime - averages.processingTime) /
                  averages.processingTime) *
                100
              ).toFixed(1)}
              %
            </div>
          </div>
          <Progress
            value={Math.min(
              (currentMetrics.processingTime / (averages.processingTime * 2)) * 100,
              100
            )}
            className="mt-2"
          />
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-muted-foreground" />
            <div className="text-sm text-muted-foreground">Memory Usage</div>
          </div>
          <div className="mt-2 flex items-end justify-between">
            <div className="text-2xl font-bold">
              {(currentMetrics.memoryUsage / 1024 / 1024 / 1024).toFixed(2)}GB
            </div>
            <div
              className={cn(
                'text-sm',
                currentMetrics.memoryUsage < averages.memoryUsage
                  ? 'text-green-500'
                  : 'text-destructive'
              )}
            >
              {(
                ((currentMetrics.memoryUsage - averages.memoryUsage) /
                  averages.memoryUsage) *
                100
              ).toFixed(1)}
              %
            </div>
          </div>
          <Progress
            value={(currentMetrics.memoryUsage / (16 * 1024 * 1024 * 1024)) * 100}
            className="mt-2"
          />
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <div className="text-sm text-muted-foreground">CPU Usage</div>
          </div>
          <div className="mt-2 flex items-end justify-between">
            <div className="text-2xl font-bold">{currentMetrics.cpuUsage.toFixed(1)}%</div>
            <div
              className={cn(
                'text-sm',
                currentMetrics.cpuUsage < averages.cpuUsage
                  ? 'text-green-500'
                  : 'text-destructive'
              )}
            >
              {(
                ((currentMetrics.cpuUsage - averages.cpuUsage) / averages.cpuUsage) *
                100
              ).toFixed(1)}
              %
            </div>
          </div>
          <Progress value={currentMetrics.cpuUsage} className="mt-2" />
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
            <div className="text-sm text-muted-foreground">Error Rate</div>
          </div>
          <div className="mt-2 flex items-end justify-between">
            <div className="text-2xl font-bold">
              {currentMetrics.errorRate.toFixed(2)}%
            </div>
            <div
              className={cn(
                'text-sm',
                currentMetrics.errorRate < averages.errorRate
                  ? 'text-green-500'
                  : 'text-destructive'
              )}
            >
              {(
                ((currentMetrics.errorRate - averages.errorRate) / averages.errorRate) *
                100
              ).toFixed(1)}
              %
            </div>
          </div>
          <Progress
            value={(currentMetrics.errorRate / 5) * 100}
            className={cn(
              'mt-2',
              currentMetrics.errorRate > 1 ? 'bg-destructive/20' : undefined
            )}
          />
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Processing Time Chart */}
        <Card className="p-4">
          <h3 className="mb-4 text-sm font-medium">Processing Time Trend</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(tick: number) => new Date(tick).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => `${value.toFixed(2)}ms`}
                  labelFormatter={(label: number) => new Date(label).toLocaleString()}
                />
                <Line
                  type="monotone"
                  dataKey="processingTime"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Resource Usage Chart */}
        <Card className="p-4">
          <h3 className="mb-4 text-sm font-medium">Resource Usage</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(tick: number) => new Date(tick).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip
                  formatter={(value: number, name: string) =>
                    name === 'memoryUsage'
                      ? `${(value / 1024 / 1024 / 1024).toFixed(2)}GB`
                      : `${value.toFixed(1)}%`
                  }
                  labelFormatter={(label: number) => new Date(label).toLocaleString()}
                />
                <Area
                  type="monotone"
                  dataKey="cpuUsage"
                  stackId="1"
                  stroke="hsl(var(--primary))"
                  fill="hsl(var(--primary))"
                  fillOpacity={0.2}
                />
                <Area
                  type="monotone"
                  dataKey="memoryUsage"
                  stackId="2"
                  stroke="hsl(var(--secondary))"
                  fill="hsl(var(--secondary))"
                  fillOpacity={0.2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* API Performance Chart */}
        <Card className="p-4">
          <h3 className="mb-4 text-sm font-medium">API Performance</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(tick: number) => new Date(tick).toLocaleTimeString()}
                />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip
                  formatter={(value: number, name: string) =>
                    name === 'apiLatency'
                      ? `${value.toFixed(2)}ms`
                      : `${value.toFixed(0)} req/s`
                  }
                  labelFormatter={(label: number) => new Date(label).toLocaleString()}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="apiLatency"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="throughput"
                  stroke="hsl(var(--secondary))"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Error Monitoring Chart */}
        <Card className="p-4">
          <h3 className="mb-4 text-sm font-medium">Error Monitoring</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(tick: number) => new Date(tick).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => `${value.toFixed(2)}%`}
                  labelFormatter={(label: number) => new Date(label).toLocaleString()}
                />
                <Area
                  type="monotone"
                  dataKey="errorRate"
                  stroke="hsl(var(--destructive))"
                  fill="hsl(var(--destructive))"
                  fillOpacity={0.2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}

MetricsDashboard.displayName = 'MetricsDashboard'; 