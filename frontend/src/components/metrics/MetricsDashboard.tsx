"use client";

import React, { useEffect, useState } from 'react';
import { useAtom } from 'jotai';
import { cn } from '@/lib/utils';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Progress } from '../ui/Progress';
import { Badge } from '../ui/Badge';
import { systemStatusAtom, metricsDataAtom } from '@/lib/atoms';
import { SystemStatus } from '@/types/system';
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

interface MetricsDashboardProps {
  className?: string;
  timeRange?: '1h' | '24h' | '7d' | '30d';
}

const defaultSystemStatus: SystemStatus = {
  healthy: true,
  services: [],
  rateLimits: [],
  databaseConnections: {
    active: 0,
    idle: 0,
    max: 0
  },
  errorRates: {
    total: 0,
    byType: {}
  },
  lastUpdate: 0
};

export function MetricsDashboard({ className, timeRange = '1h' }: MetricsDashboardProps) {
  const [systemStatus] = useAtom(systemStatusAtom);
  const [metricsData] = useAtom(metricsDataAtom);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const status = systemStatus || defaultSystemStatus;

  // Calculate current metrics from the latest data point
  const currentMetrics = metricsData[metricsData.length - 1] || {
    timestamp: 0,
    processingTime: 0,
    memoryUsage: 0,
    cpuUsage: 0,
    apiLatency: 0,
    queueSize: 0,
    errorRate: 0,
    throughput: 0,
  };

  // Calculate averages over the time range
  const averages = metricsData.reduce<MetricsData>(
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
    averages[key as keyof MetricsData] /= metricsData.length || 1;
  });

  // Only render time-sensitive content after mounting
  const renderLastUpdated = () => {
    if (!mounted) return null;
    return new Date(status.lastUpdate).toLocaleTimeString();
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* System Health */}
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <Badge 
              variant={status.healthy ? 'success' : 'destructive'}
              className="px-4 py-1"
            >
              {status.healthy ? 'Healthy' : 'Unhealthy'}
            </Badge>
            <span className="text-sm text-muted-foreground">
              Last updated: {renderLastUpdated()}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Services Status */}
      <Card>
        <CardHeader>
          <CardTitle>Services</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {status.services.map((service) => (
              <div key={service.name} className="flex items-center justify-between">
                <span className="font-medium">{service.name}</span>
                <Badge 
                  variant={
                    service.status === 'healthy' ? 'success' : 
                    service.status === 'degraded' ? 'warning' : 
                    'destructive'
                  }
                >
                  {service.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Database Connections */}
      <Card>
        <CardHeader>
          <CardTitle>Database Connections</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Active: {status.databaseConnections.active}</span>
              <span>Idle: {status.databaseConnections.idle}</span>
              <span>Max: {status.databaseConnections.max}</span>
            </div>
            <Progress 
              value={(status.databaseConnections.active / status.databaseConnections.max) * 100} 
              className="h-2"
            />
          </div>
        </CardContent>
      </Card>

      {/* Error Rates */}
      <Card>
        <CardHeader>
          <CardTitle>Error Rates</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Total Errors</span>
              <Badge variant={status.errorRates.total > 0 ? 'destructive' : 'success'}>
                {status.errorRates.total}
              </Badge>
            </div>
            {Object.entries(status.errorRates.byType).map(([type, count]) => (
              <div key={type} className="flex justify-between items-center text-sm">
                <span>{type}</span>
                <span>{count}</span>
              </div>
            ))}
          </div>
        </CardContent>
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
              <LineChart data={metricsData}>
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
              <AreaChart data={metricsData}>
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
              <LineChart data={metricsData}>
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
              <AreaChart data={metricsData}>
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