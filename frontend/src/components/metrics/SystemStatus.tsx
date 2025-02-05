import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '../ui/Card';
import { Progress } from '../ui/Progress';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Database,
  Globe,
  HardDrive,
  Network,
  Server,
  Shield,
  Zap,
} from 'lucide-react';
import { useWebSocketMulti } from '@/hooks/useWebSocket';
import { WebSocketEvent } from '@/lib/websocket/WebSocketManager';

interface ServiceStatus {
  name: string;
  status: 'operational' | 'degraded' | 'down';
  latency?: number;
  uptime?: number;
  lastIncident?: number;
  message?: string;
}

interface RateLimit {
  endpoint: string;
  limit: number;
  remaining: number;
  resetTime: number;
  used: number;
}

interface DatabaseConnections {
  active: number;
  idle: number;
  max: number;
  queued: number;
}

interface ErrorRates {
  last1m: number;
  last5m: number;
  last15m: number;
  last1h: number;
}

type SystemStatusData = {
  'system:status': ServiceStatus[];
  'error:rate': ErrorRates;
  'db:connections': DatabaseConnections;
  'rate:limits': RateLimit[];
  'pipeline:status': never;
  'metrics:update': never;
};

interface SystemStatusProps {
  className?: string;
  services: ServiceStatus[];
  rateLimits: RateLimit[];
  databaseConnections: {
    active: number;
    idle: number;
    max: number;
    queued: number;
  };
  errorRates: {
    last1m: number;
    last5m: number;
    last15m: number;
    last1h: number;
  };
  lastUpdate: number;
}

const getStatusColor = (status: ServiceStatus['status']) => {
  switch (status) {
    case 'operational':
      return 'text-green-500';
    case 'degraded':
      return 'text-yellow-500';
    case 'down':
      return 'text-destructive';
  }
};

const getStatusBg = (status: ServiceStatus['status']) => {
  switch (status) {
    case 'operational':
      return 'bg-green-500/10';
    case 'degraded':
      return 'bg-yellow-500/10';
    case 'down':
      return 'bg-destructive/10';
  }
};

const getServiceIcon = (name: string) => {
  switch (name.toLowerCase()) {
    case 'api':
      return Globe;
    case 'database':
      return Database;
    case 'vector store':
      return HardDrive;
    case 'embedding service':
      return Server;
    case 'authentication':
      return Shield;
    case 'websocket':
      return Zap;
    default:
      return Server;
  }
};

