import type { Meta, StoryObj } from '@storybook/react';
import { Provider, createStore } from 'jotai';
import { MainLayout } from './MainLayout';
import { uiStateAtom } from '@/lib/atoms';
import { WebSocketProvider } from '@/providers/WebSocketProvider';

const defaultStore = createStore();

const debugStore = createStore();
debugStore.set(uiStateAtom, { debug: true, sidebarOpen: true, theme: 'system' });

const closedSidebarStore = createStore();
closedSidebarStore.set(uiStateAtom, { debug: false, sidebarOpen: false, theme: 'system' });

const meta = {
  title: 'Layout/MainLayout',
  component: MainLayout,
  parameters: {
    layout: 'fullscreen',
  },
  decorators: [
    (Story) => (
      <Provider store={defaultStore}>
        <WebSocketProvider>
          <Story />
        </WebSocketProvider>
      </Provider>
    ),
  ],
  tags: ['autodocs'],
} satisfies Meta<typeof MainLayout>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: (
      <div className="p-6">
        <h1 className="mb-4 text-2xl font-bold">Dashboard</h1>
        <p>Main content goes here</p>
      </div>
    ),
  },
};

export const WithDebugPanel: Story = {
  args: {
    children: (
      <div className="p-6">
        <h1 className="mb-4 text-2xl font-bold">Dashboard</h1>
        <p>Main content goes here</p>
      </div>
    ),
  },
  decorators: [
    (Story) => (
      <Provider store={debugStore}>
        <WebSocketProvider>
          <Story />
        </WebSocketProvider>
      </Provider>
    ),
  ],
};

export const SidebarClosed: Story = {
  args: {
    children: (
      <div className="p-6">
        <h1 className="mb-4 text-2xl font-bold">Dashboard</h1>
        <p>Main content goes here</p>
      </div>
    ),
  },
  decorators: [
    (Story) => (
      <Provider store={closedSidebarStore}>
        <WebSocketProvider>
          <Story />
        </WebSocketProvider>
      </Provider>
    ),
  ],
}; 