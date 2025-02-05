import type { Meta, StoryObj } from '@storybook/react';
import { DataSourceVisualizer } from './DataSourceVisualizer';

const meta = {
  title: 'Pipeline/DataSourceVisualizer',
  component: DataSourceVisualizer,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof DataSourceVisualizer>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleStats = {
  menuItems: 1250,
  wikiArticles: 45,
  totalChunks: 875,
  averageChunkSize: 512,
  embeddingDimensions: 1536,
};

export const AllStagesPending: Story = {
  args: {
    stages: [
      { stage: 'loading', progress: 0, status: 'pending' },
      { stage: 'scraping', progress: 0, status: 'pending' },
      { stage: 'preprocessing', progress: 0, status: 'pending' },
      { stage: 'chunking', progress: 0, status: 'pending' },
      { stage: 'embedding', progress: 0, status: 'pending' },
    ],
  },
};

export const InProgress: Story = {
  args: {
    stats: sampleStats,
    stages: [
      { stage: 'loading', progress: 100, status: 'complete' },
      { 
        stage: 'scraping', 
        progress: 65, 
        status: 'processing',
        details: 'Scraping article 29 of 45: "Italian Cuisine History"'
      },
      { stage: 'preprocessing', progress: 0, status: 'pending' },
      { stage: 'chunking', progress: 0, status: 'pending' },
      { stage: 'embedding', progress: 0, status: 'pending' },
    ],
  },
};

export const WithError: Story = {
  args: {
    stats: {
      ...sampleStats,
      wikiArticles: 28,
    },
    stages: [
      { stage: 'loading', progress: 100, status: 'complete' },
      { 
        stage: 'scraping', 
        progress: 65, 
        status: 'error',
        details: 'Failed to scrape article: Rate limit exceeded'
      },
      { stage: 'preprocessing', progress: 0, status: 'pending' },
      { stage: 'chunking', progress: 0, status: 'pending' },
      { stage: 'embedding', progress: 0, status: 'pending' },
    ],
  },
};

export const Complete: Story = {
  args: {
    stats: sampleStats,
    stages: [
      { stage: 'loading', progress: 100, status: 'complete' },
      { stage: 'scraping', progress: 100, status: 'complete' },
      { stage: 'preprocessing', progress: 100, status: 'complete' },
      { stage: 'chunking', progress: 100, status: 'complete' },
      { stage: 'embedding', progress: 100, status: 'complete' },
    ],
  },
}; 