export function SystemStatus({ className }: { className?: string }) {
  const events: WebSocketEvent[] = ['system:status', 'error:rate', 'db:connections', 'rate:limits'];
  const { data, connectionState } = useWebSocketMulti<SystemStatusData>(events);

  // Use real-time data or fallback to initial states
  const services = data['system:status'] || [];
  const errorRates = data['error:rate'] || {
    last1m: 0,
    last5m: 0,
    last15m: 0,
    last1h: 0,
  };
  const databaseConnections = data['db:connections'] || {
    active: 0,
    idle: 0,
    max: 100,
    queued: 0,
  };
  const rateLimits = data['rate:limits'] || [];

  // Calculate overall system status
  const overallStatus = services.every(s => s.status === 'operational')
    ? 'operational'
    : services.some(s => s.status === 'down')
    ? 'down'
    : 'degraded';

  // Calculate error rate trend
  const errorTrend =
    errorRates.last1m > errorRates.last5m
      ? 'increasing'
      : errorRates.last1m < errorRates.last5m
      ? 'decreasing'
      : 'stable';

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overall Status */}
      <Card className="p-4">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-muted-foreground" />
            <h3 className="text-lg font-medium">System Status</h3>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-muted-foreground">
              Connection: {connectionState}
            </div>
            <div
              className={cn(
                'flex items-center gap-2 rounded-full px-3 py-1 text-sm',
                getStatusBg(overallStatus),
                getStatusColor(overallStatus)
              )}
            >
              {overallStatus === 'operational' ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : overallStatus === 'degraded' ? (
                <AlertTriangle className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <span className="capitalize">{overallStatus}</span>
            </div>
          </div>
        </div>

        {/* Service Grid */}
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {services.map(service => (
            <div
              key={service.name}
              className={cn(
                'flex items-start gap-3 rounded-lg border p-4',
                getStatusBg(service.status)
              )}
            >
              {React.createElement(getServiceIcon(service.name), {
                className: cn('h-5 w-5', getStatusColor(service.status)),
              })}
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <div className="font-medium">{service.name}</div>
                  <div className={cn('text-sm', getStatusColor(service.status))}>
                    {service.status === 'operational' ? (
                      'Healthy'
                    ) : service.status === 'degraded' ? (
                      'Degraded'
                    ) : (
                      'Down'
                    )}
                  </div>
                </div>
                {service.latency && (
                  <div className="mt-1 text-sm text-muted-foreground">
                    Latency: {service.latency.toFixed(2)}ms
                  </div>
                )}
                {service.message && (
                  <div className="mt-1 text-sm text-muted-foreground">
                    {service.message}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Database Connections */}
        <div className="mb-6">
          <h4 className="mb-3 text-sm font-medium">Database Connections</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <div className="text-muted-foreground">Active Connections</div>
              <div className="font-medium">
                {databaseConnections.active} / {databaseConnections.max}
              </div>
            </div>
            <Progress
              value={(databaseConnections.active / databaseConnections.max) * 100}
              className={cn(
                databaseConnections.active / databaseConnections.max > 0.8
                  ? 'bg-destructive/20'
                  : databaseConnections.active / databaseConnections.max > 0.6
                  ? 'bg-yellow-500/20'
                  : undefined
              )}
            />
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <div className="text-sm text-muted-foreground">Idle</div>
                <div className="font-medium">{databaseConnections.idle}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Queued</div>
                <div className="font-medium">{databaseConnections.queued}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Available</div>
                <div className="font-medium">
                  {databaseConnections.max - databaseConnections.active}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Rate Limits */}
        <div className="mb-6">
          <h4 className="mb-3 text-sm font-medium">API Rate Limits</h4>
          <div className="space-y-4">
            {rateLimits.map(limit => (
              <div key={limit.endpoint}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <div className="text-muted-foreground">{limit.endpoint}</div>
                  <div className="font-medium">
                    {limit.remaining} / {limit.limit} remaining
                  </div>
                </div>
                <Progress
                  value={(limit.used / limit.limit) * 100}
                  className={cn(
                    limit.remaining / limit.limit < 0.2
                      ? 'bg-destructive/20'
                      : limit.remaining / limit.limit < 0.4
                      ? 'bg-yellow-500/20'
                      : undefined
                  )}
                />
                <div className="mt-1 text-xs text-muted-foreground">
                  Resets in{' '}
                  {Math.ceil((limit.resetTime - Date.now()) / 1000 / 60)} minutes
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Error Rates */}
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h4 className="text-sm font-medium">Error Rates</h4>
            <div
              className={cn(
                'flex items-center gap-1 rounded-full px-2 py-1 text-xs',
                errorTrend === 'increasing'
                  ? 'bg-destructive/10 text-destructive'
                  : errorTrend === 'decreasing'
                  ? 'bg-green-500/10 text-green-500'
                  : 'bg-yellow-500/10 text-yellow-500'
              )}
            >
              {errorTrend === 'increasing' ? (
                <>
                  <AlertTriangle className="h-3 w-3" />
                  <span>Increasing</span>
                </>
              ) : errorTrend === 'decreasing' ? (
                <>
                  <CheckCircle2 className="h-3 w-3" />
                  <span>Improving</span>
                </>
              ) : (
                <>
                  <Clock className="h-3 w-3" />
                  <span>Stable</span>
                </>
              )}
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-4">
            <div>
              <div className="text-sm text-muted-foreground">Last 1m</div>
              <div className="font-medium">{errorRates.last1m.toFixed(2)}%</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Last 5m</div>
              <div className="font-medium">{errorRates.last5m.toFixed(2)}%</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Last 15m</div>
              <div className="font-medium">{errorRates.last15m.toFixed(2)}%</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Last 1h</div>
              <div className="font-medium">{errorRates.last1h.toFixed(2)}%</div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

SystemStatus.displayName = 'SystemStatus'; 