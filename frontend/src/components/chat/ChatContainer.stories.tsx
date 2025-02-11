import type { Meta, StoryObj } from '@storybook/react';
import { ChatContainer } from './ChatContainer';
import { ToastProvider } from '../ui/ToastProvider';

const meta = {
  title: 'Chat/ChatContainer',
  component: ChatContainer,
  parameters: {
    layout: 'padded',
  },
  decorators: [
    (Story) => (
      <div className="h-[600px]">
        <ToastProvider>
          <Story />
        </ToastProvider>
      </div>
    ),
  ],
  tags: ['autodocs'],
} satisfies Meta<typeof ChatContainer>;

export default meta;
type Story = StoryObj<typeof meta>;

const messages = [
  {
    id: '1',
    role: 'user' as const,
    content: 'Hello! Can you help me find a good Italian restaurant?',
    timestamp: Date.now() - 5000,
  },
  {
    id: '2',
    role: 'assistant' as const,
    content: 'I found several highly-rated Italian restaurants in your area. Would you like me to list them with their specialties?',
    timestamp: Date.now() - 3000,
  },
  {
    id: '3',
    role: 'user' as const,
    content: 'Yes, please! I particularly enjoy authentic pasta dishes.',
    timestamp: Date.now() - 2000,
  },
  {
    id: '4',
    role: 'assistant' as const,
    content: `Here are some top Italian restaurants known for their pasta:

1. La Piazza
   - Signature dish: Handmade Fettuccine Alfredo
   - Known for: Traditional Roman pasta dishes
   - Price range: $$

2. Pasta Perfection
   - Signature dish: Wild Mushroom Ravioli
   - Known for: Fresh, daily-made pasta
   - Price range: $$$

3. Trattoria Bella
   - Signature dish: Seafood Linguine
   - Known for: Coastal Italian cuisine
   - Price range: $$

Would you like more details about any of these restaurants?`,
    timestamp: Date.now() - 1000,
  },
];

export const Default: Story = {
  args: {
    messages,
    onSendMessage: async (message) => {
      console.log('Sending message:', message);
      await new Promise((resolve) => setTimeout(resolve, 1000));
    },
    onRetry: async (messageId) => {
      console.log('Retrying message:', messageId);
      await new Promise((resolve) => setTimeout(resolve, 1000));
    },
    onMessageFeedback: async (messageId, isPositive) => {
      console.log('Message feedback:', { messageId, isPositive });
      await new Promise((resolve) => setTimeout(resolve, 500));
    },
  },
};

export const Empty: Story = {
  args: {
    messages: [],
    onSendMessage: async (message) => {
      console.log('Sending message:', message);
      await new Promise((resolve) => setTimeout(resolve, 1000));
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
      ...messages,
      {
        id: '5',
        role: 'user' as const,
        content: 'This message failed to send',
        timestamp: Date.now(),
        status: 'error' as const,
        error: 'Network error occurred',
      },
    ],
    onSendMessage: async (message) => {
      console.log('Sending message:', message);
      await new Promise((resolve) => setTimeout(resolve, 1000));
    },
    onRetry: async (messageId) => {
      console.log('Retrying message:', messageId);
      await new Promise((resolve) => setTimeout(resolve, 1000));
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