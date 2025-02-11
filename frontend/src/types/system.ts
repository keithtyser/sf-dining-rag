export interface ServiceStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  latency: number;
  uptime: number;
}

export interface RateLimit {
  endpoint: string;
  limit: number;
  remaining: number;
  reset: number;
}

export interface DatabaseConnections {
  active: number;
  idle: number;
  max: number;
}

export interface ErrorRates {
  total: number;
  byType: {
    [key: string]: number;
  };
}

export interface SystemStatus {
  healthy: boolean;
  services: ServiceStatus[];
  rateLimits: RateLimit[];
  databaseConnections: DatabaseConnections;
  errorRates: ErrorRates;
  lastUpdate: number;
} 