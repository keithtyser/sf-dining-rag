import type { Meta, StoryObj } from '@storybook/react';
import { Provider, createStore } from 'jotai';
import { PipelineView } from './PipelineView';
import { pipelineStatusAtom } from '@/lib/atoms';

const defaultStore = createStore();

const loadingStore = createStore();
loadingStore.set(pipelineStatusAtom, {
  stage: 'loading',
  progress: 45,
});

const scrapingStore = createStore();
scrapingStore.set(pipelineStatusAtom, {
  stage: 'scraping',
  progress: 72,
});

const chunkingStore = createStore();
chunkingStore.set(pipelineStatusAtom, {
  stage: 'chunking',
  progress: 89,
});

const embeddingStore = createStore();
embeddingStore.set(pipelineStatusAtom, {
  stage: 'embedding',
  progress: 34,
});

const errorStore = createStore();
errorStore.set(pipelineStatusAtom, {
  stage: 'embedding',
  progress: 67,
  error: 'API rate limit exceeded. Retrying in 30 seconds...',
});

const meta = {
  title: 'Pipeline/PipelineView',
  component: PipelineView,
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
} satisfies Meta<typeof PipelineView>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Initial: Story = {
  args: {},
};

export const DataLoading: Story = {
  decorators: [
    (Story) => (
      <Provider store={loadingStore}>
        <Story />
      </Provider>
    ),
  ],
};

export const WikiScraping: Story = {
  decorators: [
    (Story) => (
      <Provider store={scrapingStore}>
        <Story />
      </Provider>
    ),
  ],
};

export const TextChunking: Story = {
  decorators: [
    (Story) => (
      <Provider store={chunkingStore}>
        <Story />
      </Provider>
    ),
  ],
};

export const EmbeddingGeneration: Story = {
  decorators: [
    (Story) => (
      <Provider store={embeddingStore}>
        <Story />
      </Provider>
    ),
  ],
};

export const WithError: Story = {
  decorators: [
    (Story) => (
      <Provider store={errorStore}>
        <Story />
      </Provider>
    ),
  ],
}; 