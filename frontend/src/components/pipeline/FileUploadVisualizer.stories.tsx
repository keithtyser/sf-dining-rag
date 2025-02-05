import type { Meta, StoryObj } from '@storybook/react';
import { FileUploadVisualizer } from './FileUploadVisualizer';

const meta = {
  title: 'Pipeline/FileUploadVisualizer',
  component: FileUploadVisualizer,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof FileUploadVisualizer>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const CustomFileTypes: Story = {
  args: {
    acceptedFileTypes: ['.txt', '.md'],
    maxFileSize: 5 * 1024 * 1024, // 5MB
  },
};

export const WithCallbacks: Story = {
  args: {
    onFileAccepted: async (file: File) => {
      // Simulate file processing
      await new Promise(resolve => setTimeout(resolve, 2000));
      console.log('File processed:', file.name);
    },
    onProcessingComplete: stats => {
      console.log('Processing complete:', stats);
    },
  },
}; 