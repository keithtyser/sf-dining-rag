import type { Meta, StoryObj } from '@storybook/react';
import { MessageBubble } from './MessageBubble';
import { ToastProvider } from '../ui/ToastProvider';

const meta = {
  title: 'Chat/MessageBubble',
  component: MessageBubble,
  parameters: {
    layout: 'centered',
  },
  decorators: [
    (Story) => (
      <div className="p-4 max-w-2xl w-full">
        <ToastProvider>
          <Story />
        </ToastProvider>
      </div>
    ),
  ],
  tags: ['autodocs'],
} satisfies Meta<typeof MessageBubble>;

export default meta;
type Story = StoryObj<typeof meta>;

const timestamp = Date.now();

export const UserMessage: Story = {
  args: {
    role: 'user',
    content: {
      type: 'text',
      content: 'Hello! Can you help me find a good Italian restaurant?',
    },
    timestamp,
  },
};

export const AssistantMessage: Story = {
  args: {
    role: 'assistant',
    content: {
      type: 'text',
      content: 'I found several highly-rated Italian restaurants in your area. Would you like me to list them with their specialties?',
    },
    timestamp,
    onFeedback: async (isPositive) => {
      console.log('Feedback:', isPositive);
    },
  },
};

export const CodeMessage: Story = {
  args: {
    role: 'assistant',
    content: {
      type: 'code',
      content: `function greet(name) {
  return \`Hello, \${name}!\`;
}`,
      language: 'typescript',
    },
    timestamp,
    onCopy: async (content) => {
      await navigator.clipboard.writeText(content);
    },
  },
};

export const ImageMessage: Story = {
  args: {
    role: 'assistant',
    content: {
      type: 'image',
      content: 'https://via.placeholder.com/400x300',
      altText: 'A sample restaurant image',
    },
    timestamp,
  },
};

export const MultiContentMessage: Story = {
  args: {
    role: 'assistant',
    content: [
      {
        type: 'text',
        content: 'Here is the recipe for Margherita Pizza:',
      },
      {
        type: 'code',
        content: `Ingredients:
- San Marzano tomatoes
- Fresh mozzarella
- Fresh basil
- Extra virgin olive oil
- Salt
- Pizza dough`,
        language: 'plaintext',
      },
      {
        type: 'image',
        content: 'https://via.placeholder.com/400x300',
        altText: 'Margherita Pizza',
      },
    ],
    timestamp,
  },
};

export const SendingMessage: Story = {
  args: {
    role: 'user',
    content: {
      type: 'text',
      content: 'Sending a message...',
    },
    timestamp,
    status: 'sending',
  },
};

export const ErrorMessage: Story = {
  args: {
    role: 'user',
    content: {
      type: 'text',
      content: 'This message failed to send.',
    },
    timestamp,
    status: 'error',
    error: 'Network error occurred',
    onRetry: async () => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      console.log('Retrying message...');
    },
  },
}; 