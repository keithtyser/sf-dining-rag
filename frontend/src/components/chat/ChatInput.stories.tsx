import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { ChatInput } from './ChatInput';
import { ToastProvider } from '../ui/ToastProvider';

const meta = {
  title: 'Chat/ChatInput',
  component: ChatInput,
  parameters: {
    layout: 'padded',
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
} satisfies Meta<typeof ChatInput>;

export default meta;
type Story = StoryObj<typeof meta>;

const defaultCommands = [
  {
    id: 'help',
    name: '/help',
    description: 'Show available commands',
    execute: () => console.log('Showing help...'),
  },
  {
    id: 'clear',
    name: '/clear',
    description: 'Clear the conversation',
    execute: () => console.log('Clearing conversation...'),
  },
  {
    id: 'search',
    name: '/search',
    description: 'Search in conversation',
    execute: () => console.log('Opening search...'),
  },
  {
    id: 'settings',
    name: '/settings',
    description: 'Open settings',
    execute: () => console.log('Opening settings...'),
  },
];

export const Default: Story = {
  args: {
    onSendMessage: async (message, attachments) => {
      console.log('Sending message:', { message, attachments });
      await new Promise((resolve) => setTimeout(resolve, 1000));
    },
    commands: defaultCommands,
  },
};

export const WithMaxLength: Story = {
  args: {
    ...Default.args,
    maxLength: 100,
  },
};

export const Disabled: Story = {
  args: {
    ...Default.args,
    disabled: true,
  },
};

export const WithTypingIndicator: Story = {
  args: {
    ...Default.args,
    onStartTyping: () => console.log('Started typing...'),
    onStopTyping: () => console.log('Stopped typing...'),
  },
};

export const WithCustomPlaceholder: Story = {
  args: {
    ...Default.args,
    placeholder: 'Ask me anything...',
  },
};

export const Loading: Story = {
  args: {
    ...Default.args,
  },
  render: (args) => {
    const [isLoading, setIsLoading] = React.useState(false);
    
    const handleSend = async (message: string, attachments?: File[]) => {
      setIsLoading(true);
      try {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        console.log('Sent:', { message, attachments });
      } finally {
        setIsLoading(false);
      }
    };

    return (
      <ChatInput
        {...args}
        onSendMessage={handleSend}
        disabled={isLoading}
      />
    );
  },
}; 