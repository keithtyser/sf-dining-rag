import type { Meta, StoryObj } from '@storybook/react';
import { ChatContainer } from './ChatContainer';

const meta = {
  title: 'Chat/ChatContainer',
  component: ChatContainer,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof ChatContainer>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleMessages = [
  {
    id: '1',
    role: 'user' as const,
    content: 'What are the most popular dishes at La Piazza?',
    timestamp: Date.now() - 5000,
  },
  {
    id: '2',
    role: 'assistant' as const,
    content: 'Based on the available data, the most popular dishes at La Piazza are:\n\n1. Margherita Pizza - A classic Italian pizza with fresh tomatoes, mozzarella, and basil\n2. Fettuccine Alfredo - Creamy pasta dish with parmesan cheese\n3. Tiramisu - Traditional Italian dessert',
    timestamp: Date.now() - 3000,
  },
  {
    id: '3',
    role: 'user' as const,
    content: 'Can you show me the ingredients for the Margherita Pizza?',
    timestamp: Date.now() - 2000,
  },
  {
    id: '4',
    role: 'assistant' as const,
    content: '```\nMargherita Pizza Ingredients:\n- San Marzano tomatoes\n- Fresh mozzarella cheese\n- Fresh basil leaves\n- Extra virgin olive oil\n- Salt\n- Pizza dough (made daily)\n```',
    timestamp: Date.now() - 1000,
  },
];

export const Default: Story = {
  args: {
    messages: sampleMessages,
    onSendMessage: async (message) => {
      console.log('Sending message:', message);
      await new Promise(resolve => setTimeout(resolve, 1000));
    },
  },
};

export const Empty: Story = {
  args: {
    messages: [],
    onSendMessage: async (message) => {
      console.log('Sending message:', message);
      await new Promise(resolve => setTimeout(resolve, 1000));
    },
  },
};

export const Loading: Story = {
  args: {
    ...Default.args,
    isTyping: true,
  },
};

export const WithError: Story = {
  args: {
    messages: [
      ...sampleMessages,
      {
        id: '5',
        role: 'user' as const,
        content: 'What are the opening hours?',
        timestamp: Date.now(),
        status: 'error' as const,
        error: 'Failed to send message. Please check your connection and try again.',
      },
    ],
    onSendMessage: async () => {
      throw new Error('Network error');
    },
    onRetry: async (messageId) => {
      console.log('Retrying message:', messageId);
      await new Promise(resolve => setTimeout(resolve, 1000));
    },
  },
};

export const LongConversation: Story = {
  args: {
    messages: Array.from({ length: 50 }, (_, i) => ({
      id: `msg-${i}`,
      role: i % 2 === 0 ? ('user' as const) : ('assistant' as const),
      content: `This is message ${i + 1} in a long conversation. ${
        i % 5 === 0 ? '\n\nIt includes some line breaks\nto test the layout.' : ''
      }`,
      timestamp: Date.now() - (50 - i) * 1000,
    })),
    onSendMessage: async (message) => {
      console.log('Sending message:', message);
      await new Promise(resolve => setTimeout(resolve, 1000));
    },
  },
}; 