import type { Meta, StoryObj } from '@storybook/react';
import { SystemStatus } from './SystemStatus';

const meta = {
  title: 'Metrics/SystemStatus',
  component: SystemStatus,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof SystemStatus>;

export default meta;
type Story = StoryObj<typeof meta>;

const now = Date.now();

const healthyServices = [
  {
    name: 'API',
    status: 'operational' as const,
    latency: 45.2,
    uptime: 99.99,
    lastIncident: now - 15 * 24 * 60 * 60 * 1000, // 15 days ago
  },
  {
    name: 'Database',
    status: 'operational' as const,
    latency: 12.5,
    uptime: 99.999,
    lastIncident: now - 30 * 24 * 60 * 60 * 1000, // 30 days ago
  },
  {
    name: 'Vector Store',
    status: 'operational' as const,
    latency: 25.8,
    uptime: 99.95,
    lastIncident: now - 7 * 24 * 60 * 60 * 1000, // 7 days ago
  },
  {
    name: 'Embedding Service',
    status: 'operational' as const,
    latency: 150.3,
    uptime: 99.9,
    lastIncident: now - 3 * 24 * 60 * 60 * 1000, // 3 days ago
  },
  {
    name: 'Authentication',
    status: 'operational' as const,
    latency: 89.1,
    uptime: 99.999,
    lastIncident: now - 45 * 24 * 60 * 60 * 1000, // 45 days ago
  },
  {
    name: 'WebSocket',
    status: 'operational' as const,
    latency: 15.7,
    uptime: 99.95,
    lastIncident: now - 5 * 24 * 60 * 60 * 1000, // 5 days ago
  },
];

const healthyRateLimits = [
  {
    endpoint: '/api/embeddings',
    limit: 1000,
    remaining: 850,
    resetTime: now + 30 * 60 * 1000, // 30 minutes from now
    used: 150,
  },
  {
    endpoint: '/api/search',
    limit: 5000,
    remaining: 4200,
    resetTime: now + 45 * 60 * 1000, // 45 minutes from now
    used: 800,
  },
  {
    endpoint: '/api/chat',
    limit: 2000,
    remaining: 1500,
    resetTime: now + 15 * 60 * 1000, // 15 minutes from now
    used: 500,
  },
];

const healthyDbConnections = {
  active: 25,
  idle: 5,
  max: 100,
  queued: 0,
};

const healthyErrorRates = {
  last1m: 0.05,
  last5m: 0.08,
  last15m: 0.06,
  last1h: 0.07,
};

export const Default: Story = {
  args: {
    services: healthyServices,
    rateLimits: healthyRateLimits,
    databaseConnections: healthyDbConnections,
    errorRates: healthyErrorRates,
    lastUpdate: now,
  },
};

export const DegradedServices: Story = {
  args: {
    services: [
      {
        ...healthyServices[0],
        status: 'degraded' as const,
        latency: 250.5,
        message: 'High latency detected',
      },
      {
        ...healthyServices[1],
        status: 'operational' as const,
      },
      {
        ...healthyServices[2],
        status: 'degraded' as const,
        latency: 180.2,
        message: 'Increased response time',
      },
      ...healthyServices.slice(3),
    ],
    rateLimits: healthyRateLimits,
    databaseConnections: {
      ...healthyDbConnections,
      active: 75,
      queued: 5,
    },
    errorRates: {
      last1m: 2.5,
      last5m: 1.8,
      last15m: 1.2,
      last1h: 0.9,
    },
    lastUpdate: now,
  },
};

export const SystemDown: Story = {
  args: {
    services: [
      {
        ...healthyServices[0],
        status: 'down' as const,
        message: 'Service unavailable',
      },
      {
        ...healthyServices[1],
        status: 'down' as const,
        message: 'Connection failed',
      },
      ...healthyServices.slice(2).map(service => ({
        ...service,
        status: 'degraded' as const,
        message: 'Limited functionality',
      })),
    ],
    rateLimits: healthyRateLimits.map(limit => ({
      ...limit,
      remaining: Math.floor(limit.remaining * 0.1),
      used: Math.floor(limit.limit * 0.9),
    })),
    databaseConnections: {
      active: 95,
      idle: 0,
      max: 100,
      queued: 25,
    },
    errorRates: {
      last1m: 15.5,
      last5m: 12.8,
      last15m: 8.2,
      last1h: 5.9,
    },
    lastUpdate: now,
  },
};

export const HighLoad: Story = {
  args: {
    services: healthyServices.map(service => ({
      ...service,
      status: 'operational' as const,
      latency: service.latency * 1.5,
    })),
    rateLimits: healthyRateLimits.map(limit => ({
      ...limit,
      remaining: Math.floor(limit.remaining * 0.3),
      used: Math.floor(limit.limit * 0.7),
    })),
    databaseConnections: {
      active: 85,
      idle: 2,
      max: 100,
      queued: 8,
    },
    errorRates: {
      last1m: 0.8,
      last5m: 0.9,
      last15m: 0.7,
      last1h: 0.5,
    },
    lastUpdate: now,
  },
};

export const MaintenanceMode: Story = {
  args: {
    services: healthyServices.map(service => ({
      ...service,
      status: 'degraded' as const,
      message: 'Scheduled maintenance in progress',
    })),
    rateLimits: healthyRateLimits.map(limit => ({
      ...limit,
      remaining: limit.limit,
      used: 0,
    })),
    databaseConnections: {
      active: 5,
      idle: 95,
      max: 100,
      queued: 0,
    },
    errorRates: {
      last1m: 0,
      last5m: 0,
      last15m: 0,
      last1h: 0.2,
    },
    lastUpdate: now,
  },
}; 