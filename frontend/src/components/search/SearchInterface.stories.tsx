import type { Meta, StoryObj } from '@storybook/react';
import { SearchInterface } from './SearchInterface';

const meta = {
  title: 'Search/SearchInterface',
  component: SearchInterface,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof SearchInterface>;

export default meta;
type Story = StoryObj<typeof meta>;

const mockResults = [
  {
    id: '1',
    text: '# Margherita Pizza\n\nClassic Italian pizza with fresh tomatoes, mozzarella, basil, and extra virgin olive oil. Our signature thin crust is made daily and cooked in a wood-fired oven.',
    score: 0.92,
    source: 'menu' as const,
    metadata: {
      title: 'Margherita Pizza',
      category: 'Pizza',
      restaurant: 'La Piazza',
      timestamp: Date.now(),
    },
  },
  {
    id: '2',
    text: 'Pizza Margherita is a typical Neapolitan pizza, made with San Marzano tomatoes, mozzarella cheese, fresh basil, salt, and extra-virgin olive oil. The pizza was created in 1889 by Raffaele Esposito in honor of Queen Margherita of Italy.',
    score: 0.87,
    source: 'wikipedia' as const,
    metadata: {
      title: 'Pizza Margherita History',
      timestamp: Date.now(),
    },
  },
  {
    id: '3',
    text: '# Pasta Carbonara\n\nTraditional Roman pasta dish made with eggs, Pecorino Romano, Parmigiano-Reggiano, guanciale, and black pepper. Served with your choice of spaghetti or rigatoni.',
    score: 0.75,
    source: 'menu' as const,
    metadata: {
      title: 'Pasta Carbonara',
      category: 'Pasta',
      restaurant: 'La Piazza',
      timestamp: Date.now(),
    },
  },
];

export const Default: Story = {
  args: {
    onSearch: async (query) => {
      console.log('Searching for:', query);
      await new Promise(resolve => setTimeout(resolve, 1000));
    },
    onFeedback: async (resultId, isRelevant) => {
      console.log('Feedback:', { resultId, isRelevant });
      await new Promise(resolve => setTimeout(resolve, 500));
    },
  },
};

export const WithResults: Story = {
  args: {
    ...Default.args,
  },
  render: (args) => {
    return (
      <SearchInterface
        {...args}
        onSearch={async (query) => {
          console.log('Searching for:', query);
          await new Promise(resolve => setTimeout(resolve, 1000));
          // @ts-ignore - we're mocking the results here
          args.results = mockResults;
        }}
      />
    );
  },
};

export const Loading: Story = {
  args: {
    ...Default.args,
  },
  render: (args) => {
    return (
      <SearchInterface
        {...args}
        onSearch={async () => {
          await new Promise(resolve => setTimeout(resolve, 10000));
        }}
      />
    );
  },
};

export const WithFeedback: Story = {
  args: {
    ...Default.args,
  },
  render: (args) => {
    return (
      <SearchInterface
        {...args}
        // @ts-ignore - we're mocking the results here
        results={mockResults.map(result => ({
          ...result,
          feedbackState: result.id === '1' ? true : result.id === '2' ? false : undefined,
        }))}
      />
    );
  },
}; 