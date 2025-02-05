import type { Meta, StoryObj } from '@storybook/react';
import { Provider, createStore } from 'jotai';
import { DetailView } from './DetailView';
import { pipelineStatusAtom, systemStatusAtom } from '@/lib/atoms';

const defaultStore = createStore();
defaultStore.set(pipelineStatusAtom, {
  stage: 'loading',
  progress: 45,
});
defaultStore.set(systemStatusAtom, {
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

const errorStore = createStore();
errorStore.set(pipelineStatusAtom, {
  stage: 'embedding',
  progress: 67,
  error: 'API rate limit exceeded. Retrying in 30 seconds...',
});
errorStore.set(systemStatusAtom, {
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

const meta = {
  title: 'Details/DetailView',
  component: DetailView,
  parameters: {
    layout: 'padded',
  },
  decorators: [
    (Story) => (
      <Provider store={defaultStore}>
        <Story />
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
        <Story />
      </Provider>
    ),
  ],
}; 