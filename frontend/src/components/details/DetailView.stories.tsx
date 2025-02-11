import type { Meta, StoryObj } from '@storybook/react';
import { Provider, createStore } from 'jotai';
import { DetailView } from './DetailView';
import { metricsDataAtom, systemStatusAtom, pipelineStatusAtom, uiStateAtom } from '@/lib/atoms';
import { WebSocketProvider } from '@/providers/WebSocketProvider';

// Create stores with different states
const defaultStore = createStore();
defaultStore.set(metricsDataAtom, Array.from({ length: 24 }, (_, i) => ({
  timestamp: Date.now() - i * 3600000,
  processingTime: Math.random() * 100 + 50,
  memoryUsage: Math.random() * 80 + 20,
  cpuUsage: Math.random() * 60 + 20,
  apiLatency: Math.random() * 200 + 50,
  queueSize: Math.floor(Math.random() * 10),
  errorRate: Math.random() * 0.01,
  throughput: Math.random() * 1000 + 500,
})));

defaultStore.set(systemStatusAtom, {
  healthy: true,
  services: [
    {
      name: 'API Server',
      status: 'operational',
      latency: 120,
      uptime: 99.99,
    },
    {
      name: 'Database',
      status: 'operational',
      latency: 15,
      uptime: 99.95,
    },
    {
      name: 'Vector Store',
      status: 'operational',
      latency: 45,
      uptime: 99.90,
    },
  ],
  rateLimits: [
    {
      endpoint: '/api/embeddings',
      limit: 100,
      remaining: 75,
      resetTime: Date.now() + 3600000,
      used: 25,
    },
  ],
  databaseConnections: {
    active: 5,
    idle: 3,
    max: 20,
    queued: 0,
  },
  errorRates: {
    last1m: 0,
    last5m: 0.02,
    last15m: 0.01,
    last1h: 0.005,
  },
  lastUpdate: Date.now(),
});

defaultStore.set(pipelineStatusAtom, {
  stage: 'loading',
  progress: 45,
});

defaultStore.set(uiStateAtom, {
  sidebarOpen: true,
  theme: 'system',
  debug: false,
});

// Create a store with error states
const errorStore = createStore();
errorStore.set(metricsDataAtom, Array.from({ length: 24 }, (_, i) => ({
  timestamp: Date.now() - i * 3600000,
  processingTime: Math.random() * 200 + 100,
  memoryUsage: Math.random() * 90 + 80,
  cpuUsage: Math.random() * 90 + 80,
  apiLatency: Math.random() * 500 + 200,
  queueSize: Math.floor(Math.random() * 50 + 20),
  errorRate: Math.random() * 0.1 + 0.05,
  throughput: Math.random() * 500 + 100,
})));

errorStore.set(systemStatusAtom, {
  healthy: false,
  services: [
    {
      name: 'API Server',
      status: 'degraded',
      latency: 350,
      uptime: 98.5,
      message: 'High latency detected',
    },
    {
      name: 'Database',
      status: 'operational',
      latency: 25,
      uptime: 99.95,
    },
    {
      name: 'Vector Store',
      status: 'down',
      latency: 0,
      uptime: 95.5,
      message: 'Connection failed',
    },
  ],
  rateLimits: [
    {
      endpoint: '/api/embeddings',
      limit: 100,
      remaining: 0,
      resetTime: Date.now() + 1800000,
      used: 100,
    },
  ],
  databaseConnections: {
    active: 18,
    idle: 0,
    max: 20,
    queued: 5,
  },
  errorRates: {
    last1m: 0.15,
    last5m: 0.08,
    last15m: 0.05,
    last1h: 0.02,
  },
  lastUpdate: Date.now(),
});

errorStore.set(pipelineStatusAtom, {
  stage: 'embedding',
  progress: 67,
  error: 'API rate limit exceeded. Retrying in 30 seconds...',
});

errorStore.set(uiStateAtom, {
  sidebarOpen: true,
  theme: 'system',
  debug: true,
});

const meta = {
  title: 'Details/DetailView',
  component: DetailView,
  parameters: {
    layout: 'padded',
  },
  decorators: [
    (Story) => (
      <Provider store={defaultStore}>
        <WebSocketProvider>
          <Story />
        </WebSocketProvider>
      </Provider>
    ),
  ],
  tags: ['autodocs'],
} satisfies Meta<typeof DetailView>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const WithErrors: Story = {
  decorators: [
    (Story) => (
      <Provider store={errorStore}>
        <WebSocketProvider>
          <Story />
        </WebSocketProvider>
      </Provider>
    ),
  ],
}; 