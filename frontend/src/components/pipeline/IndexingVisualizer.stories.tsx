import type { Meta, StoryObj } from '@storybook/react';
import { IndexingVisualizer } from './IndexingVisualizer';

const meta: Meta<typeof IndexingVisualizer> = {
  title: 'Pipeline/IndexingVisualizer',
  component: IndexingVisualizer,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof IndexingVisualizer>;

const now = Date.now();

const sampleOperations = [
  {
    id: 'op1',
    type: 'upsert' as const,
    status: 'complete' as const,
    vectors: [
      {
        id: 'vec1',
        text: '# Margherita Pizza\n\nClassic Italian pizza with fresh tomatoes, mozzarella, basil, and extra virgin olive oil.',
        dimensions: 1536,
      },
      {
        id: 'vec2',
        text: '# Pasta Carbonara\n\nTraditional Roman pasta dish made with eggs, Pecorino Romano, Parmigiano-Reggiano, and guanciale.',
        dimensions: 1536,
      },
    ],
    metadata: {
      indexSize: 2_500_000, // 2.5MB
      totalVectors: 1250,
      avgIndexTime: 125.5,
      memoryUsage: 512 * 1024 * 1024, // 512MB
      cpuUsage: 45.5,
      diskUsage: 1.5 * 1024 * 1024 * 1024, // 1.5GB
    },
    performance: {
      indexBuildTime: 850.2,
      vectorInsertTime: 425.8,
      optimizationTime: 225.5,
      totalTime: 1501.5,
    },
    networkStats: {
      bytesReceived: 1_250_000,
      bytesSent: 750_000,
      latency: 85.5,
      connectionErrors: 0,
    },
    timestamp: now - 5000,
  },
  {
    id: 'op2',
    type: 'upsert' as const,
    status: 'processing' as const,
    vectors: [
      {
        id: 'vec3',
        text: 'Pizza Margherita is a typical Neapolitan pizza, made with San Marzano tomatoes, mozzarella cheese, fresh basil.',
        dimensions: 1536,
      },
      {
        id: 'vec4',
        text: 'According to popular tradition, in June 1889, to honor the Queen consort of Italy, Margherita of Savoy...',
        dimensions: 1536,
      },
    ],
    metadata: {
      indexSize: 2_800_000, // 2.8MB
      totalVectors: 1252,
      avgIndexTime: 128.2,
      memoryUsage: 524 * 1024 * 1024, // 524MB
      cpuUsage: 65.8,
      diskUsage: 1.6 * 1024 * 1024 * 1024, // 1.6GB
    },
    performance: {
      indexBuildTime: 0,
      vectorInsertTime: 450.2,
      optimizationTime: 0,
      totalTime: 450.2,
    },
    networkStats: {
      bytesReceived: 850_000,
      bytesSent: 450_000,
      latency: 92.5,
      connectionErrors: 0,
    },
    timestamp: now - 2000,
  },
  {
    id: 'op3',
    type: 'update' as const,
    status: 'error' as const,
    vectors: [
      {
        id: 'vec5',
        text: 'Failed vector update operation example.',
        dimensions: 1536,
      },
    ],
    metadata: {
      indexSize: 2_800_000,
      totalVectors: 1252,
      avgIndexTime: 0,
      memoryUsage: 528 * 1024 * 1024,
      cpuUsage: 75.2,
      diskUsage: 1.6 * 1024 * 1024 * 1024,
    },
    performance: {
      indexBuildTime: 0,
      vectorInsertTime: 125.5,
      optimizationTime: 0,
      totalTime: 125.5,
    },
    networkStats: {
      bytesReceived: 150_000,
      bytesSent: 75_000,
      latency: 250.5,
      connectionErrors: 2,
    },
    error: 'Database connection timeout after 5 retries',
    timestamp: now - 1000,
  },
];

export const Default: Story = {
  args: {
    operations: sampleOperations,
  },
};

export const CustomConfiguration: Story = {
  args: {
    operations: sampleOperations,
    databaseName: 'Milvus',
    indexName: 'restaurant_items',
    dimensions: 768,
  },
};

export const AllComplete: Story = {
  args: {
    operations: sampleOperations.map(op => ({
      ...op,
      status: 'complete',
      error: undefined,
      metadata: {
        ...op.metadata,
        avgIndexTime: Math.random() * 50 + 100,
        cpuUsage: Math.random() * 20 + 40,
      },
      performance: {
        indexBuildTime: Math.random() * 200 + 800,
        vectorInsertTime: Math.random() * 200 + 400,
        optimizationTime: Math.random() * 100 + 200,
        totalTime: Math.random() * 500 + 1400,
      },
      networkStats: {
        bytesReceived: Math.random() * 1_000_000 + 500_000,
        bytesSent: Math.random() * 500_000 + 250_000,
        latency: Math.random() * 50 + 50,
        connectionErrors: 0,
      },
    })),
  },
};

export const AllProcessing: Story = {
  args: {
    operations: sampleOperations.map(op => ({
      ...op,
      status: 'processing',
      error: undefined,
      metadata: {
        ...op.metadata,
        cpuUsage: Math.random() * 40 + 60,
      },
      performance: {
        indexBuildTime: 0,
        vectorInsertTime: Math.random() * 200 + 200,
        optimizationTime: 0,
        totalTime: Math.random() * 200 + 200,
      },
      networkStats: {
        bytesReceived: Math.random() * 500_000 + 250_000,
        bytesSent: Math.random() * 250_000 + 125_000,
        latency: Math.random() * 100 + 50,
        connectionErrors: 0,
      },
    })),
  },
};

export const WithErrors: Story = {
  args: {
    operations: sampleOperations.map((op, index) => ({
      ...op,
      status: index % 2 === 0 ? 'error' : 'complete',
      error: index % 2 === 0 ? 'Database connection error: Connection refused' : undefined,
      metadata: {
        ...op.metadata,
        cpuUsage: Math.random() * 20 + 80,
      },
      networkStats: {
        bytesReceived: Math.random() * 200_000 + 100_000,
        bytesSent: Math.random() * 100_000 + 50_000,
        latency: Math.random() * 200 + 100,
        connectionErrors: index % 2 === 0 ? Math.floor(Math.random() * 3) + 1 : 0,
      },
    })),
  },
}; 