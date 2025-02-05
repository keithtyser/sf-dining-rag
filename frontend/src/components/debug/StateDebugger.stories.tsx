import type { Meta, StoryObj } from '@storybook/react';
import { Provider, createStore } from 'jotai';
import { StateDebugger } from './StateDebugger';
import { debugStateAtom, uiStateAtom } from '@/lib/atoms';

const defaultStore = createStore();
defaultStore.set(uiStateAtom, { debug: true, sidebarOpen: true, theme: 'system' });

const errorStore = createStore();
errorStore.set(uiStateAtom, { debug: true, sidebarOpen: true, theme: 'system' });
errorStore.set(debugStateAtom, {
  wsConnections: 1,
  wsMessages: 42,
  apiCalls: 15,
  debug: true,
  errors: [
    {
      timestamp: Date.now() - 5000,
      message: 'Failed to connect to WebSocket',
      stack: 'Error: Failed to connect to WebSocket\n    at WebSocket.onerror (websocket.ts:42)',
    },
    {
      timestamp: Date.now() - 60000,
      message: 'API rate limit exceeded',
      stack: 'Error: Rate limit exceeded\n    at handleResponse (api.ts:123)',
    },
  ],
});

const statsStore = createStore();
statsStore.set(uiStateAtom, { debug: true, sidebarOpen: true, theme: 'system' });
statsStore.set(debugStateAtom, {
  wsConnections: 3,
  wsMessages: 156,
  apiCalls: 42,
  debug: true,
  errors: [],
});

const meta = {
  title: 'Debug/StateDebugger',
  component: StateDebugger,
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
} satisfies Meta<typeof StateDebugger>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const WithErrors: Story = {
  decorators: [
    (Story) => (
      <Provider store={errorStore}>
        <Story />
      </Provider>
    ),
  ],
};

export const WithStats: Story = {
  decorators: [
    (Story) => (
      <Provider store={statsStore}>
        <Story />
      </Provider>
    ),
  ],
}; 