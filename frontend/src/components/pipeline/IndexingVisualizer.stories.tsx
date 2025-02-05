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
    },
    timestamp: Date.now() - 5000,
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
    },
    timestamp: Date.now() - 2000,
  },
  {
    id: 'op3',
    type: 'delete' as const,
    status: 'error' as const,
    vectors: [
      {
        id: 'vec5',
        text: 'Outdated menu item to be removed from the index.',
        dimensions: 1536,
      },
    ],
    error: 'Failed to delete vectors: Connection timeout',
    timestamp: Date.now() - 1000,
  },
  {
    id: 'op4',
    type: 'update' as const,
    status: 'pending' as const,
    vectors: [
      {
        id: 'vec6',
        text: 'Updated description for an existing menu item with new prices and ingredients.',
        dimensions: 1536,
      },
    ],
    timestamp: Date.now(),
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
    indexName: 'restaurant_data',
    dimensions: 384,
  },
};

export const AllComplete: Story = {
  args: {
    operations: sampleOperations.map(op => ({
      ...op,
      status: 'complete',
      metadata: {
        indexSize: 2_500_000 + Math.random() * 500_000,
        totalVectors: 1250 + Math.floor(Math.random() * 10),
        avgIndexTime: 125 + Math.random() * 10,
      },
    })),
  },
};

export const WithErrors: Story = {
  args: {
    operations: sampleOperations.map((op, index) => ({
      ...op,
      status: index % 2 === 0 ? 'error' : 'complete',
      error: index % 2 === 0 ? 'Failed to process vectors: Database connection error' : undefined,
    })),
  },
}; 