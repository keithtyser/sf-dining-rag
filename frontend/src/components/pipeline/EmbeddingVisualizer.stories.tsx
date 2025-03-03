import type { Meta, StoryObj } from '@storybook/react';
import { EmbeddingVisualizer } from './EmbeddingVisualizer';

const meta = {
  title: 'Pipeline/EmbeddingVisualizer',
  component: EmbeddingVisualizer,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof EmbeddingVisualizer>;

export default meta;
type Story = StoryObj<typeof meta>;

const generateEmbedding = () =>
  Array.from({ length: 1536 }, () => (Math.random() * 2 - 1) * 0.1);

const now = Date.now();

const sampleBatches = [
  {
    id: 'batch1',
    text: '# Margherita Pizza\n\nClassic Italian pizza with fresh tomatoes, mozzarella, basil, and extra virgin olive oil.',
    tokens: 64,
    embedding: generateEmbedding(),
    status: 'complete' as const,
    apiLatency: 245.8,
    processingDetails: {
      tokenization: {
        startTime: now - 1000,
        endTime: now - 800,
        tokenCount: 64,
      },
      embedding: {
        startTime: now - 800,
        endTime: now - 600,
        dimensions: 1536,
      },
    },
    apiCalls: [
      {
        timestamp: now - 800,
        endpoint: 'api/embeddings',
        requestSize: 2048,
        responseSize: 12288,
        duration: 245.8,
        status: 200,
      },
    ],
  },
  {
    id: 'batch2',
    text: 'Pizza Margherita is a typical Neapolitan pizza, made with San Marzano tomatoes, mozzarella cheese, fresh basil, salt, and extra-virgin olive oil.',
    tokens: 72,
    status: 'processing' as const,
    processingDetails: {
      tokenization: {
        startTime: now - 500,
        endTime: now - 400,
        tokenCount: 72,
      },
      embedding: {
        startTime: now - 400,
        endTime: now,
        dimensions: 1536,
      },
    },
    apiCalls: [
      {
        timestamp: now - 400,
        endpoint: 'api/embeddings',
        requestSize: 2304,
        responseSize: 0,
        duration: 400,
        status: 202,
      },
    ],
  },
  {
    id: 'batch3',
    text: 'According to popular tradition, in June 1889, to honor the Queen consort of Italy, Margherita of Savoy, the Neapolitan pizza maker Raffaele Esposito created the "Pizza Margherita".',
    tokens: 89,
    status: 'pending' as const,
  },
  {
    id: 'batch4',
    text: '# Failed Batch\n\nThis batch will simulate an error condition.',
    tokens: 42,
    status: 'error' as const,
    error: 'API rate limit exceeded. Please try again in 60 seconds.',
    apiCalls: [
      {
        timestamp: now - 100,
        endpoint: 'api/embeddings',
        requestSize: 1024,
        responseSize: 512,
        duration: 89.5,
        status: 429,
        error: 'Rate limit exceeded. Please try again in 60 seconds.',
      },
    ],
  },
];

export const Default: Story = {
  args: {
    batches: sampleBatches,
  },
};

export const CustomConfiguration: Story = {
  args: {
    batches: sampleBatches,
    modelName: 'text-embedding-3-large',
    dimensions: 3072,
    batchSize: 16,
    apiEndpoint: 'https://api.example.com/v1/embeddings',
  },
};

export const AllComplete: Story = {
  args: {
    batches: sampleBatches.map(batch => ({
      ...batch,
      status: 'complete',
      embedding: generateEmbedding(),
      apiLatency: Math.random() * 300 + 200,
      processingDetails: {
        tokenization: {
          startTime: now - 1000,
          endTime: now - 800,
          tokenCount: batch.tokens,
        },
        embedding: {
          startTime: now - 800,
          endTime: now - 600,
          dimensions: 1536,
        },
      },
      apiCalls: [
        {
          timestamp: now - 800,
          endpoint: 'api/embeddings',
          requestSize: batch.tokens * 32,
          responseSize: 1536 * 4,
          duration: Math.random() * 300 + 200,
          status: 200,
        },
      ],
    })),
  },
};

export const AllProcessing: Story = {
  args: {
    batches: sampleBatches.map(batch => ({
      ...batch,
      status: 'processing',
      processingDetails: {
        tokenization: {
          startTime: now - 500,
          endTime: now - 400,
          tokenCount: batch.tokens,
        },
        embedding: {
          startTime: now - 400,
          endTime: now,
          dimensions: 1536,
        },
      },
      apiCalls: [
        {
          timestamp: now - 400,
          endpoint: 'api/embeddings',
          requestSize: batch.tokens * 32,
          responseSize: 0,
          duration: 400,
          status: 202,
        },
      ],
    })),
  },
};

export const WithErrors: Story = {
  args: {
    batches: sampleBatches.map((batch, index) => ({
      ...batch,
      status: index % 2 === 0 ? 'error' : 'complete',
      error: index % 2 === 0 ? 'Failed to generate embedding: Network error' : undefined,
      embedding: index % 2 === 0 ? undefined : generateEmbedding(),
      apiCalls: [
        {
          timestamp: now - 100,
          endpoint: 'api/embeddings',
          requestSize: batch.tokens * 32,
          responseSize: index % 2 === 0 ? 512 : 1536 * 4,
          duration: Math.random() * 300 + 200,
          status: index % 2 === 0 ? 500 : 200,
          error: index % 2 === 0 ? 'Internal Server Error' : undefined,
        },
      ],
    })),
  },
}; 