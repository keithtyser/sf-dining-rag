import type { Meta, StoryObj } from '@storybook/react';
import { SettingsPanel } from './SettingsPanel';

const meta = {
  title: 'Settings/SettingsPanel',
  component: SettingsPanel,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof SettingsPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    onSave: async (settings) => {
      console.log('Saving settings:', settings);
      await new Promise(resolve => setTimeout(resolve, 1000));
    },
    onReset: async () => {
      console.log('Resetting settings');
      await new Promise(resolve => setTimeout(resolve, 500));
    },
  },
};

export const WithCustomValues: Story = {
  args: {
    ...Default.args,
    initialValues: {
      pipeline: {
        batchSize: 64,
        maxTokens: 1000,
        chunkOverlap: 100,
        similarityThreshold: 0.8,
        maxResults: 20,
      },
      model: {
        model: 'gpt-4',
        temperature: 0.9,
        topP: 0.95,
        frequencyPenalty: 0.5,
        presencePenalty: 0.5,
        maxTokens: 2000,
      },
      system: {
        theme: 'dark',
        debug: true,
        autoSave: false,
        notifications: true,
      },
    },
  },
};

export const Saving: Story = {
  args: {
    ...Default.args,
    onSave: async () => {
      await new Promise(resolve => setTimeout(resolve, 10000));
    },
  },
};

export const WithError: Story = {
  args: {
    ...Default.args,
    onSave: async () => {
      await new Promise((_, reject) => setTimeout(() => reject(new Error('Failed to save settings')), 1000));
    },
  },
}; 