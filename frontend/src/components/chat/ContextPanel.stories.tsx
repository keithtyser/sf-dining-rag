import type { Meta, StoryObj } from '@storybook/react';
import { ContextPanel } from './ContextPanel';

const meta = {
  title: 'Chat/ContextPanel',
  component: ContextPanel,
  parameters: {
    layout: 'padded',
  },
  decorators: [
    (Story) => (
      <div className="h-[600px] max-w-md">
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
} satisfies Meta<typeof ContextPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleChunks = [
  {
    id: 'chunk1',
    text: '# Margherita Pizza\n\nClassic Italian pizza with fresh tomatoes, mozzarella, basil, and extra virgin olive oil. Our signature thin crust is made daily and cooked in a wood-fired oven.',
    tokens: 128,
    metadata: {
      source: 'menu' as const,
      title: 'Margherita Pizza',
      position: 1,
      similarity: 0.92,
    },
  },
  {
    id: 'chunk2',
    text: '# Pasta Carbonara\n\nTraditional Roman pasta dish made with eggs, Pecorino Romano, Parmigiano-Reggiano, guanciale, and black pepper. Served with your choice of spaghetti or rigatoni.',
    tokens: 142,
    metadata: {
      source: 'menu' as const,
      title: 'Pasta Carbonara',
      position: 2,
      similarity: 0.75,
    },
  },
  {
    id: 'chunk3',
    text: 'Pizza Margherita (more commonly known in English as Margherita pizza) is a typical Neapolitan pizza, made with San Marzano tomatoes, mozzarella cheese, fresh basil, salt, and extra-virgin olive oil.',
    tokens: 98,
    metadata: {
      source: 'wikipedia' as const,
      title: 'Pizza Margherita',
      position: 1,
      similarity: 0.88,
      url: 'https://en.wikipedia.org/wiki/Pizza_Margherita',
    },
  },
];

const sampleHistory = [
  {
    query: 'Tell me about Margherita pizza',
    chunks: sampleChunks,
    timestamp: Date.now() - 5000,
  },
  {
    query: 'What pasta dishes do you have?',
    chunks: [sampleChunks[1]],
    timestamp: Date.now() - 60000,
  },
];

export const Default: Story = {
  args: {
    chunks: sampleChunks,
    onChunkClick: (chunk) => {
      console.log('Chunk clicked:', chunk);
    },
    onChunkRemove: (chunkId) => {
      console.log('Remove chunk:', chunkId);
    },
    onClearContext: () => {
      console.log('Clear context');
    },
  },
};

export const Empty: Story = {
  args: {
    chunks: [],
  },
};

export const WithHistory: Story = {
  args: {
    ...Default.args,
    contextHistory: sampleHistory,
    onHistorySelect: (chunks) => {
      console.log('History selected:', chunks);
    },
  },
};

export const HighSimilarityOnly: Story = {
  args: {
    chunks: sampleChunks.filter((chunk) => chunk.metadata.similarity > 0.8),
  },
};

export const MenuItemsOnly: Story = {
  args: {
    chunks: sampleChunks.filter((chunk) => chunk.metadata.source === 'menu'),
  },
};

export const WikipediaOnly: Story = {
  args: {
    chunks: sampleChunks.filter((chunk) => chunk.metadata.source === 'wikipedia'),
  },
}; 