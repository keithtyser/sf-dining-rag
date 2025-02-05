import type { Meta, StoryObj } from '@storybook/react';
import { MetricsDashboard } from './MetricsDashboard';

const meta = {
  title: 'Metrics/MetricsDashboard',
  component: MetricsDashboard,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof MetricsDashboard>;

export default meta;
type Story = StoryObj<typeof meta>;

const now = Date.now();
const hour = 60 * 60 * 1000;

// Generate sample data points for the last hour
const generateDataPoints = (count: number, options?: {
  errorSpike?: boolean;
  highLoad?: boolean;
  degradedApi?: boolean;
}) => {
  const points = [];
  for (let i = 0; i < count; i++) {
    const timestamp = now - (count - i) * (hour / count);
    const baseLoad = options?.highLoad ? 0.8 : 0.4;
    const loadVariation = Math.sin((i / count) * Math.PI * 2) * 0.2;
    const point = {
      timestamp,
      processingTime: 100 + Math.random() * 50 + (options?.degradedApi ? 200 : 0),
      memoryUsage: (8 + Math.random() * 2) * 1024 * 1024 * 1024, // 8-10GB
      cpuUsage: (baseLoad + loadVariation) * 100,
      apiLatency: 50 + Math.random() * 20 + (options?.degradedApi ? 150 : 0),
      queueSize: Math.floor(Math.random() * 100),
      errorRate: options?.errorSpike && i > count * 0.7 ? 5 + Math.random() * 3 : 0.5 + Math.random() * 0.5,
      throughput: 100 + Math.sin((i / count) * Math.PI * 2) * 50,
    };
    points.push(point);
  }
  return points;
};

const healthySystem = {
  healthy: true,
  lastUpdate: now,
  services: {
    api: true,
    database: true,
    vectorStore: true,
    embedding: true,
  },
};

const degradedSystem = {
  healthy: false,
  lastUpdate: now,
  message: 'API performance degraded',
  services: {
    api: false,
    database: true,
    vectorStore: true,
    embedding: true,
  },
};

export const Default: Story = {
  args: {
    data: generateDataPoints(60),
    systemStatus: healthySystem,
    timeRange: '1h',
  },
};

export const HighLoad: Story = {
  args: {
    data: generateDataPoints(60, { highLoad: true }),
    systemStatus: {
      ...healthySystem,
      message: 'System under high load',
    },
    timeRange: '1h',
  },
};

export const ErrorSpike: Story = {
  args: {
    data: generateDataPoints(60, { errorSpike: true }),
    systemStatus: {
      healthy: false,
      lastUpdate: now,
      message: 'Elevated error rates detected',
      services: {
        api: true,
        database: true,
        vectorStore: false,
        embedding: true,
      },
    },
    timeRange: '1h',
  },
};

export const DegradedAPI: Story = {
  args: {
    data: generateDataPoints(60, { degradedApi: true }),
    systemStatus: degradedSystem,
    timeRange: '1h',
  },
};

export const Empty: Story = {
  args: {
    data: [],
    systemStatus: healthySystem,
    timeRange: '1h',
  },
}; 