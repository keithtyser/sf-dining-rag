import type { Meta, StoryObj } from '@storybook/react';
import { TextChunkVisualizer } from './TextChunkVisualizer';

const meta = {
  title: 'Pipeline/TextChunkVisualizer',
  component: TextChunkVisualizer,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof TextChunkVisualizer>;

export default meta;
type Story = StoryObj<typeof meta>;

const menuChunks = [
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
];

const wikiChunks = [
  {
    id: 'chunk3',
    text: 'Pizza Margherita (more commonly known in English as Margherita pizza) is a typical Neapolitan pizza, made with San Marzano tomatoes, mozzarella cheese, fresh basil, salt, and extra-virgin olive oil.',
    tokens: 98,
    metadata: {
      source: 'wikipedia' as const,
      title: 'Pizza Margherita',
      position: 1,
      similarity: 0.88,
    },
  },
  {
    id: 'chunk4',
    text: 'According to popular tradition, in June 1889, to honor the Queen consort of Italy, Margherita of Savoy, the Neapolitan pizza maker Raffaele Esposito created the "Pizza Margherita", a pizza garnished with tomatoes, mozzarella, and basil, to represent the national colors of Italy as on the Italian flag.',
    tokens: 156,
    metadata: {
      source: 'wikipedia' as const,
      title: 'Pizza Margherita',
      position: 2,
      similarity: 0.62,
    },
  },
];

export const MenuItems: Story = {
  args: {
    chunks: menuChunks,
  },
};

export const WikipediaArticles: Story = {
  args: {
    chunks: wikiChunks,
  },
};

export const Mixed: Story = {
  args: {
    chunks: [...menuChunks, ...wikiChunks],
    highlightedChunkId: 'chunk1',
  },
};

export const WithInteraction: Story = {
  args: {
    chunks: [...menuChunks, ...wikiChunks],
    onChunkClick: chunk => {
      console.log('Chunk clicked:', chunk);
    },
  },
}; 