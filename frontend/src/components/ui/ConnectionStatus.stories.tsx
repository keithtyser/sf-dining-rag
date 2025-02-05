import type { Meta, StoryObj } from '@storybook/react';
import { ConnectionStatus } from './ConnectionStatus';
import { WebSocketProvider } from '@/providers/WebSocketProvider';

const meta = {
  title: 'UI/ConnectionStatus',
  component: ConnectionStatus,
  parameters: {
    layout: 'centered',
  },
  decorators: [
    (Story) => (
      <WebSocketProvider>
        <Story />
      </WebSocketProvider>
    ),
  ],
  tags: ['autodocs'],
} satisfies Meta<typeof ConnectionStatus>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const WithoutReconnect: Story = {
  args: {
    showReconnect: false,
  },
};

export const CustomClassName: Story = {
  args: {
    className: 'bg-muted p-4 rounded-lg',
  },
}; 